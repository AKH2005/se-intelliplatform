"""Hardened Docker Runtime Executor for Phase 11J Application Runtime.

This module encapsulates all Docker operations for launching, health-probing,
and tearing down isolated, non-networked (internal bridge) application containers.

Security Guarantees:
1. No host port publishing (-p and --publish are strictly prohibited).
2. Ephemeral user-defined Docker bridge created with --internal (zero external WAN routing).
3. Hardened container flags: --cap-drop=ALL, --security-opt=no-new-privileges:true, --read-only.
4. Non-root user execution (UID 2000:2000).
5. No Docker socket access (/var/run/docker.sock is NEVER mounted).
6. Read-only application workspace mount (-v host_dir:/workspace:ro).
7. Writable memory-backed tmpfs only (/tmp and /home/sandboxuser).
8. Fixed executable invocation via asyncio.create_subprocess_exec (NEVER shell=True).
9. Bounded stdout/stderr log capture.
10. Guaranteed resource cleanup.
"""

import asyncio
import logging
import os
import re
import subprocess
import time
from typing import Any

from app.runtime.contracts import (
    DEFAULT_APPLICATION_MEMORY_LIMIT,
    DEFAULT_APPLICATION_CPUS,
    DEFAULT_APPLICATION_MAX_PIDS,
    DEFAULT_STARTUP_TIMEOUT_SECONDS,
    MAX_LOG_BYTES,
    MAX_LOG_LINES,
    RuntimeLimits,
)
from app.runtime.errors import (
    DockerUnavailableError,
    RuntimeStartupError,
    RuntimeTimeoutError,
)
from app.schemas.runtime import ApplicationRuntimeManifest

logger = logging.getLogger(__name__)

DEFAULT_APPLICATION_RUNTIME_IMAGE: str = "se-intelliplatform-sandbox:latest"


class DockerRuntimeExecutor:
    """Executes and manages lifecycle of isolated application runtime containers in Docker."""

    def __init__(self, image: str = DEFAULT_APPLICATION_RUNTIME_IMAGE) -> None:
        self.image = image
        self._docker_available: bool | None = None

    async def check_docker_available(self) -> bool:
        """Check if Docker daemon is responsive."""
        if self._docker_available is not None:
            return self._docker_available

        try:
            try:
                proc = await asyncio.create_subprocess_exec(
                    "docker",
                    "info",
                    stdout=asyncio.subprocess.DEVNULL,
                    stderr=asyncio.subprocess.DEVNULL,
                )
                try:
                    exit_code = await asyncio.wait_for(proc.wait(), timeout=5.0)
                    self._docker_available = (exit_code == 0)
                except asyncio.TimeoutError:
                    try:
                        proc.kill()
                    except Exception:
                        pass
                    self._docker_available = False
            except NotImplementedError:
                def _sync_check():
                    res = subprocess.run(
                        ["docker", "info"],
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL,
                        timeout=5.0,
                        shell=False,
                    )
                    return res.returncode == 0
                self._docker_available = await asyncio.to_thread(_sync_check)
        except Exception as exc:
            logger.warning(f"Docker availability check failed: {exc}")
            self._docker_available = False

        return self._docker_available

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

    async def create_internal_network(self, network_name: str) -> None:
        """Create a dedicated, isolated Docker bridge network with WAN access completely disabled."""
        if not await self.check_docker_available():
            raise DockerUnavailableError("Docker daemon is unavailable.")

        cmd = ["docker", "network", "create", "--internal", network_name]
        logger.info(f"Creating internal Docker network: {network_name}")
        ret, stdout, stderr = await self._safe_subprocess_exec(*cmd)
        if ret != 0:
            err_msg = stderr.decode("utf-8", errors="replace").strip()
            raise RuntimeStartupError(f"Failed to create internal Docker network '{network_name}': {err_msg}")

    async def remove_network(self, network_name: str) -> None:
        """Remove the internal Docker network cleanly."""
        try:
            await self._safe_subprocess_exec("docker", "network", "rm", network_name, capture_output=False, timeout=5.0)
            logger.info(f"Removed internal Docker network: {network_name}")
        except Exception as exc:
            logger.warning(f"Failed to remove Docker network '{network_name}': {exc}")

    async def start_application_container(
        self,
        container_name: str,
        network_name: str,
        workspace_dir: str,
        manifest: ApplicationRuntimeManifest,
        limits: RuntimeLimits,
    ) -> None:
        """Launch the application server container with strict security bounds.
        
        CRITICAL: Never publishes host ports (-p is forbidden).
        """
        if not await self.check_docker_available():
            raise DockerUnavailableError("Docker daemon is unavailable.")

        norm_workspace = os.path.abspath(workspace_dir)

        # Build hardened docker run argument vector
        cmd = [
            "docker",
            "run",
            "-d",
            "--name",
            container_name,
            "--network",
            network_name,
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
            f"{norm_workspace}:/workspace:ro",
            "-w",
            "/workspace",
            "-u",
            "2000:2000",
            "-e",
            "PYTHONPATH=/workspace",
            "-e",
            "PYTHONDONTWRITEBYTECODE=1",
            "-e",
            "PYTHONUNBUFFERED=1",
            "-e",
            "DATABASE_URL=sqlite:////tmp/app.db",
        ]

        # Add image
        cmd.append(self.image)

        # Add validated startup command argument vector (no shell=True)
        cmd.extend(manifest.startup_command)

        logger.info(f"Starting application container '{container_name}' on network '{network_name}'")
        ret, stdout, stderr = await self._safe_subprocess_exec(*cmd)
        if ret != 0:
            err_msg = stderr.decode("utf-8", errors="replace").strip()
            raise RuntimeStartupError(
                f"Failed to start application container '{container_name}': {err_msg}"
            )

    async def get_container_status(self, container_name: str) -> tuple[bool, int | None]:
        """Inspect container state returning (is_running, exit_code)."""
        cmd = [
            "docker",
            "inspect",
            "--format",
            "{{.State.Running}} {{.State.ExitCode}}",
            container_name,
        ]
        try:
            ret, stdout, _ = await self._safe_subprocess_exec(*cmd, timeout=5.0)
            if ret != 0:
                return False, None
            parts = stdout.decode("utf-8").strip().split()
            if len(parts) >= 2:
                is_running = parts[0].lower() == "true"
                exit_code = int(parts[1])
                return is_running, exit_code
        except Exception:
            pass
        return False, None

    async def poll_health(
        self,
        container_name: str,
        port: int,
        path: str,
        method: str = "GET",
        timeout_seconds: float = DEFAULT_STARTUP_TIMEOUT_SECONDS,
        interval_seconds: float = 0.5,
    ) -> tuple[bool, str]:
        """Poll application internal HTTP health endpoint from inside the container namespace.
        
        Requires NO host port binding. Uses unprivileged python probe inside the running container.
        """
        start_time = time.monotonic()
        probe_code = (
            f"import http.client, sys; "
            f"conn = http.client.HTTPConnection('127.0.0.1', {port}, timeout=2); "
            f"conn.request('{method}', '{path}'); "
            f"res = conn.getresponse(); "
            f"sys.exit(0 if res.status in (200, 301, 302, 307) else 1)"
        )

        while time.monotonic() - start_time < timeout_seconds:
            is_running, exit_code = await self.get_container_status(container_name)
            if not is_running:
                return False, f"Container exited prematurely with exit code {exit_code}."

            cmd = [
                "docker",
                "exec",
                "-u",
                "2000:2000",
                container_name,
                "python",
                "-c",
                probe_code,
            ]
            try:
                ret, _, _ = await self._safe_subprocess_exec(*cmd, capture_output=False, timeout=3.0)
                if ret == 0:
                    elapsed = round(time.monotonic() - start_time, 2)
                    return True, f"Application healthy at '{path}' (readiness confirmed in {elapsed}s)."
            except Exception:
                pass

            await asyncio.sleep(interval_seconds)

        return False, f"Health check timed out after {timeout_seconds}s probing '{path}' on port {port}."

    async def get_container_logs(
        self,
        container_name: str,
        max_bytes: int = MAX_LOG_BYTES,
    ) -> tuple[str, str, bool]:
        """Collect bounded stdout and stderr from container."""
        cmd = ["docker", "logs", "--tail", str(MAX_LOG_LINES), container_name]
        try:
            _, stdout_bytes, stderr_bytes = await self._safe_subprocess_exec(*cmd, timeout=5.0)
            raw_stdout = stdout_bytes.decode("utf-8", errors="replace")
            raw_stderr = stderr_bytes.decode("utf-8", errors="replace")

            is_truncated = len(stdout_bytes) > max_bytes or len(stderr_bytes) > max_bytes
            stdout = raw_stdout[:max_bytes]
            stderr = raw_stderr[:max_bytes]
            return stdout, stderr, is_truncated
        except Exception as exc:
            return "", f"Failed to retrieve container logs: {exc}", False

    async def stop_and_remove_container(
        self,
        container_name: str,
        timeout_seconds: float = 3.0,
    ) -> None:
        """Gracefully stop container and force remove."""
        try:
            await self._safe_subprocess_exec(
                "docker", "stop", "-t", "2", container_name, capture_output=False, timeout=timeout_seconds
            )
        except Exception:
            pass

        try:
            await self._safe_subprocess_exec(
                "docker", "rm", "-f", container_name, capture_output=False, timeout=5.0
            )
            logger.info(f"Removed container '{container_name}'")
        except Exception as exc:
            logger.warning(f"Failed to remove container '{container_name}': {exc}")
