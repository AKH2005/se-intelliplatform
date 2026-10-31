"""API endpoint integration tests for Phase 11I Intelli Assistant."""

import uuid
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.exceptions import AgentConfigurationError, ProviderError, TransientProviderError
from app.agents.providers.mock import MockLLMProvider
from app.api.dependencies import get_assistant_llm_provider, get_current_user_optional
from app.main import app
from app.models.assistant import AssistantConversation, AssistantMessage
from app.models.development_version import DevelopmentVersion, DevelopmentVersionStatus
from app.models.project import Project, ProjectStatus
from app.models.user import User, UserRole
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


@pytest.mark.asyncio
async def test_assistant_create_and_delete_conversation(client: AsyncClient, db_session: AsyncSession):
    """Verify explicit conversation creation and deletion endpoints."""
    project_id = uuid.uuid4()
    proj = Project(id=project_id, name="Conversations Project", slug="conv-proj", status=ProjectStatus.IN_PROGRESS)
    db_session.add(proj)
    await db_session.commit()

    # 1. Create conversation explicitly
    create_resp = await client.post(
        f"/api/v1/projects/{project_id}/assistant/conversations",
        json={"title": "Architecture Discussion"},
    )
    assert create_resp.status_code == 201
    create_data = create_resp.json()
    assert create_data["title"] == "Architecture Discussion"
    assert create_data["project_id"] == str(project_id)
    assert create_data["messages"] == []
    conv_id = create_data["conversation_id"]

    # 2. Verify it shows up in conversation listing
    list_resp = await client.get(f"/api/v1/projects/{project_id}/assistant/conversations")
    assert list_resp.status_code == 200
    list_data = list_resp.json()
    assert any(c["conversation_id"] == conv_id for c in list_data["items"])

    # 3. Delete the conversation
    delete_resp = await client.delete(f"/api/v1/projects/{project_id}/assistant/conversations/{conv_id}")
    assert delete_resp.status_code == 204

    # 4. Fetching deleted conversation returns 404
    get_deleted = await client.get(f"/api/v1/projects/{project_id}/assistant/conversations/{conv_id}")
    assert get_deleted.status_code == 404


@pytest.mark.asyncio
async def test_assistant_project_aware_context_assembly(client: AsyncClient, db_session: AsyncSession):
    """Verify that project source files and active version manifest are extracted into context prompt."""
    project_id = uuid.uuid4()
    proj = Project(
        id=project_id,
        name="TaskMaster Pro",
        slug="taskmaster-pro",
        description="A full-stack React task manager",
        status=ProjectStatus.IN_PROGRESS,
    )
    db_session.add(proj)

    # Active development version with files manifest
    ver_id = uuid.uuid4()
    ver = DevelopmentVersion(
        id=ver_id,
        project_id=project_id,
        version_number=1,
        status=DevelopmentVersionStatus.VERIFIED,
        content_hash="abc123hash",
        manifest_hash="man123hash",
        artifact_key="code_generation",
        files_manifest=[
            {"path": "frontend/src/App.tsx", "size_bytes": 180, "language": "typescript"},
            {"path": "package.json", "size_bytes": 120, "language": "json"},
            {"path": "README.md", "size_bytes": 90, "language": "markdown"},
        ],
    )
    db_session.add(ver)
    await db_session.commit()

    provider = MockLLMProvider()
    provider.register_structured_response(
        AssistantResponseSchema(
            message="In frontend/src/App.tsx, the App component renders the main task board.",
            suggested_action=None,
        )
    )
    app.dependency_overrides[get_assistant_llm_provider] = lambda: provider

    try:
        response = await client.post(
            f"/api/v1/projects/{project_id}/assistant/messages",
            json={"content": "Explain the frontend App component in frontend/src/App.tsx"},
        )
        assert response.status_code == 201
        data = response.json()
        assert "frontend/src/App.tsx" in data["content"]

        # Check call history received by MockLLMProvider
        assert len(provider.call_history) == 1
        llm_req = provider.call_history[0]
        context_msg = llm_req.messages[1].content
        assert "<untrusted_content>" in context_msg
        assert "TaskMaster Pro" in context_msg
        assert "frontend/src/App.tsx" in context_msg
        assert "package.json" in context_msg
    finally:
        app.dependency_overrides.pop(get_assistant_llm_provider, None)


@pytest.mark.asyncio
async def test_assistant_missing_files_requested(client: AsyncClient, db_session: AsyncSession):
    """Verify that asking about non-existent files marks them in missing_files_requested."""
    project_id = uuid.uuid4()
    proj = Project(id=project_id, name="Isolated Project", slug="isolated-proj", status=ProjectStatus.IN_PROGRESS)
    ver = DevelopmentVersion(
        id=uuid.uuid4(),
        project_id=project_id,
        version_number=1,
        status=DevelopmentVersionStatus.VERIFIED,
        content_hash="h1",
        manifest_hash="m1",
        artifact_key="code_generation",
        files_manifest=[{"path": "README.md", "size_bytes": 50}],
    )
    db_session.add_all([proj, ver])
    await db_session.commit()

    provider = MockLLMProvider()
    provider.register_structured_response(
        AssistantResponseSchema(
            message="The requested file backend/controllers/auth.py does not exist in active version v1.",
            suggested_action=None,
        )
    )
    app.dependency_overrides[get_assistant_llm_provider] = lambda: provider

    try:
        response = await client.post(
            f"/api/v1/projects/{project_id}/assistant/messages",
            json={"content": "Explain backend/controllers/auth.py"},
        )
        assert response.status_code == 201
        llm_req = provider.call_history[0]
        context_msg = llm_req.messages[1].content
        assert "missing_files_requested" in context_msg
        assert "backend/controllers/auth.py" in context_msg
    finally:
        app.dependency_overrides.pop(get_assistant_llm_provider, None)


@pytest.mark.asyncio
async def test_assistant_debugging_guidance_with_error_text(client: AsyncClient, db_session: AsyncSession):
    """Verify that explicitly supplied error text is captured and forwarded in context."""
    project_id = uuid.uuid4()
    proj = Project(id=project_id, name="Debug Project", slug="debug-proj", status=ProjectStatus.IN_PROGRESS)
    db_session.add(proj)
    await db_session.commit()

    provider = MockLLMProvider()
    provider.register_structured_response(
        AssistantResponseSchema(
            message="Based on the TypeError, tasks is undefined prior to fetching.",
            suggested_action=None,
        )
    )
    app.dependency_overrides[get_assistant_llm_provider] = lambda: provider

    try:
        response = await client.post(
            f"/api/v1/projects/{project_id}/assistant/messages",
            json={
                "content": "Why is my task list failing to render?",
                "error_message": "TypeError: Cannot read properties of undefined (reading 'map')",
            },
        )
        assert response.status_code == 201
        llm_req = provider.call_history[0]
        context_msg = llm_req.messages[1].content
        assert "supplied_error_text" in context_msg
        assert "TypeError: Cannot read properties of undefined" in context_msg
    finally:
        app.dependency_overrides.pop(get_assistant_llm_provider, None)


@pytest.mark.asyncio
async def test_assistant_context_limits_and_oversized_inputs(client: AsyncClient, db_session: AsyncSession):
    """Verify that oversized user queries and empty queries are rejected with validation errors."""
    project_id = uuid.uuid4()
    proj = Project(id=project_id, name="Limits Project", slug="limits-proj", status=ProjectStatus.IN_PROGRESS)
    db_session.add(proj)
    await db_session.commit()

    # Empty content rejected
    empty_resp = await client.post(
        f"/api/v1/projects/{project_id}/assistant/messages",
        json={"content": "   "},
    )
    assert empty_resp.status_code == 422

    # Oversized content (> 4000 characters) rejected
    oversized_resp = await client.post(
        f"/api/v1/projects/{project_id}/assistant/messages",
        json={"content": "a" * 4001},
    )
    assert oversized_resp.status_code == 422


@pytest.mark.asyncio
async def test_assistant_missing_provider_configuration(client: AsyncClient, db_session: AsyncSession):
    """Verify that missing provider configuration returns RFC 7807 error with 500 status."""
    project_id = uuid.uuid4()
    proj = Project(id=project_id, name="Config Error Project", slug="config-err-proj", status=ProjectStatus.IN_PROGRESS)
    db_session.add(proj)
    await db_session.commit()

    def raise_config_error():
        raise AgentConfigurationError("Groq provider selected, but GROQ_API_KEY is not configured.")

    app.dependency_overrides[get_assistant_llm_provider] = raise_config_error

    try:
        response = await client.post(
            f"/api/v1/projects/{project_id}/assistant/messages",
            json={"content": "Hello assistant"},
        )
        assert response.status_code == 500
        problem = response.json()
        assert "title" in problem
        assert "detail" in problem
        assert "GROQ_API_KEY is not configured" in problem["detail"]
    finally:
        app.dependency_overrides.pop(get_assistant_llm_provider, None)


@pytest.mark.asyncio
async def test_assistant_provider_rate_limit_and_timeout_errors(client: AsyncClient, db_session: AsyncSession):
    """Verify that transient rate limit errors return 503 and permanent errors return 502."""
    project_id = uuid.uuid4()
    proj = Project(id=project_id, name="Error Project", slug="err-proj", status=ProjectStatus.IN_PROGRESS)
    db_session.add(proj)
    await db_session.commit()

    # 1. Transient error -> 503
    transient_provider = MockLLMProvider()
    transient_provider.simulate_transient_failures(1)
    app.dependency_overrides[get_assistant_llm_provider] = lambda: transient_provider

    try:
        resp_503 = await client.post(
            f"/api/v1/projects/{project_id}/assistant/messages",
            json={"content": "What is the project architecture?"},
        )
        assert resp_503.status_code == 503
        problem_503 = resp_503.json()
        assert "Transient" in problem_503["title"]

        # 2. Permanent error -> 502
        permanent_provider = MockLLMProvider()
        permanent_provider.simulate_permanent_failure(
            ProviderError(message="Upstream model quota exceeded", provider_name="mock")
        )

        app.dependency_overrides[get_assistant_llm_provider] = lambda: permanent_provider

        resp_502 = await client.post(
            f"/api/v1/projects/{project_id}/assistant/messages",
            json={"content": "What is the project architecture?"},
        )
        assert resp_502.status_code == 502
        problem_502 = resp_502.json()
        assert "Provider Error" in problem_502["title"]
    finally:
        app.dependency_overrides.pop(get_assistant_llm_provider, None)


@pytest.mark.asyncio
async def test_assistant_unauthorized_user_and_cross_user_isolation(client: AsyncClient, db_session: AsyncSession):
    """Verify that unauthorized users cannot access another user's project or conversation."""
    user_a_id = uuid.uuid4()
    user_b_id = uuid.uuid4()

    user_a = User(id=user_a_id, email="alice@test.local", name="Alice", hashed_password="pw", is_active=True)
    user_b = User(id=user_b_id, email="bob@test.local", name="Bob", hashed_password="pw", is_active=True)
    proj_a = Project(
        id=uuid.uuid4(),
        owner_id=user_a_id,
        name="Alice Private Project",
        slug="alice-private",
        status=ProjectStatus.IN_PROGRESS,
    )
    conv_a = AssistantConversation(
        id=uuid.uuid4(),
        project_id=proj_a.id,
        user_id=user_a_id,
        title="Alice Secret Conversation",
    )
    db_session.add_all([user_a, user_b, proj_a, conv_a])
    await db_session.commit()

    # User B attempting to access Alice's project conversations -> 403 Forbidden
    app.dependency_overrides[get_current_user_optional] = lambda: user_b
    try:
        resp_list = await client.get(f"/api/v1/projects/{proj_a.id}/assistant/conversations")
        assert resp_list.status_code == 403

        resp_detail = await client.get(f"/api/v1/projects/{proj_a.id}/assistant/conversations/{conv_a.id}")
        assert resp_detail.status_code == 403

        resp_send = await client.post(
            f"/api/v1/projects/{proj_a.id}/assistant/messages",
            json={"content": "Sneak into Alice's project", "conversation_id": str(conv_a.id)},
        )
        assert resp_send.status_code == 403
    finally:
        app.dependency_overrides.pop(get_current_user_optional, None)


@pytest.mark.asyncio
async def test_assistant_conversation_followup_continuity(client: AsyncClient, db_session: AsyncSession):
    """Verify that follow-up messages preserve prior turn context across requests."""
    project_id = uuid.uuid4()
    proj = Project(id=project_id, name="Continuity Project", slug="cont-proj", status=ProjectStatus.IN_PROGRESS)
    db_session.add(proj)
    await db_session.commit()

    provider = MockLLMProvider()
    provider.register_structured_response(
        AssistantResponseSchema(
            message="The system uses PostgreSQL for relational data persistence.",
            suggested_action=None,
        )
    )
    provider.register_structured_response(
        AssistantResponseSchema(
            message="Specifically, the users and projects tables model core entities.",
            suggested_action=None,
        )
    )
    app.dependency_overrides[get_assistant_llm_provider] = lambda: provider

    try:
        # Turn 1
        resp_1 = await client.post(
            f"/api/v1/projects/{project_id}/assistant/messages",
            json={"content": "Which database does the project use?"},
        )
        assert resp_1.status_code == 201
        data_1 = resp_1.json()
        conv_id = data_1["conversation_id"]

        # Turn 2 with conversation_id
        resp_2 = await client.post(
            f"/api/v1/projects/{project_id}/assistant/messages",
            json={"content": "And which tables are defined?", "conversation_id": conv_id},
        )
        assert resp_2.status_code == 201

        # Verify second LLM call received history from turn 1
        assert len(provider.call_history) == 2
        second_call = provider.call_history[1]
        history_roles = [m.role for m in second_call.messages]
        # Should include system, context, assistant ack, prior user, prior assistant, and latest user
        assert "user" in history_roles
        assert "assistant" in history_roles
        turn1_user_msg = next((m for m in second_call.messages if m.content == "Which database does the project use?"), None)
        assert turn1_user_msg is not None

        # Verify persisted conversation history has 4 messages in total
        detail_resp = await client.get(f"/api/v1/projects/{project_id}/assistant/conversations/{conv_id}")
        assert detail_resp.status_code == 200
        detail = detail_resp.json()
        assert len(detail["messages"]) == 4
        assert detail["messages"][0]["content"] == "Which database does the project use?"
        assert detail["messages"][1]["content"] == "The system uses PostgreSQL for relational data persistence."
        assert detail["messages"][2]["content"] == "And which tables are defined?"
        assert detail["messages"][3]["content"] == "Specifically, the users and projects tables model core entities."
    finally:
        app.dependency_overrides.pop(get_assistant_llm_provider, None)

