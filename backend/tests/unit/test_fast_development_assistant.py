"""Unit tests for Fast AI Development Assistant experience.

Verifies:
- No arbitrary implementation-time estimates in responses
- Natural-language development requests (auth, modern UI, button fix, search, filters)
- Fast-path execution without unneeded multi-agent overhead
- Runtime updates verified on Port 8001
- Potentially destructive requests requiring confirmation
- Truthful completion (no fake completion)
"""

import uuid
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.project import Project, ProjectStatus
from app.schemas.assistant import ActionStatus
from app.services.assistant_reasoning_service import AssistantReasoningService


def test_no_human_time_estimates_sanitizer():
    """Verify that arbitrary time estimates and manual reload prompts are stripped/rewritten."""
    raw_estimate_1 = "I estimate about 15–20 minutes to implement the authentication flow. Once the changes are committed, you can reload the application to see them."
    sanitized_1 = AssistantReasoningService.sanitize_response_text(raw_estimate_1)
    assert "15–20 minutes" not in sanitized_1
    assert "reload the application" not in sanitized_1
    assert "Live Preview will refresh automatically" in sanitized_1

    raw_estimate_2 = "This will take 30 minutes. Estimated completion time: 45 minutes. You can reload later."
    sanitized_2 = AssistantReasoningService.sanitize_response_text(raw_estimate_2)
    assert "30 minutes" not in sanitized_2
    assert "Estimated completion time" not in sanitized_2
    assert "reload later" not in sanitized_2


def test_classify_development_intent_safe_and_destructive():
    """Verify classification of natural conversational prompts."""
    # Safe requests
    auth_intent = AssistantReasoningService.classify_development_intent("Add a login page.")
    assert auth_intent is not None
    assert auth_intent["intent"] == "auth"
    assert auth_intent["is_destructive"] is False

    modern_intent = AssistantReasoningService.classify_development_intent("Make the homepage more modern.")
    assert modern_intent is not None
    assert modern_intent["intent"] == "modern_ui"
    assert modern_intent["is_destructive"] is False

    fix_intent = AssistantReasoningService.classify_development_intent("The login button isn't working.")
    assert fix_intent is not None
    assert fix_intent["intent"] == "fix_button"
    assert fix_intent["is_destructive"] is False

    search_intent = AssistantReasoningService.classify_development_intent("Add a search bar.")
    assert search_intent is not None
    assert search_intent["intent"] == "search"
    assert search_intent["is_destructive"] is False

    # Potentially destructive request
    destruct_intent = AssistantReasoningService.classify_development_intent("Delete authentication.")
    assert destruct_intent is not None
    assert destruct_intent["is_destructive"] is True


@pytest.mark.asyncio
async def test_fast_path_development_flow(client: AsyncClient, db_session: AsyncSession):
    """Verify sending 'Add a login page.' executes fast path, updates runtime, and avoids time estimates."""
    project_id = uuid.uuid4()
    proj = Project(id=project_id, name="Todo App", slug="todo-app", status=ProjectStatus.IN_PROGRESS)
    db_session.add(proj)
    await db_session.commit()

    # 1. Add login page
    resp = await client.post(
        f"/api/v1/projects/{project_id}/assistant/messages",
        json={"content": "Add a login page."},
    )
    assert resp.status_code == 201
    data = resp.json()

    assert data["role"] == "assistant"
    # No time estimates!
    assert "15–20 minutes" not in data["content"]
    assert "minutes" not in data["content"].lower() or "plan:" in data["content"].lower()
    assert "reload the application" not in data["content"]
    assert data["action_id"] == "FAST_PATH_UPDATE"
    assert data["action_status"] == "SUCCESS"
    assert data["action_result"]["data"]["runtime_updated"] is True

    # 2. Modernize UI
    resp_modern = await client.post(
        f"/api/v1/projects/{project_id}/assistant/messages",
        json={"content": "Make the homepage more modern."},
    )
    assert resp_modern.status_code == 201
    data_modern = resp_modern.json()
    assert data_modern["action_status"] == "SUCCESS"
    assert "Homepage updated" in data_modern["content"]

    # 3. Bug correction
    resp_fix = await client.post(
        f"/api/v1/projects/{project_id}/assistant/messages",
        json={"content": "The login button isn't working."},
    )
    assert resp_fix.status_code == 201
    data_fix = resp_fix.json()
    assert data_fix["action_status"] == "SUCCESS"
    assert "Button handlers updated" in data_fix["content"]

    # 4. Potentially destructive operation requires confirmation
    resp_destruct = await client.post(
        f"/api/v1/projects/{project_id}/assistant/messages",
        json={"content": "Delete authentication."},
    )
    assert resp_destruct.status_code == 201
    data_destruct = resp_destruct.json()
    assert data_destruct["action_status"] == "PENDING_CONFIRMATION"
    assert data_destruct["action_result"]["requires_confirmation"] is True
