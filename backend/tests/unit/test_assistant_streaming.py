"""Unit Tests for Assistant Server-Sent Events (SSE) Streaming (Milestone 4 - Workstream 2)."""

import json
import uuid
import pytest
from httpx import AsyncClient, ASGITransport
from unittest.mock import AsyncMock, MagicMock

from app.main import app
from app.models.project import Project
from app.models.assistant import AssistantConversation
from app.api.dependencies import (
    get_assistant_context_builder,
    get_assistant_reasoning_service,
    get_db,
    get_engineering_action_service,
)
from app.schemas.assistant import AssistantResponseSchema, AssistantActionCandidate, AssistantContext


from datetime import datetime, timezone

@pytest.fixture
def test_project_id():
    return uuid.uuid4()


@pytest.mark.asyncio
async def test_assistant_streaming_conversational(test_project_id):
    """Verify that a conversational prompt streams SSE chunks and finishes with event: done."""
    mock_session = AsyncMock()
    mock_project = Project(
        id=test_project_id,
        name="Stream Project",
        slug="stream-project",
        status="IN_PROGRESS",
        settings={},
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    mock_project_res = MagicMock()
    mock_project_res.scalar_one_or_none.return_value = mock_project

    # When querying project, return mock_project
    mock_session.execute.return_value = mock_project_res

    # Mock reasoning service that yields progressive stream chunks
    mock_reasoning_service = MagicMock()
    async def mock_chunk_stream(*args, **kwargs):
        yield "Hello! "
        yield "React hooks "
        yield "are powerful."

    mock_reasoning_service.classify_development_intent.return_value = None
    mock_reasoning_service.generate_response_stream = mock_chunk_stream
    mock_reasoning_service.sanitize_response_text = lambda x: x

    mock_context_builder = MagicMock()
    mock_context = AssistantContext(
        project_id=test_project_id,
        project_name="Stream Project",
        project_slug="stream-project",
        project_status="IN_PROGRESS",
    )
    mock_context_builder.build_context = AsyncMock(return_value=mock_context)

    app.dependency_overrides[get_db] = lambda: mock_session
    app.dependency_overrides[get_assistant_reasoning_service] = lambda: mock_reasoning_service
    app.dependency_overrides[get_assistant_context_builder] = lambda: mock_context_builder

    try:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                f"/api/v1/projects/{test_project_id}/assistant/messages/stream",
                json={"content": "Explain React hooks briefly."},
            )
            assert response.status_code == 200
            assert "text/event-stream" in response.headers.get("content-type", "")

            lines = response.text.strip().split("\n")
            event_types = [l.replace("event: ", "") for l in lines if l.startswith("event: ")]
            assert "start" in event_types
            assert "content" in event_types
            assert "done" in event_types

            # Verify chunks were received
            content_lines = [l for l in lines if l.startswith("data: {\"chunk\":")]
            assert len(content_lines) >= 3

    finally:
        app.dependency_overrides.pop(get_db, None)
        app.dependency_overrides.pop(get_assistant_reasoning_service, None)
        app.dependency_overrides.pop(get_assistant_context_builder, None)


@pytest.mark.asyncio
async def test_assistant_streaming_code_modification_atomic(test_project_id):
    """Verify that code modification emits status, diffs, and done with action candidate."""
    mock_session = AsyncMock()
    mock_project = Project(
        id=test_project_id,
        name="Stream Project",
        slug="stream-project",
        status="IN_PROGRESS",
        settings={"active_version_id": str(uuid.uuid4())},
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    mock_project_res = MagicMock()
    mock_project_res.scalar_one_or_none.return_value = mock_project
    mock_session.execute.return_value = mock_project_res

    mock_reasoning_service = MagicMock()
    mock_reasoning_service.classify_development_intent.return_value = None

    v_id = uuid.uuid4()
    mock_action = AssistantActionCandidate(
        action_id="APPLY_CODE_CHANGE",
        parameters={
            "version_id": str(v_id),
            "reason": "Add Clear button",
            "changes": [{"file_path": "App.tsx", "content": "export default function App() {}"}],
        },
    )
    mock_reasoning_output = AssistantResponseSchema(
        message="I propose adding a clear completed button.",
        suggested_action=mock_action,
        persona="IntelliDev",
        intent="CODE_MODIFICATION",
    )
    mock_reasoning_service.generate_response = AsyncMock(return_value=mock_reasoning_output)

    # Mock action service
    mock_action_service = MagicMock()
    from app.schemas.assistant import ActionResult, ActionStatus
    mock_action_result = ActionResult(
        action_id="APPLY_CODE_CHANGE",
        status=ActionStatus.PENDING_CONFIRMATION,
        summary="Proposed 1 change",
        requires_confirmation=True,
        confirmation_token="test-token-123",
    )
    mock_action_service.execute_action = AsyncMock(return_value=mock_action_result)

    mock_context_builder = MagicMock()
    mock_context = AssistantContext(
        project_id=test_project_id,
        project_name="Stream Project",
        project_slug="stream-project",
        project_status="IN_PROGRESS",
    )
    mock_context_builder.build_context = AsyncMock(return_value=mock_context)

    app.dependency_overrides[get_db] = lambda: mock_session
    app.dependency_overrides[get_assistant_reasoning_service] = lambda: mock_reasoning_service
    app.dependency_overrides[get_assistant_context_builder] = lambda: mock_context_builder
    app.dependency_overrides[get_engineering_action_service] = lambda: mock_action_service

    try:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                f"/api/v1/projects/{test_project_id}/assistant/messages/stream",
                json={"content": "Please update App.tsx to add clear button."},
            )
            assert response.status_code == 200
            assert "text/event-stream" in response.headers.get("content-type", "")

            text = response.text
            assert "event: status" in text
            assert "event: content" in text
            assert "event: done" in text
            assert "APPLY_CODE_CHANGE" in text
            assert "test-token-123" in text

    finally:
        app.dependency_overrides.pop(get_db, None)
        app.dependency_overrides.pop(get_assistant_reasoning_service, None)
        app.dependency_overrides.pop(get_assistant_context_builder, None)
        app.dependency_overrides.pop(get_engineering_action_service, None)


@pytest.mark.asyncio
async def test_assistant_streaming_provider_error(test_project_id):
    """Verify that provider failure yields event: error SSE packet cleanly."""
    mock_session = AsyncMock()
    mock_project = Project(
        id=test_project_id,
        name="Stream Project",
        slug="stream-project",
        status="IN_PROGRESS",
        settings={},
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    mock_project_res = MagicMock()
    mock_project_res.scalar_one_or_none.return_value = mock_project
    mock_session.execute.return_value = mock_project_res

    mock_reasoning_service = MagicMock()
    mock_reasoning_service.classify_development_intent.return_value = None

    async def mock_failing_stream(*args, **kwargs):
        yield "Initial thought... "
        raise RuntimeError("Provider connection failed: rate limit exceeded.")

    mock_reasoning_service.generate_response_stream = mock_failing_stream

    mock_context_builder = MagicMock()
    mock_context = AssistantContext(
        project_id=test_project_id,
        project_name="Stream Project",
        project_slug="stream-project",
        project_status="IN_PROGRESS",
    )
    mock_context_builder.build_context = AsyncMock(return_value=mock_context)

    app.dependency_overrides[get_db] = lambda: mock_session
    app.dependency_overrides[get_assistant_reasoning_service] = lambda: mock_reasoning_service
    app.dependency_overrides[get_assistant_context_builder] = lambda: mock_context_builder

    try:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                f"/api/v1/projects/{test_project_id}/assistant/messages/stream",
                json={"content": "Failing query"},
            )
            assert response.status_code == 200
            assert "text/event-stream" in response.headers.get("content-type", "")

            text = response.text
            assert "event: error" in text
            assert "Provider connection failed" in text

    finally:
        app.dependency_overrides.pop(get_db, None)
        app.dependency_overrides.pop(get_assistant_reasoning_service, None)
        app.dependency_overrides.pop(get_assistant_context_builder, None)


@pytest.mark.asyncio
async def test_assistant_streaming_project_not_found():
    """Verify that non-existent project returns 404 before stream opens."""
    mock_session = AsyncMock()
    mock_project_res = MagicMock()
    mock_project_res.scalar_one_or_none.return_value = None
    mock_session.execute.return_value = mock_project_res

    app.dependency_overrides[get_db] = lambda: mock_session

    try:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            random_id = uuid.uuid4()
            response = await client.post(
                f"/api/v1/projects/{random_id}/assistant/messages/stream",
                json={"content": "Hello?"},
            )
            assert response.status_code == 404

    finally:
        app.dependency_overrides.pop(get_db, None)

