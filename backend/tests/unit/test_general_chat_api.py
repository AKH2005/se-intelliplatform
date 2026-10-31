"""Unit tests for the Global AI Assistant & Guided App Plan API."""

import pytest
from httpx import AsyncClient
from unittest.mock import patch, AsyncMock
from app.agents.providers.mock import MockLLMProvider
from app.agents.providers.base import LLMResponse


@pytest.mark.asyncio
async def test_general_chat_endpoint_success(client: AsyncClient):
    """Verify general chat responds with AI generation."""
    mock_provider = MockLLMProvider()
    mock_provider.register_response("SE IntelliPlatform supports User Mode and Developer Mode.")

    with patch("app.api.v1.endpoints.general_chat.get_llm_provider", return_value=mock_provider):
        response = await client.post(
            "/api/v1/chat",
            json={
                "message": "How does SE IntelliPlatform work?",
                "conversation_history": [
                    {"role": "user", "content": "Hello!"},
                    {"role": "assistant", "content": "Hi there! How can I help you today?"},
                ],
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["response"] == "SE IntelliPlatform supports User Mode and Developer Mode."
        assert data["provider"] == "mock"
        assert "model" in data


@pytest.mark.asyncio
async def test_general_chat_validation_error(client: AsyncClient):
    """Verify empty message payload triggers 422 Unprocessable Entity."""
    response = await client.post(
        "/api/v1/chat",
        json={"message": ""},
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_guided_app_plan_structured_synthesis(client: AsyncClient):
    """Verify guided app plan endpoint synthesizes blueprint from prompt."""
    canned_json = """{
      "name": "RecipeMaster AI",
      "slug": "recipemaster-ai",
      "description": "Smart recipe generation and pantry inventory manager.",
      "requirements": [
        {"title": "Pantry inventory tracker", "description": "Track ingredients in real time", "type": "FUNCTIONAL", "priority": "HIGH"},
        {"title": "Recipe generation from ingredients", "description": "Suggest meals based on available items", "type": "FUNCTIONAL", "priority": "HIGH"},
        {"title": "Interactive Live Preview", "description": "Preview app in sandboxed container", "type": "NON_FUNCTIONAL", "priority": "HIGH"}
      ],
      "suggested_features": ["Nutritional breakdown", "Shopping list export"]
    }"""

    mock_provider = MockLLMProvider()
    mock_provider.register_response(canned_json)

    with patch("app.api.v1.endpoints.general_chat.get_llm_provider", return_value=mock_provider):
        response = await client.post(
            "/api/v1/chat/guided-app-plan",
            json={"prompt": "A smart recipe generator based on ingredients currently in pantry"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "RecipeMaster AI"
        assert data["slug"] == "recipemaster-ai"
        assert len(data["requirements"]) == 3
        assert data["requirements"][0]["title"] == "Pantry inventory tracker"


@pytest.mark.asyncio
async def test_guided_app_plan_fallback_on_invalid_json(client: AsyncClient):
    """Verify heuristic fallback handles non-JSON model generation gracefully."""
    mock_provider = MockLLMProvider()
    mock_provider.register_response("Not a JSON response but general text.")

    with patch("app.api.v1.endpoints.general_chat.get_llm_provider", return_value=mock_provider):
        response = await client.post(
            "/api/v1/chat/guided-app-plan",
            json={"prompt": "Task Tracker for Software Developers"},
        )
        assert response.status_code == 200
        data = response.json()
        assert "Task Tracker" in data["name"]
        assert len(data["requirements"]) >= 2
