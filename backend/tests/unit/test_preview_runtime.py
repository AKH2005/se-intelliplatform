"""Unit tests for Application Preview Runtime & Port 8001 Lifecycle."""

import uuid
import pytest
from unittest.mock import AsyncMock, patch
from httpx import AsyncClient, ASGITransport

from app.main import create_application
from app.models.project import Project
from app.runtime.preview_runtime_manager import PreviewRuntimeManager


@pytest.mark.asyncio
async def test_preview_runtime_manager_health_check_healthy():
    manager = PreviewRuntimeManager()
    with patch.object(manager, "_sync_http_get", return_value=(True, 200, {"status": "ok", "port": 8001})):
        healthy, msg, details = await manager.check_health()
        assert healthy is True
        assert "running on port 8001" in msg
        assert details.get("status") == "ok"


@pytest.mark.asyncio
async def test_preview_runtime_manager_health_check_unhealthy():
    manager = PreviewRuntimeManager()
    with patch.object(manager, "_sync_http_get", return_value=(False, 0, {"error": "Connection refused"})):
        healthy, msg, details = await manager.check_health()
        assert healthy is False
        assert "unavailable on port 8001" in msg


@pytest.mark.asyncio
async def test_preview_runtime_status_endpoint():
    app = create_application()
    transport = ASGITransport(app=app)
    dummy_project = Project(
        id=uuid.UUID("5ec6a638-4520-4c14-ad8b-b9d1aaa0df6c"),
        name="TaskFlow",
        slug="taskflow",
        description="Task flow test project",
        owner_id=None,
    )
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        with patch("app.api.v1.endpoints.preview_runtime._resolve_project", new_callable=AsyncMock, return_value=dummy_project), \
             patch("app.api.v1.endpoints.preview_runtime.preview_runtime_manager.check_health", new_callable=AsyncMock) as mock_health:
            mock_health.return_value = (True, "Application running on port 8001.", {"active_mode": "taskflow"})
            
            resp = await client.get("/api/v1/projects/5ec6a638-4520-4c14-ad8b-b9d1aaa0df6c/runtime/status")
            assert resp.status_code == 200
            data = resp.json()
            assert data["status"] == "RUNNING"
            assert data["port"] == 8001
            assert data["is_healthy"] is True
            assert data["preview_url"] == "http://127.0.0.1:8001/"


@pytest.mark.asyncio
async def test_preview_runtime_status_endpoint_unavailable():
    app = create_application()
    transport = ASGITransport(app=app)
    dummy_project = Project(
        id=uuid.UUID("5ec6a638-4520-4c14-ad8b-b9d1aaa0df6c"),
        name="TaskFlow",
        slug="taskflow",
        description="Task flow test project",
        owner_id=None,
    )
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        with patch("app.api.v1.endpoints.preview_runtime._resolve_project", new_callable=AsyncMock, return_value=dummy_project), \
             patch("app.api.v1.endpoints.preview_runtime.preview_runtime_manager.check_health", new_callable=AsyncMock) as mock_health:
            mock_health.return_value = (False, "Application runtime unavailable on port 8001.", {})
            
            resp = await client.get("/api/v1/projects/5ec6a638-4520-4c14-ad8b-b9d1aaa0df6c/runtime/status")
            assert resp.status_code == 200
            data = resp.json()
            assert data["status"] == "UNAVAILABLE"
            assert data["port"] == 8001
            assert data["is_healthy"] is False
