"""Unit Tests for Error Handlers and Custom Exceptions."""

import pytest
from httpx import AsyncClient
from unittest.mock import patch
from app.core.exceptions import ConfigurationError, ValidationError


@pytest.mark.asyncio
async def test_starlette_not_found_handler(client: AsyncClient):
    """Verify standard 404 endpoint not found returns RFC 7807 response."""
    response = await client.get("/api/v1/nonexistent-route")
    assert response.status_code == 404
    data = response.json()
    assert data["status"] == 404
    assert data["title"] == "Endpoint Not Found"
    assert "trace_id" in data


@pytest.mark.asyncio
async def test_starlette_method_not_allowed_handler(client: AsyncClient):
    """Verify 405 Method Not Allowed returns RFC 7807 response."""
    response = await client.post("/api/v1/health")
    assert response.status_code == 405
    data = response.json()
    assert data["status"] == 405
    assert data["title"] == "Method Not Allowed"


@pytest.mark.asyncio
async def test_unhandled_exception_returns_500_without_stack_trace():
    """Verify unexpected exception yields RFC 7807 500 error without exposing stack traces."""
    from httpx import ASGITransport
    from app.main import app
    transport = ASGITransport(app=app, raise_app_exceptions=False)
    async with AsyncClient(transport=transport, base_url="http://testserver") as test_client:
        with patch("app.services.project_service.ProjectService.list_projects", side_effect=RuntimeError("Secret DB crash!")):
            response = await test_client.get("/api/v1/projects")

    assert response.status_code == 500
    data = response.json()
    assert data["status"] == 500
    assert data["title"] == "Internal Server Error"
    assert "Secret DB crash!" not in response.text
    assert "trace_id" in data


def test_custom_exceptions():
    """Verify custom exception representations."""
    ve = ValidationError("Invalid value", errors=[{"field": "name"}])
    assert ve.status_code == 422
    assert ve.extra["errors"] == [{"field": "name"}]

    ce = ConfigurationError("Config failed")
    assert ce.status_code == 500
