"""Application Runtime Manager for Phase 11J Isolated Docker Runtime.

Coordinates resolution of DevelopmentVersion, ApplicationRuntimeManifest validation,
ephemeral workspace creation, isolated internal Docker network allocation, container
execution, health-check polling, concurrency governance, and guaranteed teardown.
"""

import asyncio
from contextlib import asynccontextmanager
import logging
import os
import re
import shutil
import tempfile
import time
import uuid
from datetime import datetime, timezone
from typing import Any, AsyncGenerator

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError, ValidationError
from app.models.development_version import DevelopmentVersion
from app.models.project import Project
from app.models.workflow_execution import WorkflowExecution
from app.runtime.contracts import (
    MAX_CONCURRENT_RUNTIMES,
    MAX_SESSION_TIMEOUT_SECONDS,
    RuntimeLimits,
    RuntimeSessionConfig,
    RuntimeSessionResult,
    RuntimeStatus,
)
from app.runtime.docker_runtime_executor import (
    DEFAULT_APPLICATION_RUNTIME_IMAGE,
    DockerRuntimeExecutor,
)
from app.runtime.errors import (
    DockerUnavailableError,
    RuntimeConfigurationError,
    RuntimeIsolationError,
    RuntimeResourceLimitError,
    RuntimeStartupError,
    RuntimeTimeoutError,
)
from app.schemas.runtime import (
    ApplicationRuntimeManifest,
    create_default_fastapi_manifest,
)

logger = logging.getLogger(__name__)


class ApplicationRuntimeManager:
    """Authoritative orchestrator for isolated application runtime sessions."""

    _concurrency_semaphore: asyncio.Semaphore | None = None

    def __init__(
        self,
        session: AsyncSession | None = None,
        docker_executor: DockerRuntimeExecutor | None = None,
        max_concurrent: int = MAX_CONCURRENT_RUNTIMES,
    ) -> None:
        self.session = session
        self.docker_executor = docker_executor or DockerRuntimeExecutor()
        self.max_concurrent = max_concurrent
        if ApplicationRuntimeManager._concurrency_semaphore is None:
            ApplicationRuntimeManager._concurrency_semaphore = asyncio.Semaphore(max_concurrent)

    @classmethod
    def get_semaphore(cls) -> asyncio.Semaphore:
        """Access global concurrency semaphore."""
        if cls._concurrency_semaphore is None:
            cls._concurrency_semaphore = asyncio.Semaphore(MAX_CONCURRENT_RUNTIMES)
        return cls._concurrency_semaphore

    async def resolve_version_files_and_manifest(
        self,
        project_id: uuid.UUID,
        version_id: uuid.UUID,
    ) -> tuple[dict[str, str], ApplicationRuntimeManifest]:
        """Resolve generated file contents and validated runtime manifest from DevelopmentVersion."""
        if not self.session:
            raise ValidationError("Database session is required to resolve DevelopmentVersion.")

        # 1. Authoritative ownership check
        stmt = select(DevelopmentVersion).where(
            DevelopmentVersion.id == version_id,
            DevelopmentVersion.project_id == project_id,
        )
        res = await self.session.execute(stmt)
        version = res.scalar_one_or_none()
        if not version:
            raise NotFoundError("DevelopmentVersion", str(version_id))

        # 2. Fetch WorkflowExecution artifacts
        if not version.workflow_execution_id:
            raise ValidationError(
                f"DevelopmentVersion '{version_id}' has no associated workflow execution."
            )

        stmt_wf = select(WorkflowExecution).where(
            WorkflowExecution.workflow_execution_id == version.workflow_execution_id,
            WorkflowExecution.project_id == project_id,
        )
        res_wf = await self.session.execute(stmt_wf)
        wf = res_wf.scalar_one_or_none()
        if not wf or not wf.artifacts:
            raise ValidationError(
                f"WorkflowExecution '{version.workflow_execution_id}' has no valid artifacts."
            )

        # 3. Extract code generation files map
        code_data = wf.artifacts.get(version.artifact_key)
        if not code_data:
            if version.artifact_key == "code-generation" and "code_generation" in wf.artifacts:
                code_data = wf.artifacts["code_generation"]
            elif version.artifact_key == "code_generation" and "code-generation" in wf.artifacts:
                code_data = wf.artifacts["code-generation"]

        if not code_data:
            raise ValidationError(
                f"Code artifact key '{version.artifact_key}' missing in execution artifacts."
            )

        if hasattr(code_data, "generated_files"):
            generated_files = code_data.generated_files
        elif isinstance(code_data, dict):
            generated_files = code_data.get("generated_files", [])
        else:
            generated_files = []

        if not generated_files:
            raise ValidationError("Generated code artifact contains zero files.")

        files_map: dict[str, str] = {}
        for f in generated_files:
            p = f.get("path") if isinstance(f, dict) else getattr(f, "path", None)
            c = f.get("content", "") if isinstance(f, dict) else getattr(f, "content", "")
            if p:
                files_map[p] = c

        # 4. Resolve Runtime Manifest
        raw_manifest = (version.metadata_payload or {}).get("runtime_manifest") or wf.artifacts.get("runtime_manifest")
        if raw_manifest:
            try:
                manifest = ApplicationRuntimeManifest.model_validate(raw_manifest)
            except Exception as e:
                raise RuntimeConfigurationError(f"Malformed ApplicationRuntimeManifest in version metadata: {e}")
        else:
            # Deterministic default FastAPI manifest
            manifest = create_default_fastapi_manifest()

        return files_map, manifest

    def materialize_workspace(
        self,
        files_map: dict[str, str],
        temp_dir: str,
    ) -> None:
        """Materialize generated files safely into an ephemeral host directory."""
        abs_base = os.path.abspath(temp_dir)
        for rel_path, content in files_map.items():
            clean_path = rel_path.replace("\\", "/").strip()
            if clean_path.startswith("/") or ".." in clean_path or re.search(r"^[a-zA-Z]:", clean_path):
                raise RuntimeIsolationError(f"Unsafe path in generated artifact: '{rel_path}'")

            target_path = os.path.abspath(os.path.join(abs_base, clean_path))
            if not target_path.startswith(abs_base):
                raise RuntimeIsolationError(f"Path traversal detected for file: '{rel_path}'")

            os.makedirs(os.path.dirname(target_path), exist_ok=True)
            with open(target_path, "w", encoding="utf-8") as fp:
                fp.write(content)

    @asynccontextmanager
    async def managed_runtime_session(
        self,
        project_id: uuid.UUID,
        files_map: dict[str, str],
        manifest: ApplicationRuntimeManifest,
        version_id: uuid.UUID | None = None,
        limits: RuntimeLimits | None = None,
    ) -> AsyncGenerator[RuntimeSessionResult, None]:
        """Context manager providing an active, health-verified application container session.
        
        Guarantees:
        - Strict concurrency limit (max 2 concurrent sessions).
        - Hard teardown of containers, networks, and workspaces on exit.
        """
        limits = limits or RuntimeLimits()
        semaphore = self.get_semaphore()

        # Non-blocking concurrency check
        acquired = False
        try:
            try:
                await asyncio.wait_for(semaphore.acquire(), timeout=0.05)
                acquired = True
            except asyncio.TimeoutError:
                yield RuntimeSessionResult(
                    project_id=project_id,
                    version_id=version_id,
                    status=RuntimeStatus.RESOURCE_LIMIT,
                    internal_url="",
                    container_name="",
                    network_name="",
                    resource_limit_reason=(
                        f"Maximum concurrent application runtime sessions ({self.max_concurrent}) exceeded."
                    ),
                    failure_reason="Server concurrency limit reached.",
                )
                return

            session_id = uuid.uuid4()
            container_name = f"app-{session_id}"
            network_name = f"se_net_{session_id}"
            internal_url = f"http://app-{session_id}:{manifest.application_port}"
            temp_dir = tempfile.mkdtemp(prefix="se_app_runtime_")
            start_time = time.monotonic()
            started_at = datetime.now(timezone.utc)

            try:
                # 1. Materialize workspace
                self.materialize_workspace(files_map, temp_dir)

                # 2. Check Docker availability
                if not await self.docker_executor.check_docker_available():
                    yield RuntimeSessionResult(
                        runtime_id=session_id,
                        project_id=project_id,
                        version_id=version_id,
                        status=RuntimeStatus.RUNTIME_ERROR,
                        internal_url="",
                        container_name=container_name,
                        network_name=network_name,
                        failure_reason="Docker daemon is unavailable.",
                    )
                    return

                # 3. Create internal network (no external WAN gateway)
                await self.docker_executor.create_internal_network(network_name)

                # 4. Start application container (no published host ports)
                await self.docker_executor.start_application_container(
                    container_name=container_name,
                    network_name=network_name,
                    workspace_dir=temp_dir,
                    manifest=manifest,
                    limits=limits,
                )

                # 5. Poll health endpoint
                healthy, health_msg = await self.docker_executor.poll_health(
                    container_name=container_name,
                    port=manifest.application_port,
                    path=manifest.health_check_path,
                    method=manifest.health_check_method,
                    timeout_seconds=limits.startup_timeout_seconds,
                    interval_seconds=limits.health_poll_interval_seconds,
                )

                stdout, stderr, is_truncated = await self.docker_executor.get_container_logs(container_name)

                if not healthy:
                    yield RuntimeSessionResult(
                        runtime_id=session_id,
                        project_id=project_id,
                        version_id=version_id,
                        status=RuntimeStatus.STARTUP_FAILED,
                        internal_url=internal_url,
                        container_name=container_name,
                        network_name=network_name,
                        started_at=started_at,
                        stopped_at=datetime.now(timezone.utc),
                        duration_seconds=round(time.monotonic() - start_time, 3),
                        health_status=health_msg,
                        stdout_summary=stdout,
                        stderr_summary=stderr,
                        is_truncated=is_truncated,
                        failure_reason=health_msg,
                    )
                    return

                # Healthy & Ready
                ready_at = datetime.now(timezone.utc)
                yield RuntimeSessionResult(
                    runtime_id=session_id,
                    project_id=project_id,
                    version_id=version_id,
                    status=RuntimeStatus.READY,
                    internal_url=internal_url,
                    container_name=container_name,
                    network_name=network_name,
                    started_at=started_at,
                    ready_at=ready_at,
                    duration_seconds=round(time.monotonic() - start_time, 3),
                    health_status=health_msg,
                    stdout_summary=stdout,
                    stderr_summary=stderr,
                    is_truncated=is_truncated,
                    metadata={
                        "entrypoint": manifest.entrypoint,
                        "application_port": manifest.application_port,
                        "health_check_path": manifest.health_check_path,
                    },
                )

            finally:
                # Guaranteed cleanup in strict reverse order
                try:
                    await self.docker_executor.stop_and_remove_container(container_name)
                except Exception as exc:
                    logger.warning(f"Error stopping container '{container_name}': {exc}")

                try:
                    await self.docker_executor.remove_network(network_name)
                except Exception as exc:
                    logger.warning(f"Error removing network '{network_name}': {exc}")

                try:
                    shutil.rmtree(temp_dir, ignore_errors=True)
                except Exception as exc:
                    logger.warning(f"Error removing temp workspace '{temp_dir}': {exc}")

        finally:
            if acquired:
                semaphore.release()

    async def execute_runtime_validation(
        self,
        project_id: uuid.UUID,
        version_id: uuid.UUID,
        limits: RuntimeLimits | None = None,
    ) -> RuntimeSessionResult:
        """Resolve version, start isolated runtime, probe readiness health, and teardown."""
        files_map, manifest = await self.resolve_version_files_and_manifest(project_id, version_id)
        async with self.managed_runtime_session(
            project_id=project_id,
            files_map=files_map,
            manifest=manifest,
            version_id=version_id,
            limits=limits,
        ) as session_result:
            return session_result
