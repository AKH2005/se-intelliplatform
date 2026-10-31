"""Unit and regression tests for AI refinement synchronization, WAL consistency, and failure recovery."""

import uuid
from unittest.mock import AsyncMock, MagicMock, patch
import pytest

from app.core.exceptions import ConflictError, ValidationError
from app.models.development_version import DevelopmentVersion, DevelopmentVersionStatus
from app.models.project import Project, ProjectStatus
from app.services.engineering_action_service import EngineeringActionService


@pytest.fixture
def mock_db():
    db = AsyncMock()
    return db


@pytest.fixture
def sample_project():
    return Project(
        id=uuid.uuid4(),
        name="Task Manager Pro",
        slug="task-manager-pro",
        status=ProjectStatus.IN_PROGRESS,
        settings={"active_version_id": None},
    )


@pytest.fixture
def sample_v1(sample_project):
    v_id = uuid.uuid4()
    sample_project.settings["active_version_id"] = str(v_id)
    return DevelopmentVersion(
        id=v_id,
        project_id=sample_project.id,
        version_number=1,
        status=DevelopmentVersionStatus.VERIFIED,
        files_manifest=[
            {"path": "app/main.py", "size_bytes": 45, "language": "python", "content": "def run():\n    return 'v1'\n"},
            {"path": "index.html", "size_bytes": 100, "language": "html", "content": "<h1>TaskFlow</h1>"},
        ],
        file_count=2,
        total_size_bytes=145,
        content_hash="content-hash-v1",
        manifest_hash="manifest-hash-v1",
        requirement_ids=[],
    )


def make_service(session, version_svc=None):
    if version_svc is None:
        version_svc = MagicMock()
        version_svc.sanitize_file_path = lambda p: p.replace("\\", "/").strip().lstrip("/")
        version_svc.compute_content_hash = lambda files: "new-content-hash"
        version_svc.compute_manifest_hash = lambda files: "new-manifest-hash"
    return EngineeringActionService(
        session=session,
        version_service=version_svc,
        verification_service=MagicMock(),
        requirement_service=MagicMock(),
        context_engine=MagicMock(),
        workflow_service=MagicMock(),
    )


@pytest.mark.asyncio
async def test_successful_refinement_synchronization(mock_db, sample_project, sample_v1):
    """Verify successful refinement creates immutable v2, commits DB state before preview refresh, and updates files."""
    version_svc = MagicMock()
    version_svc.sanitize_file_path = lambda p: p.replace("\\", "/").strip().lstrip("/")
    version_svc.compute_content_hash = lambda files: "content-hash-v2"
    version_svc.compute_manifest_hash = lambda files: "manifest-hash-v2"
    version_svc.get_active_version = AsyncMock(return_value=sample_v1)
    version_svc._resolve_project = AsyncMock(return_value=sample_project)
    version_svc._resolve_version_files_map = AsyncMock(return_value={
        "app/main.py": "def run():\n    return 'v1'\n",
        "index.html": "<h1>TaskFlow</h1>",
    })

    # Mock DB query executions
    async def mock_execute(stmt):
        m_res = MagicMock()
        # active_orm query
        m_res.scalar_one_or_none.return_value = sample_v1
        # max version query
        m_scalars = MagicMock()
        m_scalars.first.return_value = 1
        m_res.scalars.return_value = m_scalars
        return m_res

    mock_db.execute = AsyncMock(side_effect=mock_execute)
    mock_db.commit = AsyncMock()
    mock_db.refresh = AsyncMock()

    service = make_service(mock_db, version_svc)

    with patch("app.runtime.preview_runtime_manager.preview_runtime_manager.materialize_project_files") as mock_materialize, \
         patch("app.runtime.preview_runtime_manager.preview_runtime_manager.restart_runtime", new_callable=AsyncMock) as mock_restart:
        mock_restart.return_value = (True, "Runtime updated and verified.", {"status": "RUNNING"})

        params = {
            "version_id": str(sample_v1.id),
            "reason": "Refinement: Add dark mode toggle to navigation",
            "changes": [
                {"file_path": "index.html", "content": "<h1>TaskFlow</h1><button id=\"btn-theme-toggle\">Toggle</button>"}
            ],
        }

        result, msg = await service._dispatch_action(
            project_id=sample_project.id,
            action_id="APPLY_CODE_CHANGE",
            parameters=params,
            target_id=None,
            user_id="qa_user",
        )

        assert result["version_number"] == 2
        assert result["runtime_updated"] is True
        assert "Synthesized immutable version v2" in msg

        # Database state updated
        assert sample_v1.status == DevelopmentVersionStatus.SUPERSEDED
        assert sample_project.settings["active_version_id"] == result["version_id"]

        # Materialization was called with updated files containing dark mode
        mock_materialize.assert_called_once()
        written_files = mock_materialize.call_args[0][1]
        assert "btn-theme-toggle" in written_files["index.html"]

        # Runtime restart called with project context
        mock_restart.assert_called_once_with(
            project_id=str(sample_project.id),
            project_name=sample_project.name,
            project_description=sample_project.description,
        )

        # Database commit occurred
        assert mock_db.commit.call_count >= 1


@pytest.mark.asyncio
async def test_concurrent_refinement_version_conflict(mock_db, sample_project, sample_v1):
    """Verify that a refinement prepared against a stale version is rejected with ConflictError."""
    # Active version has already advanced to v2
    v2_id = uuid.uuid4()
    sample_v2 = DevelopmentVersion(
        id=v2_id,
        project_id=sample_project.id,
        version_number=2,
        status=DevelopmentVersionStatus.VERIFIED,
    )

    version_svc = MagicMock()
    version_svc.get_active_version = AsyncMock(return_value=sample_v2)
    service = make_service(mock_db, version_svc)

    # Edit prepared against stale v1
    params = {
        "version_id": str(sample_v1.id),
        "reason": "Concurrent edit prepared against v1",
        "changes": [{"file_path": "app/main.py", "content": "def run(): return 'concurrent'\n"}],
    }

    with pytest.raises(ConflictError) as exc_info:
        await service._dispatch_action(
            project_id=sample_project.id,
            action_id="APPLY_CODE_CHANGE",
            parameters=params,
            target_id=None,
            user_id="qa_user",
        )

    assert "Version conflict" in str(exc_info.value)
    assert "active version is v2" in str(exc_info.value)


@pytest.mark.asyncio
async def test_refinement_runtime_failure_recovery(mock_db, sample_project, sample_v1):
    """Verify that if preview runtime restart fails, files and active version are safely restored to last known-good state."""
    version_svc = MagicMock()
    version_svc.sanitize_file_path = lambda p: p.replace("\\", "/").strip().lstrip("/")
    version_svc.compute_content_hash = lambda files: "content-hash-v2"
    version_svc.compute_manifest_hash = lambda files: "manifest-hash-v2"
    version_svc.get_active_version = AsyncMock(return_value=sample_v1)
    version_svc._resolve_project = AsyncMock(return_value=sample_project)
    original_files = {
        "app/main.py": "def run():\n    return 'v1'\n",
        "index.html": "<h1>TaskFlow</h1>",
    }
    version_svc._resolve_version_files_map = AsyncMock(return_value=original_files)

    async def mock_execute(stmt):
        m_res = MagicMock()
        m_res.scalar_one_or_none.return_value = sample_v1
        m_scalars = MagicMock()
        m_scalars.first.return_value = 1
        m_res.scalars.return_value = m_scalars
        return m_res

    mock_db.execute = AsyncMock(side_effect=mock_execute)
    mock_db.commit = AsyncMock()
    mock_db.refresh = AsyncMock()

    service = make_service(mock_db, version_svc)

    with patch("app.runtime.preview_runtime_manager.preview_runtime_manager.materialize_project_files") as mock_materialize, \
         patch("app.runtime.preview_runtime_manager.preview_runtime_manager.restart_runtime", new_callable=AsyncMock) as mock_restart:
        # First restart fails (simulating runtime crash on edit)
        mock_restart.side_effect = [
            (False, "Port 8001 startup timeout or syntax crash.", {}),
            (True, "Restored baseline runtime.", {}),
        ]

        params = {
            "version_id": str(sample_v1.id),
            "reason": "Refinement that causes runtime crash",
            "changes": [
                {"file_path": "index.html", "content": "<div><h1>Test Runtime Failure</h1></div>"}
            ],
        }

        result, msg = await service._dispatch_action(
            project_id=sample_project.id,
            action_id="APPLY_CODE_CHANGE",
            parameters=params,
            target_id=None,
            user_id="qa_user",
        )

        assert result["runtime_updated"] is False
        assert "Changes were reverted" in msg

        # Materialization was called twice: once for changes, and once to restore original files
        assert mock_materialize.call_count == 2
        restored_files = mock_materialize.call_args_list[1][0][1]
        assert restored_files == original_files

        # Active pointer in DB settings was rolled back to sample_v1
        assert sample_project.settings["active_version_id"] == str(sample_v1.id)
        assert sample_v1.status == DevelopmentVersionStatus.VERIFIED

