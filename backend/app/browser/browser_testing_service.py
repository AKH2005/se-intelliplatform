"""Browser Testing Service for Phase 11J (Stage 3).

Coordinates the end-to-end execution of deterministic browser smoke tests
against isolated application containers on ephemeral Docker networks.

Key Responsibilities:
1. Authoritative resolution of DevelopmentVersion, manifest, and generated code.
2. Cross-project isolation and ownership verification.
3. Concurrency governance (capped at 2 concurrent browser sessions).
4. Strict navigation allowlisting (only the internal application origin is allowed).
5. Safe Playwright/Chromium container execution on the internal Docker network.
6. Diagnostic evidence collection: console errors, network failures, and screenshots.
7. Filesystem-based screenshot storage with bounded dimensions and size limits.
8. Guaranteed deterministic cleanup of browser containers, workspaces, and networks.
"""

import asyncio
import json
import logging
import os
import shutil
import tempfile
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.browser.contracts import (
    DEFAULT_PLAYWRIGHT_IMAGE,
    MAX_CONCURRENT_BROWSER_SESSIONS,
    BrowserLimits,
    BrowserSessionConfig,
    DeterministicBrowserTestDefinition,
    create_default_smoke_suite,
)
from app.browser.deterministic_runner_template import get_runner_script_content
from app.browser.errors import (
    BrowserArtifactError,
    BrowserConfigurationError,
    BrowserErrorBase,
    BrowserExecutionError,
    BrowserNavigationError,
    BrowserResourceLimitError,
    BrowserStartupError,
    BrowserTimeoutError,
)
from app.browser.browser_executor import BrowserExecutor
from app.core.exceptions import NotFoundError, ValidationError
from app.runtime.application_runtime_manager import ApplicationRuntimeManager
from app.runtime.contracts import RuntimeLimits, RuntimeSessionResult, RuntimeStatus
from app.schemas.browser_testing import (
    BrowserArtifactReference,
    BrowserArtifactType,
    BrowserConsoleError,
    BrowserNetworkRecord,
    BrowserTestCaseResult,
    BrowserTestRun,
    BrowserTestStatus,
)
from app.telemetry.contracts import EventSeverity, ExecutionEventType, ExecutionKind
from app.telemetry.publisher import ExecutionEventPublisher

logger = logging.getLogger(__name__)


class BrowserTestingService:
    """Authoritative service orchestrating deterministic UI smoke testing."""

    _concurrency_semaphore: asyncio.Semaphore | None = None

    def __init__(
        self,
        session: AsyncSession | None = None,
        runtime_manager: ApplicationRuntimeManager | None = None,
        browser_executor: BrowserExecutor | None = None,
        artifacts_base_dir: str | Path | None = None,
        max_concurrent: int = MAX_CONCURRENT_BROWSER_SESSIONS,
    ) -> None:
        self.session = session
        self.runtime_manager = runtime_manager or ApplicationRuntimeManager(session=session)
        self.browser_executor = browser_executor or BrowserExecutor()
        self.artifacts_base_dir = Path(artifacts_base_dir or "artifacts")
        self.max_concurrent = max_concurrent
        if BrowserTestingService._concurrency_semaphore is None:
            BrowserTestingService._concurrency_semaphore = asyncio.Semaphore(max_concurrent)

    @classmethod
    def get_semaphore(cls) -> asyncio.Semaphore:
        """Global concurrency semaphore for browser testing sessions."""
        if cls._concurrency_semaphore is None:
            cls._concurrency_semaphore = asyncio.Semaphore(MAX_CONCURRENT_BROWSER_SESSIONS)
        return cls._concurrency_semaphore

    def validate_navigation_target(self, target_url: str, allowed_origin: str) -> None:
        """Enforce strict allowlisting on navigation targets.

        Rejects localhost, 127.0.0.1, external domains, file://, javascript:, data:.
        """
        stripped = target_url.strip()
        stripped_origin = allowed_origin.strip().rstrip("/")

        # Prohibit dangerous schemes
        if any(stripped.lower().startswith(s) for s in ("file:", "javascript:", "data:", "about:")):
            raise BrowserNavigationError(f"Navigation to unsafe scheme prohibited: '{target_url}'")

        # Prohibit localhost / 127.0.0.1 / cloud metadata
        if any(h in stripped.lower() for h in ("localhost", "127.0.0.1", "0.0.0.0", "169.254.")):
            raise BrowserNavigationError(
                f"Navigation to host address prohibited (internal origin only): '{target_url}'"
            )

        # Must start strictly with the internal origin
        if not stripped.startswith(stripped_origin):
            raise BrowserNavigationError(
                f"Target URL '{target_url}' is outside authorized internal origin '{stripped_origin}'"
            )

    async def _emit_terminal_event(self, result: BrowserTestRun) -> BrowserTestRun:
        """Safely emit BROWSER_COMPLETED or BROWSER_FAILED terminal telemetry event."""
        is_success = result.status == BrowserTestStatus.PASSED
        term_evt = (
            ExecutionEventType.BROWSER_COMPLETED
            if is_success
            else ExecutionEventType.BROWSER_FAILED
        )
        await ExecutionEventPublisher.emit(
            event_type=term_evt,
            project_id=result.project_id,
            execution_id=result.run_id,
            execution_kind=ExecutionKind.BROWSER,
            source="BrowserTestingService",
            status=result.status.value,
            severity=EventSeverity.INFO if is_success else EventSeverity.ERROR,
            payload={
                "status": result.status.value,
                "version_id": str(result.version_id) if result.version_id else None,
                "tests_passed": result.tests_passed,
                "tests_failed": result.tests_failed,
                "tests_total": result.tests_total,
                "failure_reason": result.failure_reason,
                "phase": f"Browser tests {result.status.value.lower()}",
                "progress_pct": 100.0 if is_success else None,
            },
        )
        return result

    async def execute_browser_tests(
        self,
        project_id: uuid.UUID,
        version_id: uuid.UUID | None = None,
        test_definitions: list[DeterministicBrowserTestDefinition] | None = None,
        limits: BrowserLimits | None = None,
        files_map: dict[str, str] | None = None,
        manifest: Any | None = None,
    ) -> BrowserTestRun:
        """Run deterministic smoke tests against an isolated application container."""
        run_id = uuid.uuid4()
        started_at = datetime.now(timezone.utc)
        start_time = time.monotonic()
        limits = limits or BrowserLimits()
        semaphore = self.get_semaphore()

        await ExecutionEventPublisher.emit(
            event_type=ExecutionEventType.BROWSER_STARTED,
            project_id=project_id,
            execution_id=run_id,
            execution_kind=ExecutionKind.BROWSER,
            source="BrowserTestingService",
            status="RUNNING",
            payload={
                "version_id": str(version_id) if version_id else None,
                "phase": "Browser tests started",
            },
        )

        # 1. Non-blocking concurrency check
        acquired = False
        try:
            try:
                await asyncio.wait_for(semaphore.acquire(), timeout=0.05)
                acquired = True
            except asyncio.TimeoutError:
                return await self._emit_terminal_event(
                    BrowserTestRun(
                        run_id=run_id,
                        project_id=project_id,
                        version_id=version_id,
                        status=BrowserTestStatus.RESOURCE_LIMIT,
                        failure_reason=(
                            f"Maximum concurrent browser sessions ({self.max_concurrent}) exceeded."
                        ),
                        summary="Browser test execution rejected due to resource limits.",
                        started_at=started_at,
                        completed_at=datetime.now(timezone.utc),
                        duration_seconds=0.0,
                    )
                )

            # 2. Resolve version files and manifest (project isolation check)
            if files_map is not None:
                if manifest is None:
                    from app.schemas.runtime import create_default_fastapi_manifest
                    manifest = create_default_fastapi_manifest()
            else:
                if not version_id:
                    return await self._emit_terminal_event(
                        BrowserTestRun(
                            run_id=run_id,
                            project_id=project_id,
                            version_id=None,
                            status=BrowserTestStatus.VALIDATION_ERROR,
                            failure_reason="Either files_map or version_id must be provided.",
                            summary="Validation error: Missing target version or files.",
                            started_at=started_at,
                            completed_at=datetime.now(timezone.utc),
                            duration_seconds=0.0,
                        )
                    )
                try:
                    files_map, manifest = await self.runtime_manager.resolve_version_files_and_manifest(
                        project_id=project_id,
                        version_id=version_id,
                    )
                except Exception as res_exc:
                    logger.error(f"Failed to resolve version '{version_id}': {res_exc}")
                    return await self._emit_terminal_event(
                        BrowserTestRun(
                            run_id=run_id,
                            project_id=project_id,
                            version_id=version_id,
                            status=BrowserTestStatus.VALIDATION_ERROR,
                            failure_reason=f"Version or artifact resolution failed: {res_exc}",
                            summary="Validation error resolving development version artifact.",
                            started_at=started_at,
                            completed_at=datetime.now(timezone.utc),
                            duration_seconds=round(time.monotonic() - start_time, 3),
                        )
                    )

            # 3. Determine deterministic test suite
            suite = test_definitions or create_default_smoke_suite(manifest.health_check_path)

            # 4. Start Application Runtime Session
            runtime_limits = RuntimeLimits(
                session_timeout_seconds=limits.session_timeout_seconds,
            )

            async with self.runtime_manager.managed_runtime_session(
                project_id=project_id,
                files_map=files_map,
                manifest=manifest,
                version_id=version_id,
                limits=runtime_limits,
            ) as app_session:
                # Check application startup outcome
                if app_session.status != RuntimeStatus.READY:
                    status_map = {
                        RuntimeStatus.RESOURCE_LIMIT: BrowserTestStatus.RESOURCE_LIMIT,
                        RuntimeStatus.STARTUP_FAILED: BrowserTestStatus.STARTUP_FAILED,
                        RuntimeStatus.TIMEOUT: BrowserTestStatus.TIMEOUT,
                        RuntimeStatus.RUNTIME_ERROR: BrowserTestStatus.BROWSER_ERROR,
                    }
                    mapped_status = status_map.get(app_session.status, BrowserTestStatus.STARTUP_FAILED)
                    return await self._emit_terminal_event(
                        BrowserTestRun(
                            run_id=run_id,
                            project_id=project_id,
                            version_id=version_id,
                            status=mapped_status,
                            failure_reason=app_session.failure_reason or "Application failed to become ready.",
                            summary=f"Application container failed with status {app_session.status}.",
                            started_at=started_at,
                            completed_at=datetime.now(timezone.utc),
                            duration_seconds=round(time.monotonic() - start_time, 3),
                        )
                    )

                # Validate internal origin
                internal_url = app_session.internal_url
                for t in suite:
                    full_target = f"{internal_url.rstrip('/')}/{t.target_path.lstrip('/')}"
                    self.validate_navigation_target(full_target, internal_url)

                # 5. Check if browser image is available
                if not await self.browser_executor.check_image_available():
                    return await self._emit_terminal_event(
                        BrowserTestRun(
                            run_id=run_id,
                            project_id=project_id,
                            version_id=version_id,
                            status=BrowserTestStatus.BROWSER_ERROR,
                            failure_reason=(
                                f"Playwright browser image '{self.browser_executor.image}' is unavailable."
                            ),
                            summary="Browser execution environment unavailable.",
                            started_at=started_at,
                            completed_at=datetime.now(timezone.utc),
                            duration_seconds=round(time.monotonic() - start_time, 3),
                        )
                    )

                # 6. Execute tests inside browser container
                result = await self._execute_in_browser_container(
                    run_id=run_id,
                    project_id=project_id,
                    version_id=version_id,
                    app_session=app_session,
                    suite=suite,
                    limits=limits,
                    started_at=started_at,
                    start_time=start_time,
                )
                if version_id:
                    await self._persist_run_result(project_id, version_id, result)
                return await self._emit_terminal_event(result)

        finally:
            if acquired:
                semaphore.release()

    async def _execute_in_browser_container(
        self,
        run_id: uuid.UUID,
        project_id: uuid.UUID,
        version_id: uuid.UUID,
        app_session: RuntimeSessionResult,
        suite: list[DeterministicBrowserTestDefinition],
        limits: BrowserLimits,
        started_at: datetime,
        start_time: float,
    ) -> BrowserTestRun:
        """Run Playwright container on app network and assemble evidence."""
        temp_dir = tempfile.mkdtemp(prefix="se_browser_run_")
        container_name = f"browser-{run_id}"

        try:
            # 1. Prepare container workspace
            runner_code = get_runner_script_content()
            with open(os.path.join(temp_dir, "runner.py"), "w", encoding="utf-8") as rf:
                rf.write(runner_code)

            config_payload = {
                "base_url": app_session.internal_url,
                "allowed_origin": app_session.internal_url,
                "tests": [t.model_dump() for t in suite],
                "limits": limits.model_dump(),
            }
            with open(os.path.join(temp_dir, "config.json"), "w", encoding="utf-8") as cf:
                json.dump(config_payload, cf, indent=2)

            os.makedirs(os.path.join(temp_dir, "screenshots"), exist_ok=True)

            await ExecutionEventPublisher.emit(
                event_type=ExecutionEventType.BROWSER_PROGRESS,
                project_id=project_id,
                execution_id=run_id,
                execution_kind=ExecutionKind.BROWSER,
                source="BrowserTestingService",
                status="RUNNING",
                payload={
                    "version_id": str(version_id) if version_id else None,
                    "container_name": container_name,
                    "phase": "Executing browser test suite",
                    "progress_pct": 50.0,
                },
            )

            # 2. Launch browser container
            try:
                exit_code, stdout, stderr = await self.browser_executor.run_browser_container(
                    container_name=container_name,
                    network_name=app_session.network_name,
                    workspace_dir=temp_dir,
                    limits=limits,
                )
            except BrowserTimeoutError as te:
                return BrowserTestRun(
                    run_id=run_id,
                    project_id=project_id,
                    version_id=version_id,
                    status=BrowserTestStatus.TIMEOUT,
                    failure_reason=str(te),
                    summary="Browser test execution exceeded bounded session timeout.",
                    started_at=started_at,
                    completed_at=datetime.now(timezone.utc),
                    duration_seconds=round(time.monotonic() - start_time, 3),
                )
            except BrowserStartupError as se:
                return BrowserTestRun(
                    run_id=run_id,
                    project_id=project_id,
                    version_id=version_id,
                    status=BrowserTestStatus.BROWSER_ERROR,
                    failure_reason=str(se),
                    summary="Browser container failed to start.",
                    started_at=started_at,
                    completed_at=datetime.now(timezone.utc),
                    duration_seconds=round(time.monotonic() - start_time, 3),
                )

            # 3. Read output results.json
            results_path = os.path.join(temp_dir, "results.json")
            if not os.path.exists(results_path):
                return BrowserTestRun(
                    run_id=run_id,
                    project_id=project_id,
                    version_id=version_id,
                    status=BrowserTestStatus.BROWSER_ERROR,
                    failure_reason=f"Browser runner produced no results file. exit_code={exit_code}. stderr: {stderr[:500]}",
                    summary="Browser execution ended without valid test output.",
                    started_at=started_at,
                    completed_at=datetime.now(timezone.utc),
                    duration_seconds=round(time.monotonic() - start_time, 3),
                )

            with open(results_path, "r", encoding="utf-8") as rf:
                raw_results = json.load(rf)

            raw_cases = raw_results.get("test_cases", [])

            # 4. Process screenshots and copy into authoritative storage
            dest_dir = (
                self.artifacts_base_dir
                / "projects"
                / str(project_id)
                / "versions"
                / str(version_id)
                / "browser"
                / str(run_id)
            )
            dest_dir.mkdir(parents=True, exist_ok=True)

            processed_cases: list[BrowserTestCaseResult] = []
            all_artifacts: list[BrowserArtifactReference] = []

            for raw_c in raw_cases:
                case_screenshots: list[BrowserArtifactReference] = []
                for s in raw_c.get("screenshots", []):
                    rel_src = s.get("file_path", "")
                    src_file = os.path.join(temp_dir, rel_src)
                    if os.path.exists(src_file):
                        fname = os.path.basename(src_file)
                        dest_file = dest_dir / fname
                        shutil.copy2(src_file, dest_file)
                        size_b = dest_file.stat().st_size

                        # Storage relative path
                        rel_storage_path = (
                            f"artifacts/projects/{project_id}/versions/{version_id}/browser/{run_id}/{fname}"
                        )
                        art_ref = BrowserArtifactReference(
                            artifact_type=BrowserArtifactType.SCREENSHOT,
                            file_path=rel_storage_path,
                            size_bytes=size_b,
                            content_type="image/png",
                            caption=s.get("caption") or f"Screenshot for {raw_c.get('test_id')}",
                        )
                        case_screenshots.append(art_ref)
                        all_artifacts.append(art_ref)

                case_result = BrowserTestCaseResult(
                    test_id=raw_c.get("test_id", "test"),
                    name=raw_c.get("name", "Test"),
                    status=BrowserTestStatus(raw_c.get("status", "FAILED")),
                    duration_seconds=raw_c.get("duration_seconds", 0.0),
                    failed_step=raw_c.get("failed_step"),
                    assertion_summary=raw_c.get("assertion_summary"),
                    screenshots=case_screenshots,
                    console_errors=[
                        BrowserConsoleError(**ce) for ce in raw_c.get("console_errors", [])[:10]
                    ],
                    network_errors=[
                        BrowserNetworkRecord(**ne) for ne in raw_c.get("network_errors", [])[:10]
                    ],
                    metadata=raw_c.get("metadata", {}),
                )
                processed_cases.append(case_result)

            # 5. Aggregate outcomes
            total = len(processed_cases)
            passed = sum(1 for c in processed_cases if c.status == BrowserTestStatus.PASSED)
            failed = sum(1 for c in processed_cases if c.status == BrowserTestStatus.FAILED)
            terminal_status = (
                BrowserTestStatus.PASSED if (failed == 0 and total > 0) else BrowserTestStatus.FAILED
            )

            failure_reason = None
            if terminal_status == BrowserTestStatus.FAILED:
                failed_cases = [c for c in processed_cases if c.status == BrowserTestStatus.FAILED]
                summaries = [f"{c.test_id}: {c.failed_step}" for c in failed_cases if c.failed_step]
                failure_reason = "; ".join(summaries) or f"{failed} of {total} test cases failed."

            summary = f"{passed}/{total} browser smoke test cases passed in {round(time.monotonic() - start_time, 2)}s."

            return BrowserTestRun(
                run_id=run_id,
                project_id=project_id,
                version_id=version_id,
                status=terminal_status,
                tests_total=total,
                tests_passed=passed,
                tests_failed=failed,
                tests_skipped=0,
                duration_seconds=round(time.monotonic() - start_time, 3),
                test_cases=processed_cases,
                failure_reason=failure_reason,
                summary=summary,
                artifacts=all_artifacts,
                started_at=started_at,
                completed_at=datetime.now(timezone.utc),
                metadata={
                    "browser_image": self.browser_executor.image,
                    "application_url": app_session.internal_url,
                    "network_name": app_session.network_name,
                },
            )

        finally:
            # Deterministic cleanup
            try:
                await self.browser_executor.stop_and_remove_container(container_name)
            except Exception as exc:
                logger.warning(f"Error removing browser container '{container_name}': {exc}")

            try:
                shutil.rmtree(temp_dir, ignore_errors=True)
            except Exception as exc:
                logger.warning(f"Error removing browser temp dir '{temp_dir}': {exc}")

    async def _persist_run_result(
        self,
        project_id: uuid.UUID,
        version_id: uuid.UUID,
        run_result: BrowserTestRun,
    ) -> None:
        """Persist BrowserTestRun metadata and update version verification status."""
        if not self.session:
            return

        from sqlalchemy import select
        from sqlalchemy.orm.attributes import flag_modified
        from app.models.development_version import DevelopmentVersion
        from app.models.workflow_execution import WorkflowExecution

        stmt = select(DevelopmentVersion).where(
            DevelopmentVersion.id == version_id,
            DevelopmentVersion.project_id == project_id,
        )
        res = await self.session.execute(stmt)
        version = res.scalar_one_or_none()
        if not version:
            return

        run_dict = run_result.model_dump(mode="json")

        # CRITICAL IMMUTABILITY ENFORCEMENT:
        # DevelopmentVersion is an immutable historical record.
        # Browser execution MUST NOT mutate version.metadata_payload, version.status,
        # or version.verification_summary.
        #
        # Approved architecture:
        # DevelopmentVersion -> workflow_execution_id -> WorkflowExecution.artifacts["browser_test_run"]
        wf = None
        if version.workflow_execution_id:
            stmt_wf = select(WorkflowExecution).where(
                WorkflowExecution.workflow_execution_id == version.workflow_execution_id,
                WorkflowExecution.project_id == project_id,
            )
            wf_res = await self.session.execute(stmt_wf)
            wf = wf_res.scalar_one_or_none()

        if wf:
            artifacts = dict(wf.artifacts or {})
            artifacts["browser_test_run"] = run_dict
            wf_history = list(artifacts.get("browser_test_runs") or [])
            wf_history.append(run_dict)
            artifacts["browser_test_runs"] = wf_history
            wf.artifacts = artifacts
            flag_modified(wf, "artifacts")
        else:
            # Create a dedicated WorkflowExecution record for provenance
            from app.models.workflow_execution import WorkflowExecutionStatus
            wf_corr_id = uuid.uuid4()
            wf = WorkflowExecution(
                workflow_execution_id=wf_corr_id,
                project_id=project_id,
                workflow_id="browser-testing",
                workflow_version="1.0.0",
                status=(
                    WorkflowExecutionStatus.COMPLETED
                    if run_result.status == BrowserTestStatus.PASSED
                    else WorkflowExecutionStatus.FAILED
                ),
                artifacts={
                    "browser_test_run": run_dict,
                    "browser_test_runs": [run_dict],
                },
            )
            self.session.add(wf)
            if not version.workflow_execution_id:
                version.workflow_execution_id = wf_corr_id

        try:
            await self.session.commit()
            if wf:
                await self.session.refresh(wf)
        except Exception as e:
            logger.warning(f"Failed to commit browser test run persistence: {e}")
            await self.session.rollback()

    _persist_browser_test_results = _persist_run_result

    async def get_latest_browser_test_run(
        self,
        project_id: uuid.UUID,
        version_id: uuid.UUID | None = None,
    ) -> BrowserTestRun | None:
        """Retrieve the latest BrowserTestRun for a project or specific version.
        
        Resolves via WorkflowExecution.artifacts['browser_test_run'] linked to the version.
        """
        if not self.session:
            return None

        from sqlalchemy import select
        from app.models.development_version import DevelopmentVersion
        from app.models.project import Project
        from app.models.workflow_execution import WorkflowExecution

        # 1. Project ownership check
        proj_stmt = select(Project.id).where(Project.id == project_id)
        proj_res = await self.session.execute(proj_stmt)
        if not proj_res.scalar_one_or_none():
            raise NotFoundError("Project", str(project_id))

        if version_id:
            ver_stmt = select(DevelopmentVersion).where(
                DevelopmentVersion.id == version_id,
                DevelopmentVersion.project_id == project_id,
            )
            ver_res = await self.session.execute(ver_stmt)
            ver = ver_res.scalar_one_or_none()
            if not ver:
                raise NotFoundError("DevelopmentVersion", str(version_id))

            # Retrieve from associated WorkflowExecution
            if ver.workflow_execution_id:
                wf_stmt = select(WorkflowExecution).where(
                    WorkflowExecution.workflow_execution_id == ver.workflow_execution_id,
                    WorkflowExecution.project_id == project_id,
                )
                wf_res = await self.session.execute(wf_stmt)
                wf = wf_res.scalar_one_or_none()
                if wf and wf.artifacts and "browser_test_run" in wf.artifacts:
                    return BrowserTestRun.model_validate(wf.artifacts["browser_test_run"])

            # Read-only fallback for legacy metadata_payload
            meta = ver.metadata_payload or {}
            latest_run = meta.get("latest_browser_test_run")
            if latest_run:
                return BrowserTestRun.model_validate(latest_run)
            return None

        # If version_id is None, query versions in descending order
        stmt = (
            select(DevelopmentVersion)
            .where(DevelopmentVersion.project_id == project_id)
            .order_by(DevelopmentVersion.version_number.desc())
        )
        res = await self.session.execute(stmt)
        versions = res.scalars().all()
        for v in versions:
            if v.workflow_execution_id:
                wf_stmt = select(WorkflowExecution).where(
                    WorkflowExecution.workflow_execution_id == v.workflow_execution_id,
                    WorkflowExecution.project_id == project_id,
                )
                wf_res = await self.session.execute(wf_stmt)
                wf = wf_res.scalar_one_or_none()
                if wf and wf.artifacts and "browser_test_run" in wf.artifacts:
                    return BrowserTestRun.model_validate(wf.artifacts["browser_test_run"])

            # Read-only fallback for legacy metadata_payload
            meta = v.metadata_payload or {}
            latest_run = meta.get("latest_browser_test_run")
            if latest_run:
                return BrowserTestRun.model_validate(latest_run)

        # Also search direct browser-testing workflow executions for this project
        wf_direct_stmt = (
            select(WorkflowExecution)
            .where(
                WorkflowExecution.project_id == project_id,
                WorkflowExecution.workflow_id == "browser-testing",
            )
            .order_by(WorkflowExecution.created_at.desc())
        )
        wf_direct_res = await self.session.execute(wf_direct_stmt)
        for wf_record in wf_direct_res.scalars().all():
            if wf_record.artifacts and "browser_test_run" in wf_record.artifacts:
                return BrowserTestRun.model_validate(wf_record.artifacts["browser_test_run"])

        return None

    async def get_browser_test_run(
        self,
        project_id: uuid.UUID,
        run_id: uuid.UUID,
    ) -> BrowserTestRun | None:
        """Retrieve a specific BrowserTestRun by run_id within project scope."""
        if not self.session:
            return None

        from sqlalchemy import select
        from app.models.development_version import DevelopmentVersion
        from app.models.project import Project
        from app.models.workflow_execution import WorkflowExecution

        proj_stmt = select(Project.id).where(Project.id == project_id)
        proj_res = await self.session.execute(proj_stmt)
        if not proj_res.scalar_one_or_none():
            raise NotFoundError("Project", str(project_id))

        run_id_str = str(run_id)

        # 1. Search in WorkflowExecution artifacts for this project
        wf_stmt = select(WorkflowExecution).where(WorkflowExecution.project_id == project_id)
        wf_res = await self.session.execute(wf_stmt)
        for wf in wf_res.scalars().all():
            artifacts = wf.artifacts or {}
            latest_run = artifacts.get("browser_test_run")
            if latest_run and str(latest_run.get("run_id")) == run_id_str:
                return BrowserTestRun.model_validate(latest_run)
            for r in artifacts.get("browser_test_runs", []):
                if str(r.get("run_id")) == run_id_str:
                    return BrowserTestRun.model_validate(r)

        # 2. Read-only fallback in DevelopmentVersion metadata_payload
        stmt = select(DevelopmentVersion).where(DevelopmentVersion.project_id == project_id)
        res = await self.session.execute(stmt)
        versions = res.scalars().all()
        for v in versions:
            meta = v.metadata_payload or {}
            latest_run = meta.get("latest_browser_test_run")
            if latest_run and str(latest_run.get("run_id")) == run_id_str:
                return BrowserTestRun.model_validate(latest_run)
            for r in meta.get("browser_test_runs", []):
                if str(r.get("run_id")) == run_id_str:
                    return BrowserTestRun.model_validate(r)

        return None

    def get_screenshot_path(
        self,
        project_id: uuid.UUID,
        run_id: uuid.UUID,
        filename: str,
    ) -> Path:
        """Deterministically and securely locate a screenshot file for a run.
        
        Strict security invariants:
        - Filename must be alphanumeric + dashes/underscores/dots with .png/.webp/.jpg extension.
        - Directory traversal ('..', '/', '\\') is strictly prohibited.
        - Must resolve strictly under the project's authorized artifacts directory.
        """
        import re

        clean_filename = filename.strip()
        if not re.match(r"^[a-zA-Z0-9_\-\.]+\.(png|webp|jpg)$", clean_filename, re.IGNORECASE):
            raise ValidationError(f"Invalid screenshot filename format: '{filename}'")
        if ".." in clean_filename or "/" in clean_filename or "\\" in clean_filename:
            raise ValidationError("Path traversal is strictly prohibited.")

        project_dir = (self.artifacts_base_dir / "projects" / str(project_id)).resolve()
        if not project_dir.exists():
            raise NotFoundError("ProjectArtifacts", str(project_id))

        # Search within project versions for run_id/filename
        matches = list(project_dir.glob(f"versions/*/browser/{run_id}/{clean_filename}"))
        if not matches:
            raise NotFoundError("Screenshot", clean_filename)

        target_file = matches[0].resolve()
        if not str(target_file).startswith(str(project_dir)):
            raise ValidationError("Unauthorized path access outside project storage.")

        if not target_file.is_file():
            raise NotFoundError("Screenshot", clean_filename)

        return target_file

    async def execute_validated_browser_journey_suite(
        self,
        suite: Any,
        limits: BrowserLimits | None = None,
        files_map: dict[str, str] | None = None,
        manifest: Any | None = None,
        version_id: uuid.UUID | None = None,
    ) -> BrowserTestRun:
        """Execute an authoritatively validated browser journey suite using Phase 11J infrastructure.

        Strictly enforces that ONLY ValidatedBrowserJourneySuite can be adapted and executed.
        Translates journeys to deterministic test definitions via BrowserJourneyAdapter,
        and delegates execution to the authoritative BrowserTestingService.execute_browser_tests.
        """
        from app.browser.journey.adapter import BrowserJourneyAdapter
        from app.browser.journey.contracts import ValidatedBrowserJourneySuite

        if not isinstance(suite, ValidatedBrowserJourneySuite):
            raise TypeError(
                f"execute_validated_browser_journey_suite requires ValidatedBrowserJourneySuite, "
                f"got {type(suite).__name__}. Unvalidated candidate suites cannot be executed."
            )

        test_definitions = BrowserJourneyAdapter.adapt(suite)

        return await self.execute_browser_tests(
            project_id=suite.project_id,
            version_id=version_id,
            test_definitions=test_definitions,
            limits=limits,
            files_map=files_map,
            manifest=manifest,
        )

