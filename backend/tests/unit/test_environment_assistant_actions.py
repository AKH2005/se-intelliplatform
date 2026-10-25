"""Unit tests for Phase 13 Assistant Environment & Deployment Actions."""

from unittest.mock import AsyncMock, MagicMock
import uuid
import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.assistant import AssistantConversation
from app.models.development_version import DevelopmentVersion, DevelopmentVersionStatus
from app.models.environment import EnvironmentType
from app.models.project import Project, ProjectStatus
from app.schemas.assistant import ActionStatus
from app.services.action_registry import get_action_definition, is_confirmation_required
from app.services.assistant_context_builder import AssistantContextBuilder
from app.services.engineering_action_service import EngineeringActionService
from app.services.environment_service import EnvironmentService


@pytest.fixture
async def sample_project(db_session: AsyncSession) -> Project:
    project = Project(
        name="Assistant Env Project",
        slug="assistant-env-proj",
        status=ProjectStatus.IN_PROGRESS,
    )
    db_session.add(project)
    await db_session.flush()
    return project


@pytest.fixture
async def conversation(db_session: AsyncSession, sample_project: Project) -> AssistantConversation:
    conv = AssistantConversation(
        project_id=sample_project.id,
        title="Environment Session",
    )
    db_session.add(conv)
    await db_session.flush()
    return conv


@pytest.fixture
async def sample_version(db_session: AsyncSession, sample_project: Project) -> DevelopmentVersion:
    v = DevelopmentVersion(
        project_id=sample_project.id,
        version_number=1,
        artifact_key="art-v1",
        status=DevelopmentVersionStatus.VERIFIED,
        content_hash="hash-v1",
        manifest_hash="m-v1",
        file_count=2,
        total_size_bytes=100,
        source_reason="Initial v1",
        created_by="system",
        verification_summary={"verification_status": "PASSED", "is_verified": True},
    )
    db_session.add(v)
    await db_session.flush()
    return v


@pytest.fixture
def env_service(db_session: AsyncSession) -> EnvironmentService:
    return EnvironmentService(session=db_session)


@pytest.fixture
def action_service(db_session: AsyncSession, env_service: EnvironmentService) -> EngineeringActionService:
    service = EngineeringActionService(
        session=db_session,
        version_service=MagicMock(),
        verification_service=MagicMock(),
        requirement_service=MagicMock(),
        context_engine=MagicMock(),
        workflow_service=MagicMock(),
        environment_service=env_service,
    )
    service._authorize_target = AsyncMock()
    return service


def test_environment_actions_registered():
    """Verify all 7 environment actions are properly registered in ACTION_REGISTRY."""
    expected_actions = [
        ("GET_ENVIRONMENTS", False),
        ("GET_ENVIRONMENT_STATUS", False),
        ("GET_DEPLOYMENT_HISTORY", False),
        ("CHECK_PROMOTION_ELIGIBILITY", False),
        ("PROMOTE_VERSION", True),
        ("DEPLOY_TO_ENVIRONMENT", True),
        ("ROLLBACK_ENVIRONMENT", True),
    ]

    for action_id, requires_conf in expected_actions:
        defn = get_action_definition(action_id)
        assert defn is not None
        assert defn.action_id == action_id
        assert is_confirmation_required(action_id) == requires_conf


@pytest.mark.asyncio
async def test_get_environments_action(
    action_service: EngineeringActionService,
    sample_project: Project,
    conversation: AssistantConversation,
) -> None:
    """Verify GET_ENVIRONMENTS returns project environments."""
    result = await action_service.execute_action(
        project_id=sample_project.id,
        conversation_id=conversation.id,
        action_id="GET_ENVIRONMENTS",
        parameters={},
    )
    assert result.status == ActionStatus.SUCCESS
    assert "environments" in result.data
    assert len(result.data["environments"]) == 3


@pytest.mark.asyncio
async def test_check_promotion_eligibility_action(
    action_service: EngineeringActionService,
    sample_project: Project,
    conversation: AssistantConversation,
    sample_version: DevelopmentVersion,
) -> None:
    """Verify CHECK_PROMOTION_ELIGIBILITY action execution."""
    result = await action_service.execute_action(
        project_id=sample_project.id,
        conversation_id=conversation.id,
        action_id="CHECK_PROMOTION_ELIGIBILITY",
        parameters={
            "version_id": str(sample_version.id),
            "target_environment": "STAGING",
            "source_environment": "DEVELOPMENT",
        },
    )
    assert result.status == ActionStatus.SUCCESS
    assert result.data["eligible"] is True
    assert result.data["version_number"] == 1


@pytest.mark.asyncio
async def test_mutating_actions_require_confirmation(
    action_service: EngineeringActionService,
    sample_project: Project,
    conversation: AssistantConversation,
    sample_version: DevelopmentVersion,
) -> None:
    """Ensure mutating deployment actions require confirmation tokens."""
    # PROMOTE_VERSION without token -> PENDING_CONFIRMATION
    res_promote = await action_service.execute_action(
        project_id=sample_project.id,
        conversation_id=conversation.id,
        action_id="PROMOTE_VERSION",
        parameters={
            "version_id": str(sample_version.id),
            "target_environment": "STAGING",
        },
    )
    assert res_promote.status == ActionStatus.PENDING_CONFIRMATION
    assert res_promote.confirmation_token is not None

    # DEPLOY_TO_ENVIRONMENT without token -> PENDING_CONFIRMATION
    res_deploy = await action_service.execute_action(
        project_id=sample_project.id,
        conversation_id=conversation.id,
        action_id="DEPLOY_TO_ENVIRONMENT",
        parameters={
            "environment_type": "DEVELOPMENT",
            "version_id": str(sample_version.id),
        },
    )
    assert res_deploy.status == ActionStatus.PENDING_CONFIRMATION
    assert res_deploy.confirmation_token is not None

    # ROLLBACK_ENVIRONMENT without token -> PENDING_CONFIRMATION
    res_rollback = await action_service.execute_action(
        project_id=sample_project.id,
        conversation_id=conversation.id,
        action_id="ROLLBACK_ENVIRONMENT",
        parameters={
            "environment_type": "DEVELOPMENT",
            "target_version_id": str(sample_version.id),
            "reason": "Test rollback",
        },
    )
    assert res_rollback.status == ActionStatus.PENDING_CONFIRMATION
    assert res_rollback.confirmation_token is not None


@pytest.mark.asyncio
async def test_mutating_action_executes_with_valid_token(
    action_service: EngineeringActionService,
    sample_project: Project,
    conversation: AssistantConversation,
    sample_version: DevelopmentVersion,
) -> None:
    """Ensure mutating action executes successfully when confirmation token is redeemed."""
    # 1. Request token
    req_res = await action_service.execute_action(
        project_id=sample_project.id,
        conversation_id=conversation.id,
        action_id="DEPLOY_TO_ENVIRONMENT",
        parameters={
            "environment_type": "DEVELOPMENT",
            "version_id": str(sample_version.id),
        },
    )
    token = req_res.confirmation_token
    assert token is not None

    # 2. Confirm execution via confirm_action
    exec_res = await action_service.confirm_action(
        project_id=sample_project.id,
        confirmation_token=token,
    )
    assert exec_res.status == ActionStatus.SUCCESS
    assert "deployment_id" in exec_res.data


@pytest.mark.asyncio
async def test_assistant_context_builder_includes_environments_summary(
    db_session: AsyncSession,
    sample_project: Project,
    env_service: EnvironmentService,
) -> None:
    """Verify AssistantContextBuilder populates environments_summary."""
    await env_service.get_or_create_project_environments(sample_project.id)

    mock_ctx_engine = MagicMock()
    mock_ctx = MagicMock()
    mock_ctx.project.name = sample_project.name
    mock_ctx.project.slug = sample_project.slug
    mock_ctx.project.status = sample_project.status
    mock_ctx.requirements = []
    mock_ctx_engine.generate_context = AsyncMock(return_value=mock_ctx)

    mock_ver_service = MagicMock()
    mock_ver_service.get_active_version = AsyncMock(return_value=None)

    builder = AssistantContextBuilder(
        session=db_session,
        context_engine=mock_ctx_engine,
        version_service=mock_ver_service,
        requirement_service=MagicMock(),
    )
    context = await builder.build_context(sample_project.id)

    assert context.environments_summary is not None
    assert "DEVELOPMENT" in context.environments_summary
    assert "STAGING" in context.environments_summary
    assert "PRODUCTION" in context.environments_summary
