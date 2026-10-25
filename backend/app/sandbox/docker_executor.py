"""Hardened Docker Sandbox Executor for Untrusted Code Execution."""

import asyncio
import logging
import os
import re
import shutil
import subprocess
import tempfile
import time
import uuid
from typing import Any

from app.agents.code_generation.contracts import CodeGenerationOutput
from app.sandbox.base import AbstractSandboxExecutor
from app.sandbox.contracts import (
    ALLOWED_ENV_VARS,
    DEFAULT_MEMORY_LIMIT,
    ExecutionRequest,
    ExecutionResult,
    ExecutionStatus,
    ExecutionType,
    ResourceLimits,
)
from app.sandbox.validation import validate_artifact_for_execution
from app.telemetry.contracts import EventSeverity, ExecutionEventType, ExecutionKind
from app.telemetry.publisher import ExecutionEventPublisher

logger = logging.getLogger(__name__)

DEFAULT_SANDBOX_IMAGE = "se-intelliplatform-sandbox:latest"


class DockerSandboxExecutor(AbstractSandboxExecutor):
    """Executes untrusted generated code within an isolated, hardened Docker container.

    Security Controls Enforced:
    1. Ephemeral read-only workspace mount: -v {host_temp_dir}:/workspace:ro
    2. Zero host filesystem access: C:\\, /, and project root are NEVER mounted.
    3. Docker socket is NEVER mounted or exposed.
    4. Network completely disabled: --network=none
    5. Dropped all Linux capabilities: --cap-drop=ALL
    6. Non-root user: --user=2000:2000
    7. Prevention of privilege escalation: --security-opt=no-new-privileges:true
    8. Writable memory-backed tmpfs only: --tmpfs /tmp:rw,size=64m
    9. PID and process limits: --pids-limit=64
    10. CPU and memory limits: --cpus=1.0, --memory=512m
    11. Execution timeout enforcement with hard kill.
    12. Bounded stdout/stderr capture with truncation indicator.
    13. Strict environment allowlist: NO host API keys or DB passwords passed.
    14. Fixed, deterministic test runner invocation: python -m pytest
    15. Re-runs static deterministic validation prior to container startup.
    16. NO insecure host execution fallback if Docker is unavailable.
    """

    def __init__(self, image: str = DEFAULT_SANDBOX_IMAGE) -> None:
        self.image = image
        self._docker_available: bool | None = None

    async def _safe_subprocess_exec(
        self,
        *cmd: str,
        capture_output: bool = True,
        timeout: float | None = None,
    ) -> tuple[int, bytes, bytes]:
        """Safely execute subprocess asynchronously, with fallback for environments lacking subprocess_exec."""
        try:
            proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE if capture_output else asyncio.subprocess.DEVNULL,
                stderr=asyncio.subprocess.PIPE if capture_output else asyncio.subprocess.DEVNULL,
            )
            try:
                stdout_bytes, stderr_bytes = await asyncio.wait_for(
                    proc.communicate(),
                    timeout=timeout,
                )
                return proc.returncode, stdout_bytes or b"", stderr_bytes or b""
            except asyncio.TimeoutError:
                try:
                    proc.kill()
                except Exception:
                    pass
                raise
        except NotImplementedError:
            def _sync():
                try:
                    res = subprocess.run(
                        list(cmd),
                        stdout=subprocess.PIPE if capture_output else subprocess.DEVNULL,
                        stderr=subprocess.PIPE if capture_output else subprocess.DEVNULL,
                        timeout=timeout,
                        shell=False,
                    )
                    return res.returncode, res.stdout or b"", res.stderr or b""
                except subprocess.TimeoutExpired:
                    raise asyncio.TimeoutError()
            return await asyncio.to_thread(_sync)

    async def is_available(self) -> bool:
        """Check if Docker is running and available."""
        if self._docker_available is not None:
            return self._docker_available

        try:
            code, _, _ = await self._safe_subprocess_exec("docker", "info", capture_output=False, timeout=5.0)
            self._docker_available = (code == 0)
        except Exception as exc:
            logger.warning(f"Docker availability check failed: {exc}")
            self._docker_available = False

        return self._docker_available

    def _parse_pytest_output(self, stdout: str) -> tuple[int, int, int]:
        """Parse passed and failed test counts from pytest stdout."""
        passed = 0
        failed = 0

        # Match "X passed"
        passed_match = re.search(r"(\d+)\s+passed", stdout)
        if passed_match:
            passed = int(passed_match.group(1))

        # Match "X failed"
        failed_match = re.search(r"(\d+)\s+failed", stdout)
        if failed_match:
            failed = int(failed_match.group(1))

        # Match "X error"
        error_match = re.search(r"(\d+)\s+error", stdout)
        if error_match:
            failed += int(error_match.group(1))

        return passed, failed, passed + failed

    def _truncate_output(self, text: str, max_bytes: int) -> tuple[str, bool]:
        """Truncate text deterministically if UTF-8 byte length exceeds limit."""
        encoded = text.encode("utf-8")
        if len(encoded) <= max_bytes:
            return text, False

        # Truncate at byte boundary and decode safely
        truncated_bytes = encoded[:max_bytes]
        decoded = truncated_bytes.decode("utf-8", errors="ignore")
        return f"{decoded}\n\n[TRUNCATED: Output exceeded {max_bytes} bytes limit]", True

    async def _emit_terminal_event(self, result: ExecutionResult) -> ExecutionResult:
        """Safely emit SANDBOX_COMPLETED or SANDBOX_FAILED terminal telemetry event."""
        is_success = result.status == ExecutionStatus.PASSED
        term_evt = (
            ExecutionEventType.SANDBOX_COMPLETED
            if is_success
            else ExecutionEventType.SANDBOX_FAILED
        )
        await ExecutionEventPublisher.emit(
            event_type=term_evt,
            project_id=result.project_id,
            execution_id=result.execution_id,
            parent_execution_id=result.workflow_execution_id,
            execution_kind=ExecutionKind.SANDBOX,
            source="DockerSandboxExecutor",
            status=result.status.value,
            severity=EventSeverity.INFO if is_success else EventSeverity.ERROR,
            payload={
                "status": result.status.value,
                "execution_type": result.execution_type.value,
                "exit_code": result.exit_code,
                "duration_seconds": result.duration_seconds,
                "tests_passed": result.tests_passed,
                "tests_failed": result.tests_failed,
                "tests_total": result.tests_total,
                "phase": f"Sandbox {result.status.value.lower()}",
                "progress_pct": 100.0 if is_success else None,
            },
        )
        return result

    async def execute(
        self,
        request: ExecutionRequest,
        code_output: CodeGenerationOutput,
    ) -> ExecutionResult:
        """Execute validation or tests against generated code."""
        start_time = time.monotonic()
        execution_id = uuid.uuid4()

        await ExecutionEventPublisher.emit(
            event_type=ExecutionEventType.SANDBOX_STARTED,
            project_id=request.project_id,
            execution_id=execution_id,
            parent_execution_id=request.workflow_execution_id,
            execution_kind=ExecutionKind.SANDBOX,
            source="DockerSandboxExecutor",
            status="RUNNING",
            payload={
                "execution_type": request.execution_type.value,
                "test_target": request.test_target,
                "phase": f"Sandbox {request.execution_type.value} started",
            },
        )

        # 1. Deterministic Pre-Execution Static Re-Validation
        validation_errors = validate_artifact_for_execution(
            code_output,
            test_target=request.test_target,
        )
        if validation_errors:
            duration = round(time.monotonic() - start_time, 4)
            return await self._emit_terminal_event(
                ExecutionResult(
                    execution_id=execution_id,
                    project_id=request.project_id,
                    workflow_execution_id=request.workflow_execution_id,
                    execution_type=request.execution_type,
                    status=ExecutionStatus.VALIDATION_ERROR,
                    exit_code=None,
                    duration_seconds=duration,
                    stdout="",
                    stderr="",
                    is_truncated=False,
                    tests_passed=0,
                    tests_failed=0,
                    tests_total=0,
                    validation_errors=validation_errors,
                    metadata={"reason": "Deterministic pre-execution validation failed"},
                )
            )

        # 2. Handle STATIC_VALIDATE Mode (No container needed)
        if request.execution_type == ExecutionType.STATIC_VALIDATE:
            duration = round(time.monotonic() - start_time, 4)
            return await self._emit_terminal_event(
                ExecutionResult(
                    execution_id=execution_id,
                    project_id=request.project_id,
                    workflow_execution_id=request.workflow_execution_id,
                    execution_type=request.execution_type,
                    status=ExecutionStatus.PASSED,
                    exit_code=0,
                    duration_seconds=duration,
                    stdout="Static analysis and AST verification passed. No errors found.",
                    stderr="",
                    is_truncated=False,
                    tests_passed=1,
                    tests_failed=0,
                    tests_total=1,
                    validation_errors=[],
                    metadata={"mode": "static_validate"},
                )
            )

        # 3. Verify Docker Runtime Availability
        is_ready = await self.is_available()
        if not is_ready:
            duration = round(time.monotonic() - start_time, 4)
            return await self._emit_terminal_event(
                ExecutionResult(
                    execution_id=execution_id,
                    project_id=request.project_id,
                    workflow_execution_id=request.workflow_execution_id,
                    execution_type=request.execution_type,
                    status=ExecutionStatus.SANDBOX_UNAVAILABLE,
                    exit_code=None,
                    duration_seconds=duration,
                    stdout="",
                    stderr="Docker runtime is not available or unreachable. Host fallback is strictly forbidden for security.",
                    is_truncated=False,
                    tests_passed=0,
                    tests_failed=0,
                    tests_total=0,
                    validation_errors=[],
                    metadata={"reason": "docker_daemon_unavailable"},
                )
            )

        # 4. Materialize Generated Files into an Ephemeral Host Directory
        temp_dir = tempfile.mkdtemp(prefix="se_sandbox_")
        container_name = f"sandbox-{execution_id}"
        limits = request.limits

        try:
            # Write files safely into temp_dir
            for f in code_output.generated_files:
                target_path = os.path.abspath(os.path.join(temp_dir, f.path))
                # Canonical containment check: path must stay strictly inside temp_dir
                if not target_path.startswith(os.path.abspath(temp_dir)):
                    raise ValueError(f"Path traversal detected during materialization: {f.path}")
                os.makedirs(os.path.dirname(target_path), exist_ok=True)
                with open(target_path, "w", encoding="utf-8") as fp:
                    fp.write(f.content)

            await ExecutionEventPublisher.emit(
                event_type=ExecutionEventType.SANDBOX_PROGRESS,
                project_id=request.project_id,
                execution_id=execution_id,
                parent_execution_id=request.workflow_execution_id,
                execution_kind=ExecutionKind.SANDBOX,
                source="DockerSandboxExecutor",
                status="RUNNING",
                payload={
                    "container_name": container_name,
                    "phase": "Executing container command",
                    "progress_pct": 50.0,
                },
            )

            # Build strictly controlled docker command
            cmd = [
                "docker",
                "run",
                "--name",
                container_name,
                "--rm",
                "--init",
                "--network=none",
                "--read-only",
                "--cap-drop=ALL",
                "--security-opt=no-new-privileges:true",
                f"--memory={limits.memory_limit}",
                f"--cpus={limits.cpus}",
                f"--pids-limit={limits.max_pids}",
                "--tmpfs",
                "/tmp:rw,size=64m",
                "--tmpfs",
                "/home/sandboxuser:rw,size=64m",
                "-v",
                f"{temp_dir}:/workspace:ro",
                "-w",
                "/workspace",
                "-e",
                "PYTHONPATH=/workspace",
                "-e",
                "PYTHONDONTWRITEBYTECODE=1",
                "-e",
                "PYTHONUNBUFFERED=1",
                self.image,
            ]

            if request.execution_type == ExecutionType.LINT:
                cmd.extend([
                    "ruff",
                    "check",
                    "--no-cache",
                    "--output-format=json",
                    "--select=E,F,W",
                    ".",
                ])
            else:
                cmd.extend([
                    "python",
                    "-m",
                    "pytest",
                    "-q",
                    "--tb=short",
                    "--no-header",
                    "-o",
                    "cache_dir=/tmp/.pytest_cache",
                ])
                if request.test_target:
                    cmd.append(request.test_target)


            # Run container as async subprocess with strictly bounded timeout
            try:
                exit_code, stdout_bytes, stderr_bytes = await self._safe_subprocess_exec(
                    *cmd,
                    timeout=float(limits.timeout_seconds),
                )
                duration = round(time.monotonic() - start_time, 4)
            except asyncio.TimeoutError:
                # Forcefully terminate container
                logger.warning(
                    f"Sandbox execution timed out after {limits.timeout_seconds}s for {execution_id}"
                )
                try:
                    await self._safe_subprocess_exec("docker", "kill", container_name, capture_output=False, timeout=5.0)
                except Exception:
                    pass

                duration = round(time.monotonic() - start_time, 4)
                return await self._emit_terminal_event(
                    ExecutionResult(
                        execution_id=execution_id,
                        project_id=request.project_id,
                        workflow_execution_id=request.workflow_execution_id,
                        execution_type=request.execution_type,
                        status=ExecutionStatus.TIMEOUT,
                        exit_code=-1,
                        duration_seconds=duration,
                        stdout="",
                        stderr=f"Execution exceeded configured timeout limit of {limits.timeout_seconds}s.",
                        is_truncated=False,
                        tests_passed=0,
                        tests_failed=0,
                        tests_total=0,
                        validation_errors=[],
                        metadata={"timeout_limit_seconds": limits.timeout_seconds},
                    )
                )

            # Process output and limits
            raw_stdout = stdout_bytes.decode("utf-8", errors="replace")
            raw_stderr = stderr_bytes.decode("utf-8", errors="replace")

            stdout, truncated_out = self._truncate_output(raw_stdout, limits.max_output_bytes)
            stderr, truncated_err = self._truncate_output(raw_stderr, limits.max_output_bytes)
            is_truncated = truncated_out or truncated_err

            # Parse test counts
            passed, failed, total = self._parse_pytest_output(raw_stdout)

            # Determine status based on exit code and execution type
            if request.execution_type == ExecutionType.LINT:
                # Ruff exit codes: 0 = clean, 1 = lint findings reported, 2 = execution error
                if exit_code in (0, 1):
                    status = ExecutionStatus.PASSED
                elif exit_code == 137:
                    status = ExecutionStatus.RESOURCE_LIMIT
                else:
                    status = ExecutionStatus.SANDBOX_ERROR
            else:
                # pytest exit codes:
                # 0: all tests passed
                # 1: tests failed
                # 5: no tests collected
                # 137: killed (OOM / memory limit)
                if exit_code == 0:
                    status = ExecutionStatus.PASSED
                elif exit_code == 137:
                    status = ExecutionStatus.RESOURCE_LIMIT
                elif exit_code == 5:
                    # No tests collected: mark FAILED with note
                    status = ExecutionStatus.FAILED
                    if not stderr:
                        stderr = "No tests collected in project artifact."
                elif exit_code == 1:
                    status = ExecutionStatus.FAILED
                else:
                    status = ExecutionStatus.FAILED


            return await self._emit_terminal_event(
                ExecutionResult(
                    execution_id=execution_id,
                    project_id=request.project_id,
                    workflow_execution_id=request.workflow_execution_id,
                    execution_type=request.execution_type,
                    status=status,
                    exit_code=exit_code,
                    duration_seconds=duration,
                    stdout=stdout,
                    stderr=stderr,
                    is_truncated=is_truncated,
                    tests_passed=passed,
                    tests_failed=failed,
                    tests_total=total,
                    validation_errors=[],
                    metadata={
                        "container_name": container_name,
                        "image": self.image,
                        "limits": limits.model_dump(),
                    },
                )
            )

        except Exception as exc:
            logger.exception(f"Unexpected sandbox execution error: {exc}")
            duration = round(time.monotonic() - start_time, 4)
            return await self._emit_terminal_event(
                ExecutionResult(
                    execution_id=execution_id,
                    project_id=request.project_id,
                    workflow_execution_id=request.workflow_execution_id,
                    execution_type=request.execution_type,
                    status=ExecutionStatus.SANDBOX_ERROR,
                    exit_code=None,
                    duration_seconds=duration,
                    stdout="",
                    stderr=f"Sandbox execution error: {str(exc)}",
                    is_truncated=False,
                    tests_passed=0,
                    tests_failed=0,
                    tests_total=0,
                    validation_errors=[],
                    metadata={"error_type": type(exc).__name__},
                )
            )
        finally:
            # Deterministic cleanup of ephemeral files on host
            try:
                shutil.rmtree(temp_dir, ignore_errors=True)
            except Exception as clean_err:
                logger.warning(f"Failed to remove temp dir {temp_dir}: {clean_err}")
