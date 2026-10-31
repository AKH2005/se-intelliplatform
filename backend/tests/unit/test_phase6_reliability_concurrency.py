"""Unit tests for Phase 6: Multi-Operation Reliability, Concurrency & Live Preview Protection.

Verifies:
1. Duplicate build requests rejected with HTTP 409 Conflict.
2. Build failure cleanly releases lock so subsequent builds can execute.
3. Stale refinement edits submitted against outdated versions rejected with HTTP 409 Conflict.
4. Reused confirmation tokens rejected with HTTP 409 Conflict (anti-replay).
5. Confirmation after version changed/rolled back rejected with HTTP 409 Conflict.
6. Unauthorized and unauthenticated version access rejected with HTTP 403 Forbidden / 401 Unauthorized.
7. Failed runtime update restores last known-good files to preserve live preview.
"""

import asyncio
from datetime import datetime, timedelta, timezone
import uuid
from unittest.mock import AsyncMock, MagicMock, patch
import pytest

from app.core.exceptions import ConflictError, ForbiddenError, NotFoundError, UnauthorizedError
from app.models.assistant import ActionConfirmationToken
from app.models.development_version import DevelopmentVersion, DevelopmentVersionStatus
from app.models.project import Project, ProjectStatus
from app.models.user import User
from app.models.workflow_execution import WorkflowExecution
from app.schemas.assistant import ActionResult, ActionStatus
from app.schemas.context import ProjectContextResponse, RequirementStatistics
from app.schemas.project import ProjectResponse
from app.schemas.workflow import WorkflowExecuteRequest
from app.services.action_registry import get_action_definition
from app.services.engineering_action_service import EngineeringActionService
from app.services.workflow_service import WorkflowService
from app.workflows.contracts import WorkflowResult, WorkflowStatus
from app.api.v1.endpoints.development_versions import (
    activate_development_version,
    rollback_development_version,
    _resolve_project as resolve_version_project,
)


@pytest.fixture
def mock_db():
    db = AsyncMock()
    return db


@pytest.fixture
def sample_project():
    return Project(
        id=uuid.uuid4(),
        name="TaskMaster Pro",
        slug="taskmaster-pro",
        status=ProjectStatus.IN_PROGRESS,
        owner_id=uuid.uuid4(),
        settings={},
    )


@pytest.fixture
def sample_v1_version(sample_project):
    return DevelopmentVersion(
        id=uuid.uuid4(),
        project_id=sample_project.id,
        version_number=1,
        status=DevelopmentVersionStatus.VERIFIED,
        files_manifest=[
            {"path": "app/main.py", "size_bytes": 30, "language": "python"},
            {"path": "README.md", "size_bytes": 16, "language": "markdown"},
        ],
        file_count=2,
        total_size_bytes=46,
        content_hash="hash-v1",
        manifest_hash="mhash-v1",
    )


@pytest.fixture
def sample_v2_version(sample_project, sample_v1_version):
    return DevelopmentVersion(
        id=uuid.uuid4(),
        project_id=sample_project.id,
        version_number=2,
        parent_version_id=sample_v1_version.id,
        status=DevelopmentVersionStatus.VERIFIED,
        files_manifest=[
            {"path": "app/main.py", "size_bytes": 45, "language": "python"},
            {"path": "README.md", "size_bytes": 16, "language": "markdown"},
        ],
        file_count=2,
        total_size_bytes=61,
        content_hash="hash-v2",
        manifest_hash="mhash-v2",
    )


def make_action_service(mock_db, version_svc=None):
    if version_svc is None:
        version_svc = MagicMock()
        version_svc.sanitize_file_path = lambda p: p.replace("\\", "/").strip().lstrip("/")
        version_svc.get_active_version = AsyncMock(return_value=None)
        version_svc.get_version = AsyncMock(return_value=None)
        version_svc._resolve_version_files_map = AsyncMock(return_value={})
    return EngineeringActionService(
        session=mock_db,
        version_service=version_svc,
        verification_service=MagicMock(),
        requirement_service=MagicMock(),
        context_engine=MagicMock(),
        workflow_service=MagicMock(),
    )


# ==============================================================================
# 1. Duplicate Build Prevention & Lock Release
# ==============================================================================

@pytest.mark.asyncio
async def test_duplicate_build_prevention_raises_conflict_409(mock_db, sample_project):
    """Avoid starting multiple builds for the same project simultaneously."""
    context_engine = MagicMock()
    context_engine._get_project = AsyncMock(return_value=sample_project)
    coordinator = MagicMock()

    # Clear active locks
    WorkflowService._active_project_builds.clear()

    # Simulate an active build already running
    WorkflowService._active_project_builds.add(sample_project.id)

    service = WorkflowService(
        session=mock_db,
        context_engine=context_engine,
        coordinator=coordinator,
    )

    request = WorkflowExecuteRequest(project_id=sample_project.id)

    with pytest.raises(ConflictError) as exc_info:
        await service.execute_workflow("software-design-workflow", request)

    err = str(exc_info.value)
    assert "build is already in progress" in err.lower()
    assert sample_project.name in err

    # Cleanup
    WorkflowService._active_project_builds.clear()


def make_project_context(project: Project) -> ProjectContextResponse:
    return ProjectContextResponse(
        project=ProjectResponse(
            id=project.id,
            name=project.name,
            slug=project.slug,
            description="Test project description",
            status="IN_PROGRESS",
            owner_id=project.owner_id,
            settings=project.settings or {},
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        ),
        requirements=[],
        architecture_components=[],
        database_schemas=[],
        source_files=[],
        test_suites=[],
        deployment_pipelines=[],
        statistics=RequirementStatistics(
            total_requirements=0,
            active_requirements=0,
            functional_count=0,
            non_functional_count=0,
            constraint_count=0,
            completion_percentage=0.0,
        ),
        context_version=1,
        generated_at=datetime.now(timezone.utc),
    )


@pytest.mark.asyncio
async def test_build_failure_releases_lock_and_allows_subsequent_build(mock_db, sample_project):
    """Ensure failed builds release their locks in finally block."""
    context_engine = MagicMock()
    context_engine._get_project = AsyncMock(return_value=sample_project)
    context_engine.generate_context = AsyncMock(return_value=make_project_context(sample_project))

    # Coordinator raises an error during first build
    coordinator = MagicMock()
    coordinator.execute = AsyncMock(side_effect=RuntimeError("Docker daemon crashed"))

    WorkflowService._active_project_builds.clear()

    service = WorkflowService(
        session=mock_db,
        context_engine=context_engine,
        coordinator=coordinator,
    )

    # Mock DB query for existing running builds returning None
    exec_res = MagicMock()
    exec_res.scalars.return_value.first.return_value = None
    exec_res.scalars.return_value.all.return_value = []
    mock_db.execute = AsyncMock(return_value=exec_res)

    request = WorkflowExecuteRequest(project_id=sample_project.id)

    # First build fails with RuntimeError
    with pytest.raises(RuntimeError):
        await service.execute_workflow("software-design-workflow", request)

    # Crucial assertion: Lock MUST have been released despite the failure
    assert sample_project.id not in WorkflowService._active_project_builds

    # Second build can now execute without getting ConflictError
    mock_result = WorkflowResult(
        workflow_execution_id=uuid.uuid4(),
        workflow_id="software-design-workflow",
        workflow_version="1.0.0",
        status=WorkflowStatus.COMPLETED,
        started_at=datetime.now(timezone.utc),
        completed_at=datetime.now(timezone.utc),
        step_results=[],
        artifacts={},
    )
    coordinator.execute = AsyncMock(return_value=mock_result)

    result = await service.execute_workflow("software-design-workflow", request)
    assert result.status == WorkflowStatus.COMPLETED
    assert sample_project.id not in WorkflowService._active_project_builds


# ==============================================================================
# 2. Version Concurrency: Stale Edit Rejection (HTTP 409)
# ==============================================================================

@pytest.mark.asyncio
async def test_stale_refinement_edit_raises_conflict_409(mock_db, sample_project, sample_v1_version, sample_v2_version):
    """Reject edits prepared against stale version when active version has moved."""
    sample_project.settings = {"active_version_id": str(sample_v2_version.id)}

    version_svc = MagicMock()
    # Active version is v2
    version_svc.get_active_version = AsyncMock(return_value=sample_v2_version)
    version_svc.get_version = AsyncMock(return_value=sample_v1_version)

    service = make_action_service(mock_db, version_svc=version_svc)

    # When resolve_version_reference runs:
    # 1. select DevelopmentVersion -> sample_v1_version
    # 2. select Project -> sample_project (active_version_id is v2)
    # 3. select DevelopmentVersion.version_number -> 2
    mock_db.execute.return_value.scalar_one_or_none.side_effect = [
        sample_v1_version,
        sample_project,
        sample_v2_version.version_number,
    ]

    # Client submits an edit against v1 (stale!)
    params = {
        "version_id": str(sample_v1_version.id),
        "reason": "Add dark mode toggle to stale v1",
        "changes": [{"file_path": "app/main.py", "content": "print('dark mode')\n"}],
    }

    with pytest.raises(ConflictError) as exc_info:
        await service.execute_action(
            project_id=sample_project.id,
            action_id="APPLY_CODE_CHANGE",
            parameters=params,
            conversation_id=uuid.uuid4(),
        )

    err = str(exc_info.value)
    assert "the project has changed since this edit was prepared" in err.lower()
    assert "active version is v2" in err.lower()
    assert "refresh before retrying" in err.lower()


# ==============================================================================
# 3. Confirmation Token Anti-Replay & Rollback Invalidation (HTTP 409)
# ==============================================================================

@pytest.mark.asyncio
async def test_confirmation_token_reuse_rejected_with_409(mock_db, sample_project):
    """Reused confirmation tokens must be rejected with 409 Conflict."""
    service = make_action_service(mock_db)

    # Token was already consumed 5 seconds ago
    consumed_token = ActionConfirmationToken(
        token_id=uuid.uuid4(),
        token_hash="already-used-token-secret-123",
        project_id=sample_project.id,
        conversation_id=uuid.uuid4(),
        action_id="APPLY_CODE_CHANGE",
        parameters_payload={"version_id": str(uuid.uuid4()), "reason": "Test", "changes": []},
        expires_at=datetime.now(timezone.utc) + timedelta(minutes=10),
        consumed_at=datetime.now(timezone.utc) - timedelta(seconds=5),
    )

    mock_db.execute.return_value.scalar_one_or_none.return_value = consumed_token

    with pytest.raises(ConflictError) as exc_info:
        await service.confirm_action(
            project_id=sample_project.id,
            confirmation_token="already-used-token-secret-123",
            user_id="user-123",
        )

    err = str(exc_info.value)
    assert "already been consumed" in err.lower()
    assert "replay prevented" in err.lower()


@pytest.mark.asyncio
async def test_confirmation_after_rollback_or_version_advance_rejected_with_409(
    mock_db, sample_project, sample_v1_version, sample_v2_version
):
    """If project rolled back or changed between proposal and confirmation, reject token redemption."""
    version_svc = MagicMock()
    # Active version is now v2 (or rolled back to another version)
    version_svc.get_active_version = AsyncMock(return_value=sample_v2_version)

    service = make_action_service(mock_db, version_svc=version_svc)

    # Token was created against v1
    token_for_v1 = ActionConfirmationToken(
        token_id=uuid.uuid4(),
        token_hash="token-issued-against-v1",
        project_id=sample_project.id,
        conversation_id=uuid.uuid4(),
        action_id="APPLY_CODE_CHANGE",
        parameters_payload={"version_id": str(sample_v1_version.id), "reason": "Test", "changes": []},
        expires_at=datetime.now(timezone.utc) + timedelta(minutes=10),
        consumed_at=None,
    )

    mock_db.execute.return_value.scalar_one_or_none.side_effect = [
        token_for_v1,                      # find token
        sample_v1_version.version_number,  # find stale version_number
    ]

    with pytest.raises(ConflictError) as exc_info:
        await service.confirm_action(
            project_id=sample_project.id,
            confirmation_token="token-issued-against-v1",
            user_id="user-123",
        )

    err = str(exc_info.value)
    assert "the project has changed since this edit was prepared" in err.lower()
    assert "active version is v2" in err.lower()
    assert "refresh before retrying" in err.lower()


# ==============================================================================
# 4. Security & Project Ownership Authorization (403 Forbidden / 401 Unauthorized)
# ==============================================================================

@pytest.mark.asyncio
async def test_unauthorized_project_access_rejected_with_403_and_401(mock_db, sample_project):
    """Verify project ownership and reject unauthorized access."""
    owner_user = User(id=sample_project.owner_id, email="owner@example.com")
    intruder_user = User(id=uuid.uuid4(), email="intruder@example.com")

    # Mock DB returning sample_project
    mock_db.execute.return_value.scalar_one_or_none.return_value = sample_project

    # 1. Unauthenticated request -> UnauthorizedError (401)
    with pytest.raises(UnauthorizedError) as unauth_err:
        await resolve_version_project(sample_project.id, mock_db, current_user=None)
    assert "authentication required" in str(unauth_err.value).lower()

    # 2. Intruder user request -> ForbiddenError (403)
    with pytest.raises(ForbiddenError) as forb_err:
        await resolve_version_project(sample_project.id, mock_db, current_user=intruder_user)
    assert "do not have permission" in str(forb_err.value).lower()

    # 3. Legitimate owner request -> succeeds
    resolved = await resolve_version_project(sample_project.id, mock_db, current_user=owner_user)
    assert resolved.id == sample_project.id


# ==============================================================================
# 5. Live Preview Protection: Last Known-Good Preservation
# ==============================================================================

@pytest.mark.asyncio
async def test_preview_resilience_preserves_last_known_good_on_restart_failure(
    mock_db, sample_project, sample_v1_version
):
    """If new changes fail during preview runtime restart, last known-good files are restored."""
    sample_project.settings = {"active_version_id": str(sample_v1_version.id)}
    version_svc = MagicMock()
    version_svc.get_active_version = AsyncMock(return_value=sample_v1_version)
    version_svc._resolve_project = AsyncMock(return_value=sample_project)
    v1_files = {"app/main.py": "def hello():\n    return 'v1'\n"}
    version_svc._resolve_version_files_map = AsyncMock(return_value=v1_files)
    version_svc.sanitize_file_path = lambda p: p
    version_svc.compute_content_hash = lambda files: "hash-new"
    version_svc.compute_manifest_hash = lambda files: "mhash-new"

    service = make_action_service(mock_db, version_svc=version_svc)

    # Mock DB scalar results
    mock_db.execute.return_value.scalar_one_or_none.return_value = sample_v1_version
    mock_db.execute.return_value.scalars.return_value.first.return_value = 1

    params = {
        "version_id": str(sample_v1_version.id),
        "reason": "Buggy new code",
        "changes": [{"file_path": "app/main.py", "content": "def hello():\n    return 'v2_fail'\n"}],
    }

    with patch("app.runtime.preview_runtime_manager.preview_runtime_manager") as mock_preview_mgr, \
         patch("app.runtime.docker_runtime_executor.DockerRuntimeExecutor.check_docker_available", return_value=False):
        
        # Simulate: first restart with new files FAILS, so it should restore v1_files!
        mock_preview_mgr.materialize_project_files = MagicMock()
        mock_preview_mgr.restart_runtime = AsyncMock(side_effect=[
            (False, "Container syntax failure on startup", {}),  # new files fail
            (True, "Last known-good restored", {}),             # restored files succeed
        ])

        result_data, summary = await service._dispatch_action(
            project_id=sample_project.id,
            action_id="APPLY_CODE_CHANGE",
            parameters=params,
            target_id=None,
            user_id="user-123",
        )

        # Verify that materialize_project_files was called with the old files to restore preview
        assert mock_preview_mgr.materialize_project_files.call_count >= 2
        last_materialized_files = mock_preview_mgr.materialize_project_files.call_args[0][1]
        # Must have restored the original v1_files!
        assert last_materialized_files == v1_files
