"""API endpoint integration tests for Phase 11I Intelli Assistant."""

import uuid
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.providers.mock import MockLLMProvider
from app.api.dependencies import get_assistant_llm_provider
from app.main import app
from app.models.assistant import AssistantConversation, AssistantMessage
from app.models.development_version import DevelopmentVersion, DevelopmentVersionStatus
from app.models.project import Project, ProjectStatus
from app.schemas.assistant import (
    AssistantActionCandidate,
    AssistantResponseSchema,
)


@pytest.fixture
def mock_assistant_provider():
    provider = MockLLMProvider()
    return provider


@pytest.mark.asyncio
async def test_assistant_send_message_lifecycle(client: AsyncClient, db_session: AsyncSession):
    """Verify sending a message initializes conversation and returns structured assistant response."""
    project_id = uuid.uuid4()
    proj = Project(id=project_id, name="Solaris Engine", slug="solaris-engine", status=ProjectStatus.IN_PROGRESS)
    db_session.add(proj)
    await db_session.commit()

    # Configure mock provider structured response
    provider = MockLLMProvider()
    mock_reply = AssistantResponseSchema(
        message="I can check your project context.",
        suggested_action=AssistantActionCandidate(
            action_id="GET_PROJECT_CONTEXT",
            parameters={},
        ),
    )
    provider.register_structured_response(mock_reply)
    app.dependency_overrides[get_assistant_llm_provider] = lambda: provider

    try:
        response = await client.post(
            f"/api/v1/projects/{project_id}/assistant/messages",
            json={"content": "What is the project context?"},
        )
        assert response.status_code == 201
        data = response.json()

        assert data["role"] == "assistant"
        assert data["content"] == "I can check your project context."
        assert data["action_id"] == "GET_PROJECT_CONTEXT"
        assert data["action_status"] == "SUCCESS"
        assert data["action_result"] is not None
        assert data["action_result"]["data"]["name"] == "Solaris Engine"
        assert "conversation_id" in data
        conv_id = data["conversation_id"]

        # Verify conversation is persisted and listed
        list_resp = await client.get(f"/api/v1/projects/{project_id}/assistant/conversations")
        assert list_resp.status_code == 200
        list_data = list_resp.json()
        assert list_data["total"] >= 1
        assert any(c["conversation_id"] == conv_id for c in list_data["items"])

        # Verify single conversation fetch
        detail_resp = await client.get(f"/api/v1/projects/{project_id}/assistant/conversations/{conv_id}")
        assert detail_resp.status_code == 200
        detail_data = detail_resp.json()
        assert len(detail_data["messages"]) == 2  # user message + assistant message
        assert detail_data["messages"][0]["role"] == "user"
        assert detail_data["messages"][1]["role"] == "assistant"

    finally:
        app.dependency_overrides.pop(get_assistant_llm_provider, None)


@pytest.mark.asyncio
async def test_assistant_cross_project_conversation_isolation(client: AsyncClient, db_session: AsyncSession):
    """Verify conversations cannot be retrieved across different projects (must return 404)."""
    proj_a = Project(id=uuid.uuid4(), name="Project A", slug="proj-a", status=ProjectStatus.IN_PROGRESS)
    proj_b = Project(id=uuid.uuid4(), name="Project B", slug="proj-b", status=ProjectStatus.IN_PROGRESS)
    db_session.add_all([proj_a, proj_b])

    conv_a = AssistantConversation(id=uuid.uuid4(), project_id=proj_a.id, title="Conversation A")
    db_session.add(conv_a)
    await db_session.commit()

    # Accessing conv_a via proj_b MUST return 404
    resp = await client.get(f"/api/v1/projects/{proj_b.id}/assistant/conversations/{conv_a.id}")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_assistant_confirm_action_endpoint(client: AsyncClient, db_session: AsyncSession):
    """Verify confirmation API endpoint validates tokens and blocks replays."""
    project_id = uuid.uuid4()
    proj = Project(id=project_id, name="Project Alpha", slug="proj-alpha", status=ProjectStatus.IN_PROGRESS)
    db_session.add(proj)
    await db_session.commit()

    # Create authorized DevelopmentVersion in DB
    target_ver_uuid = uuid.uuid4()
    ver_record = DevelopmentVersion(
        id=target_ver_uuid,
        project_id=project_id,
        version_number=1,
        status=DevelopmentVersionStatus.VERIFIED,
        content_hash="hash123",
        manifest_hash="man123",
        artifact_key="code_generation",
        files_manifest=[],
    )
    # And target version 2 to activate
    ver_2_uuid = uuid.uuid4()
    ver_2 = DevelopmentVersion(
        id=ver_2_uuid,
        project_id=project_id,
        version_number=2,
        status=DevelopmentVersionStatus.VERIFIED,
        content_hash="hash456",
        manifest_hash="man456",
        artifact_key="code_generation",
        files_manifest=[],
    )
    db_session.add_all([ver_record, ver_2])
    await db_session.commit()

    provider = MockLLMProvider()
    mutating_reply = AssistantResponseSchema(
        message="I recommend activating version 2.",
        suggested_action=AssistantActionCandidate(
            action_id="ACTIVATE_VERSION",
            parameters={"version_id": str(ver_2_uuid), "reason": "Production deployment"},
        ),
    )
    provider.register_structured_response(mutating_reply)
    app.dependency_overrides[get_assistant_llm_provider] = lambda: provider

    try:
        # Trigger turn resulting in PENDING_CONFIRMATION
        msg_resp = await client.post(
            f"/api/v1/projects/{project_id}/assistant/messages",
            json={"content": "Please activate version 2."},
        )
        assert msg_resp.status_code == 201
        msg_data = msg_resp.json()

        assert msg_data["action_id"] == "ACTIVATE_VERSION"
        assert msg_data["action_status"] == "PENDING_CONFIRMATION"
        assert msg_data["action_result"]["requires_confirmation"] is True
        token = msg_data["action_result"]["confirmation_token"]
        assert token is not None

        # Confirm the action via POST /assistant/actions/confirm
        confirm_resp = await client.post(
            f"/api/v1/projects/{project_id}/assistant/actions/confirm",
            json={"confirmation_token": token},
        )
        assert confirm_resp.status_code == 200
        confirm_data = confirm_resp.json()
        assert confirm_data["status"] == "SUCCESS"

        # Replay the token: MUST fail with 409 Conflict
        replay_resp = await client.post(
            f"/api/v1/projects/{project_id}/assistant/actions/confirm",
            json={"confirmation_token": token},
        )
        assert replay_resp.status_code == 409
    finally:
        app.dependency_overrides.pop(get_assistant_llm_provider, None)


@pytest.mark.asyncio
async def test_assistant_direct_execute_endpoint(client: AsyncClient, db_session: AsyncSession):
    """Verify direct execute endpoint routes READ_ONLY actions without prompt inference."""
    project_id = uuid.uuid4()
    proj = Project(id=project_id, name="Project Beta", slug="proj-beta", status=ProjectStatus.IN_PROGRESS)
    db_session.add(proj)
    await db_session.commit()

    resp = await client.post(
        f"/api/v1/projects/{project_id}/assistant/actions/execute",
        json={
            "action_id": "GET_PROJECT_CONTEXT",
            "parameters": {},
        },
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["action_id"] == "GET_PROJECT_CONTEXT"
    assert data["status"] == "SUCCESS"
    assert data["data"]["name"] == "Project Beta"
