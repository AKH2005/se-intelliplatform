"""Comprehensive Unit Tests for ApplicationRuntimeManager and DockerRuntimeExecutor (Phase 11J - Stage 2)."""

import asyncio
import os
import uuid
from unittest.mock import AsyncMock, MagicMock, patch
import pytest
from pydantic import ValidationError

from app.core.exceptions import NotFoundError
from app.models.development_version import DevelopmentVersion
from app.models.workflow_execution import WorkflowExecution
from app.runtime.application_runtime_manager import ApplicationRuntimeManager
from app.runtime.contracts import (
    MAX_CONCURRENT_RUNTIMES,
    RuntimeLimits,
    RuntimeSessionResult,
    RuntimeStatus,
)
from app.runtime.docker_runtime_executor import DockerRuntimeExecutor
from app.runtime.errors import (
    DockerUnavailableError,
    RuntimeConfigurationError,
    RuntimeIsolationError,
    RuntimeStartupError,
)
from app.schemas.runtime import (
    ApplicationRuntimeManifest,
    create_default_fastapi_manifest,
)


# ==============================================================================
# Fixtures
# ==============================================================================

@pytest.fixture
def sample_project_id():
    return uuid.uuid4()


@pytest.fixture
def sample_version_id():
    return uuid.uuid4()


@pytest.fixture
def sample_workflow_id():
    return uuid.uuid4()


@pytest.fixture
def sample_files_map():
    return {
        "app/main.py": "from fastapi import FastAPI\napp = FastAPI()\n@app.get('/docs')\ndef docs(): return {'ok': True}",
        "requirements.txt": "fastapi>=0.110.0\n",
    }


@pytest.fixture
def sample_manifest():
    return create_default_fastapi_manifest(port=8000, health_path="/docs")


@pytest.fixture
def mock_docker_executor():
    executor = MagicMock(spec=DockerRuntimeExecutor)
    executor.image = "se-intelliplatform-sandbox:latest"
    executor.check_docker_available = AsyncMock(return_value=True)
    executor.create_internal_network = AsyncMock()
    executor.remove_network = AsyncMock()
    executor.start_application_container = AsyncMock()
    executor.poll_health = AsyncMock(return_value=(True, "Application healthy at '/docs'"))
    executor.get_container_logs = AsyncMock(return_value=("Startup complete", "", False))
    executor.stop_and_remove_container = AsyncMock()
    executor.get_container_status = AsyncMock(return_value=(True, 0))
    return executor


# ==============================================================================
# 1. Manifest and Version Resolution Tests
# ==============================================================================

class TestManifestAndVersionResolution:
    """Test resolution of DevelopmentVersion, WorkflowExecution artifacts, and runtime manifests."""

    @pytest.mark.asyncio
    async def test_resolve_valid_version_and_default_manifest(
        self, sample_project_id, sample_version_id, sample_workflow_id, sample_files_map
    ):
        mock_session = AsyncMock()

        version = DevelopmentVersion(
            id=sample_version_id,
            project_id=sample_project_id,
            version_number=1,
            workflow_execution_id=sample_workflow_id,
            artifact_key="code-generation",
            content_hash="abc",
            manifest_hash="def",
            metadata_payload={},
        )
        wf = WorkflowExecution(
            workflow_execution_id=sample_workflow_id,
            project_id=sample_project_id,
            artifacts={
                "code-generation": {
                    "generated_files": [
                        {"path": p, "content": c} for p, c in sample_files_map.items()
                    ]
                }
            },
        )

        # Mock query results
        res_ver = MagicMock()
        res_ver.scalar_one_or_none.return_value = version

        res_wf = MagicMock()
        res_wf.scalar_one_or_none.return_value = wf

        mock_session.execute.side_effect = [res_ver, res_wf]

        manager = ApplicationRuntimeManager(session=mock_session)
        files, manifest = await manager.resolve_version_files_and_manifest(
            sample_project_id, sample_version_id
        )

        assert "app/main.py" in files
        assert manifest.application_port == 8000
        assert manifest.health_check_path == "/docs"

    @pytest.mark.asyncio
    async def test_reject_cross_project_version(self, sample_project_id, sample_version_id):
        mock_session = AsyncMock()
        res_ver = MagicMock()
        res_ver.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = res_ver

        manager = ApplicationRuntimeManager(session=mock_session)
        with pytest.raises(NotFoundError):
            await manager.resolve_version_files_and_manifest(
                sample_project_id, sample_version_id
            )

    @pytest.mark.asyncio
    async def test_resolve_custom_manifest_from_metadata(
        self, sample_project_id, sample_version_id, sample_workflow_id, sample_files_map
    ):
        mock_session = AsyncMock()

        custom_manifest_dict = {
            "runtime_type": "docker",
            "language": "python",
            "framework": "fastapi",
            "entrypoint": "api.service:application",
            "startup_command": ["python", "-m", "uvicorn", "api.service:application", "--port", "9000"],
            "application_port": 9000,
            "health_check_path": "/healthz",
            "health_check_method": "GET",
            "health_check_timeout_seconds": 10.0,
        }

        version = DevelopmentVersion(
            id=sample_version_id,
            project_id=sample_project_id,
            version_number=2,
            workflow_execution_id=sample_workflow_id,
            artifact_key="code-generation",
            content_hash="abc",
            manifest_hash="def",
            metadata_payload={"runtime_manifest": custom_manifest_dict},
        )
        wf = WorkflowExecution(
            workflow_execution_id=sample_workflow_id,
            project_id=sample_project_id,
            artifacts={
                "code-generation": {
                    "generated_files": [
                        {"path": p, "content": c} for p, c in sample_files_map.items()
                    ]
                }
            },
        )

        res_ver = MagicMock()
        res_ver.scalar_one_or_none.return_value = version

        res_wf = MagicMock()
        res_wf.scalar_one_or_none.return_value = wf

        mock_session.execute.side_effect = [res_ver, res_wf]

        manager = ApplicationRuntimeManager(session=mock_session)
        files, manifest = await manager.resolve_version_files_and_manifest(
            sample_project_id, sample_version_id
        )

        assert manifest.application_port == 9000
        assert manifest.entrypoint == "api.service:application"
        assert manifest.health_check_path == "/healthz"


# ==============================================================================
# 2. Workspace Materialization & Isolation Tests
# ==============================================================================

class TestWorkspaceMaterialization:
    """Test safe file extraction and directory containment."""

    def test_materialize_valid_workspace(self, tmp_path, sample_files_map):
        manager = ApplicationRuntimeManager()
        manager.materialize_workspace(sample_files_map, str(tmp_path))

        assert (tmp_path / "app" / "main.py").exists()
        assert (tmp_path / "requirements.txt").exists()
        assert "FastAPI" in (tmp_path / "app" / "main.py").read_text(encoding="utf-8")

    @pytest.mark.parametrize("unsafe_path", [
        "../traversal.py",
        "/absolute/path.py",
        "\\absolute\\path.py",
        "C:\\Windows\\test.py",
        "D:test.py",
        "app/../../secret.py",
    ])
    def test_reject_unsafe_file_paths_in_artifact(self, tmp_path, unsafe_path):
        manager = ApplicationRuntimeManager()
        bad_map = {unsafe_path: "print('malicious')"}

        with pytest.raises(RuntimeIsolationError):
            manager.materialize_workspace(bad_map, str(tmp_path))


# ==============================================================================
# 3. Docker Configuration & Hardened Execution Tests
# ==============================================================================

class TestDockerRuntimeExecutorConfig:
    """Test Docker CLI argument construction and hardened security boundaries."""

    @pytest.mark.asyncio
    async def test_start_application_container_arguments(self, tmp_path, sample_manifest):
        executor = DockerRuntimeExecutor(image="test-app-image:latest")
        executor.check_docker_available = AsyncMock(return_value=True)

        limits = RuntimeLimits(
            memory_limit="512m",
            cpus=1.0,
            max_pids=64,
        )

        captured_cmd = []

        async def fake_subprocess_exec(*args, **kwargs):
            nonlocal captured_cmd
            captured_cmd = list(args)
            proc = MagicMock()
            proc.communicate = AsyncMock(return_value=(b"container-id-123", b""))
            proc.returncode = 0
            return proc

        with patch("asyncio.create_subprocess_exec", side_effect=fake_subprocess_exec):
            await executor.start_application_container(
                container_name="app-test-uuid",
                network_name="se_net_test",
                workspace_dir=str(tmp_path),
                manifest=sample_manifest,
                limits=limits,
            )

        cmd_str = " ".join(captured_cmd)

        # 1. No host port publishing (-p is forbidden)
        assert "-p" not in captured_cmd
        assert "--publish" not in captured_cmd

        # 2. Hardened container flags
        assert "--network" in captured_cmd and "se_net_test" in captured_cmd
        assert "--read-only" in captured_cmd
        assert "--cap-drop=ALL" in captured_cmd
        assert "--security-opt=no-new-privileges:true" in captured_cmd
        assert "--memory=512m" in captured_cmd
        assert "--cpus=1.0" in captured_cmd
        assert "--pids-limit=64" in captured_cmd
        assert "-u" in captured_cmd and "2000:2000" in captured_cmd

        # 3. Read-only workspace volume mount
        assert f"{os.path.abspath(str(tmp_path))}:/workspace:ro" in cmd_str

        # 4. No Docker socket mount
        assert "docker.sock" not in cmd_str

        # 5. Startup command tokens executed as argv (not sh -c)
        assert "sh" not in captured_cmd[0:15]
        assert captured_cmd[-len(sample_manifest.startup_command):] == sample_manifest.startup_command

    @pytest.mark.asyncio
    async def test_create_internal_network_arguments(self):
        executor = DockerRuntimeExecutor()
        executor.check_docker_available = AsyncMock(return_value=True)

        captured_cmd = []

        async def fake_subprocess_exec(*args, **kwargs):
            nonlocal captured_cmd
            captured_cmd = list(args)
            proc = MagicMock()
            proc.communicate = AsyncMock(return_value=(b"", b""))
            proc.returncode = 0
            return proc

        with patch("asyncio.create_subprocess_exec", side_effect=fake_subprocess_exec):
            await executor.create_internal_network("se_net_uuid123")

        assert captured_cmd == ["docker", "network", "create", "--internal", "se_net_uuid123"]


# ==============================================================================
# 4. Lifecycle, Health Check & Teardown Tests
# ==============================================================================

class TestApplicationRuntimeLifecycle:
    """Test full managed lifecycle: boot -> health check -> teardown."""

    @pytest.mark.asyncio
    async def test_successful_runtime_lifecycle(
        self, sample_project_id, sample_version_id, sample_files_map, sample_manifest, mock_docker_executor
    ):
        manager = ApplicationRuntimeManager(docker_executor=mock_docker_executor)

        async with manager.managed_runtime_session(
            project_id=sample_project_id,
            files_map=sample_files_map,
            manifest=sample_manifest,
            version_id=sample_version_id,
        ) as result:
            assert result.status == RuntimeStatus.READY
            assert result.project_id == sample_project_id
            assert result.version_id == sample_version_id
            assert result.internal_url == "http://" + result.container_name + ":8000"
            assert "healthy" in (result.health_status or "").lower()

        # Verify deterministic cleanup called
        mock_docker_executor.stop_and_remove_container.assert_called_once()
        mock_docker_executor.remove_network.assert_called_once()

    @pytest.mark.asyncio
    async def test_health_check_failure_triggers_cleanup(
        self, sample_project_id, sample_version_id, sample_files_map, sample_manifest, mock_docker_executor
    ):
        # Health check fails
        mock_docker_executor.poll_health = AsyncMock(
            return_value=(False, "Health check timed out after 15s")
        )
        mock_docker_executor.get_container_logs = AsyncMock(
            return_value=("Starting uvicorn", "Error: Address already in use", False)
        )

        manager = ApplicationRuntimeManager(docker_executor=mock_docker_executor)

        async with manager.managed_runtime_session(
            project_id=sample_project_id,
            files_map=sample_files_map,
            manifest=sample_manifest,
            version_id=sample_version_id,
        ) as result:
            assert result.status == RuntimeStatus.STARTUP_FAILED
            assert "Health check timed out" in (result.failure_reason or "")
            assert "Address already in use" in result.stderr_summary

        # Teardown must still be invoked
        mock_docker_executor.stop_and_remove_container.assert_called_once()
        mock_docker_executor.remove_network.assert_called_once()

    @pytest.mark.asyncio
    async def test_docker_unavailable_fails_safely(
        self, sample_project_id, sample_version_id, sample_files_map, sample_manifest, mock_docker_executor
    ):
        mock_docker_executor.check_docker_available = AsyncMock(return_value=False)

        manager = ApplicationRuntimeManager(docker_executor=mock_docker_executor)

        async with manager.managed_runtime_session(
            project_id=sample_project_id,
            files_map=sample_files_map,
            manifest=sample_manifest,
            version_id=sample_version_id,
        ) as result:
            assert result.status == RuntimeStatus.RUNTIME_ERROR
            assert "Docker daemon is unavailable" in (result.failure_reason or "")


# ==============================================================================
# 5. Concurrency Semaphore Tests
# ==============================================================================

class TestRuntimeConcurrencyGovernance:
    """Test concurrency throttling and resource limit enforcement."""

    @pytest.mark.asyncio
    async def test_concurrency_limit_enforced_at_max_runtimes(
        self, sample_project_id, sample_files_map, sample_manifest, mock_docker_executor
    ):
        manager = ApplicationRuntimeManager(docker_executor=mock_docker_executor, max_concurrent=2)

        # Acquire 2 slots simultaneously
        async with manager.managed_runtime_session(
            project_id=sample_project_id,
            files_map=sample_files_map,
            manifest=sample_manifest,
        ) as r1:
            assert r1.status == RuntimeStatus.READY

            async with manager.managed_runtime_session(
                project_id=sample_project_id,
                files_map=sample_files_map,
                manifest=sample_manifest,
            ) as r2:
                assert r2.status == RuntimeStatus.READY

                # 3rd concurrent request must be rejected with RESOURCE_LIMIT
                async with manager.managed_runtime_session(
                    project_id=sample_project_id,
                    files_map=sample_files_map,
                    manifest=sample_manifest,
                ) as r3:
                    assert r3.status == RuntimeStatus.RESOURCE_LIMIT
                    assert "Maximum concurrent application runtime sessions" in (r3.resource_limit_reason or "")

        # After releasing, a new session can acquire slot
        async with manager.managed_runtime_session(
            project_id=sample_project_id,
            files_map=sample_files_map,
            manifest=sample_manifest,
        ) as r4:
            assert r4.status == RuntimeStatus.READY
