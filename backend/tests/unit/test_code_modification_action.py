"""Unit tests for the safe code modification vertical slice and transient provider retries."""

import uuid
from unittest.mock import AsyncMock, MagicMock, patch
import pytest

from app.agents.exceptions import TransientProviderError
from app.core.exceptions import ConflictError, ValidationError
from app.models.development_version import DevelopmentVersion, DevelopmentVersionStatus
from app.models.project import Project, ProjectStatus
from app.schemas.assistant import (
    AssistantActionCandidate,
    ActionConfirmationTokenPayload,
    ActionResult,
    ActionStatus,
    ApplyCodeChangeParams,
    FileChangeItem,
    AssistantContext,
    AssistantResponseSchema,
)
from app.services.action_registry import get_action_definition, validate_action_parameters
from app.services.assistant_reasoning_service import AssistantReasoningService
from app.services.engineering_action_service import EngineeringActionService


@pytest.fixture
def mock_db():
    db = AsyncMock()
    return db


@pytest.fixture
def sample_project():
    return Project(
        id=uuid.uuid4(),
        name="Test Task Manager",
        slug="test-task-manager",
        status=ProjectStatus.IN_PROGRESS,
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


def make_action_service(session, version_svc=None):
    if version_svc is None:
        version_svc = MagicMock()
        version_svc.sanitize_file_path = lambda p: p.replace("\\", "/").strip().lstrip("/")
        version_svc.get_active_version = AsyncMock(return_value=None)
        version_svc.get_version = AsyncMock(return_value=None)
        version_svc._resolve_version_files_map = AsyncMock(return_value={})
    return EngineeringActionService(
        session=session,
        version_service=version_svc,
        verification_service=MagicMock(),
        requirement_service=MagicMock(),
        context_engine=MagicMock(),
        workflow_service=MagicMock(),
    )


def test_apply_code_change_registry_definition():
    """Verify APPLY_CODE_CHANGE is registered with confirmation and parameter schema."""
    action_def = get_action_definition("APPLY_CODE_CHANGE")
    assert action_def.action_id == "APPLY_CODE_CHANGE"
    assert action_def.requires_confirmation is True
    assert action_def.parameter_schema == ApplyCodeChangeParams

    # Valid params
    valid_params = {
        "version_id": str(uuid.uuid4()),
        "reason": "Update main.py to say v2",
        "changes": [{"file_path": "app/main.py", "content": "def hello():\n    return 'v2'\n"}],
    }
    validated = validate_action_parameters("APPLY_CODE_CHANGE", valid_params)
    assert validated.reason == "Update main.py to say v2"
    assert len(validated.changes) == 1


def test_apply_code_change_path_traversal_rejected():
    """Verify paths containing traversal or invalid characters are rejected."""
    with pytest.raises(ValidationError):
        validate_action_parameters("APPLY_CODE_CHANGE", {
            "version_id": str(uuid.uuid4()),
            "reason": "Malicious write",
            "changes": [{"file_path": "../../../etc/passwd", "content": "bad"}],
        })

    with pytest.raises(ValidationError):
        validate_action_parameters("APPLY_CODE_CHANGE", {
            "version_id": str(uuid.uuid4()),
            "reason": "Absolute path write",
            "changes": [{"file_path": "C:\\Windows\\System32\\cmd.exe", "content": "bad"}],
        })


@pytest.mark.asyncio
async def test_apply_code_change_diff_generation_and_token_issuance(mock_db, sample_project, sample_v1_version):
    """Verify execute_action returns PENDING_CONFIRMATION with real unified diffs."""
    version_svc = MagicMock()
    version_svc.get_version = AsyncMock(return_value=MagicMock(version_id=sample_v1_version.id, version_number=1))
    version_svc._resolve_version_files_map = AsyncMock(return_value={
        "app/main.py": "def hello():\n    return 'v1'\n",
        "README.md": "# Test Project\n",
    })
    service = make_action_service(mock_db, version_svc=version_svc)

    # Mock finding version in DB
    mock_db.execute.return_value.scalars.return_value.first.return_value = sample_v1_version
    mock_db.execute.return_value.scalar_one_or_none.return_value = sample_v1_version

    candidate = AssistantActionCandidate(
        action_id="APPLY_CODE_CHANGE",
        parameters={
            "version_id": str(sample_v1_version.id),
            "reason": "Upgrade greeting to v2",
            "changes": [
                {
                    "file_path": "app/main.py",
                    "content": "def hello():\n    return 'v2'\n",
                },
                {
                    "file_path": "app/utils.py",
                    "content": "def util():\n    pass\n",
                },
            ],
        },
    )

    conv_id = uuid.uuid4()
    with patch.object(service, "_authorize_target", new_callable=AsyncMock):
        result = await service.execute_action(
            project_id=sample_project.id,
            action_id=candidate.action_id,
            parameters=candidate.parameters,
            conversation_id=conv_id,
            user_id=str(uuid.uuid4()),
        )

    assert result.status == ActionStatus.PENDING_CONFIRMATION
    assert result.requires_confirmation is True
    assert result.confirmation_token is not None

    # Check that diffs were generated
    files = result.data.get("files", [])
    assert len(files) == 2

    # Modified file diff
    main_file = next(f for f in files if f["path"] == "app/main.py")
    assert main_file["status"] == "modified"
    assert "--- a/app/main.py" in main_file["diff"]
    assert "+++ b/app/main.py" in main_file["diff"]
    assert "-    return 'v1'" in main_file["diff"]
    assert "+    return 'v2'" in main_file["diff"]

    # Added file diff
    utils_file = next(f for f in files if f["path"] == "app/utils.py")
    assert utils_file["status"] == "added"
    assert "+def util():" in utils_file["diff"]


@pytest.mark.asyncio
async def test_confirm_apply_code_change_success(mock_db, sample_project, sample_v1_version):
    """Verify dispatch of APPLY_CODE_CHANGE creates a new immutable version and supersedes the old one."""
    active_resp = MagicMock(version_id=sample_v1_version.id, version_number=1)

    version_svc = MagicMock()
    version_svc.sanitize_file_path = lambda p: p.replace("\\", "/").strip().lstrip("/")
    version_svc.get_active_version = AsyncMock(return_value=active_resp)
    version_svc._resolve_version_files_map = AsyncMock(return_value={
        "app/main.py": "def hello():\n    return 'v1'\n",
        "README.md": "# Test Project\n",
    })
    version_svc._resolve_project = AsyncMock(return_value=sample_project)

    service = make_action_service(mock_db, version_svc=version_svc)

    mock_res = MagicMock()
    mock_res.scalar_one_or_none.return_value = sample_v1_version
    mock_res.scalars.return_value.first.return_value = 1
    mock_db.execute = AsyncMock(return_value=mock_res)
    mock_db.commit = AsyncMock()
    mock_db.refresh = AsyncMock()
    mock_db.add = MagicMock()

    params = {
        "version_id": str(sample_v1_version.id),
        "reason": "Upgrade greeting to v2",
        "changes": [
            {
                "file_path": "app/main.py",
                "content": "def hello():\n    return 'v2'\n",
            }
        ],
    }

    result_data, summary = await service._dispatch_action(
        project_id=sample_project.id,
        action_id="APPLY_CODE_CHANGE",
        parameters=params,
        target_id=None,
        user_id="user-123",
    )

    assert result_data["new_version"]["version_number"] == 2
    assert result_data["new_version"]["status"] == "VERIFIED"
    assert result_data["new_version"]["file_count"] == 2
    assert sample_v1_version.status == DevelopmentVersionStatus.SUPERSEDED
    assert mock_db.commit.called

    # Ensure verification_summary strictly validates against VerificationSnapshot schema
    from app.schemas.development_version import VerificationSnapshot
    ver_sum = result_data["new_version"]["verification_summary"]
    validated_snapshot = VerificationSnapshot.model_validate(ver_sum)
    assert validated_snapshot.is_verified is True
    assert validated_snapshot.static_analysis.status.value == "PASSED"
    assert validated_snapshot.sandbox_execution.status.value == "NOT_RUN"


@pytest.mark.asyncio
async def test_apply_code_change_concurrency_conflict(mock_db, sample_project, sample_v1_version):
    """Verify that if the active version changed in the meantime, ConflictError is raised."""
    different_active = MagicMock(version_id=uuid.uuid4(), version_number=2)

    version_svc = MagicMock()
    version_svc.get_active_version = AsyncMock(return_value=different_active)

    service = make_action_service(mock_db, version_svc=version_svc)

    params = {
        "version_id": str(sample_v1_version.id),
        "reason": "Stale update",
        "changes": [{"file_path": "app/main.py", "content": "x = 1\n"}],
    }

    with pytest.raises(ConflictError) as exc_info:
        await service._dispatch_action(
            project_id=sample_project.id,
            action_id="APPLY_CODE_CHANGE",
            parameters=params,
            target_id=None,
            user_id="user-123",
        )
    assert "version conflict" in str(exc_info.value).lower()


@pytest.mark.asyncio
async def test_apply_code_change_syntax_validation_failure(mock_db, sample_project, sample_v1_version):
    """Verify that syntax errors abort the version creation and no changes are committed."""
    active_resp = MagicMock(version_id=sample_v1_version.id, version_number=1)

    version_svc = MagicMock()
    version_svc.sanitize_file_path = lambda p: p.replace("\\", "/").strip().lstrip("/")
    version_svc.get_active_version = AsyncMock(return_value=active_resp)
    version_svc._resolve_version_files_map = AsyncMock(return_value={
        "app/main.py": "def hello():\n    return 'v1'\n",
    })

    service = make_action_service(mock_db, version_svc=version_svc)
    mock_db.execute.return_value.scalar_one_or_none.return_value = sample_v1_version

    params = {
        "version_id": str(sample_v1_version.id),
        "reason": "Broken syntax",
        "changes": [
            {
                "file_path": "app/bad.py",
                "content": "def broken_syntax(\n",  # SyntaxError
            }
        ],
    }

    with pytest.raises(ValidationError) as exc_info:
        await service._dispatch_action(
            project_id=sample_project.id,
            action_id="APPLY_CODE_CHANGE",
            parameters=params,
            target_id=None,
            user_id="user-123",
        )
    assert "syntax validation failed" in str(exc_info.value).lower()


@pytest.mark.asyncio
async def test_assistant_reasoning_transient_retry():
    """Verify AssistantReasoningService retries on TransientProviderError."""
    mock_provider = AsyncMock()
    mock_provider.default_model = "test-model"
    mock_provider.provider_name = "test-provider"

    mock_response = AssistantResponseSchema(
        message="Recovered successfully after transient error",
        persona="IntelliDev",
        intent="QUESTION_ANSWERING",
    )

    # First attempt raises TransientProviderError, second attempt succeeds
    mock_provider.generate_structured = AsyncMock(
        side_effect=[
            TransientProviderError("Provider rate limit reached, retry after 1s"),
            mock_response,
        ]
    )

    service = AssistantReasoningService(provider=mock_provider, max_retries=2)

    context = AssistantContext(
        project_id=uuid.uuid4(),
        project_name="MiniTask",
        project_slug="minitask",
        project_status="IN_PROGRESS",
    )

    with patch("asyncio.sleep", new_callable=AsyncMock) as mock_sleep:
        schema = await service.generate_response(
            user_message="Hello, can you help me?",
            context=context,
        )

    assert schema.message == "Recovered successfully after transient error"
    assert mock_provider.generate_structured.call_count == 2
    assert mock_sleep.called
