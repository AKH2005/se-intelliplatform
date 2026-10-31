"""Unit tests for Application Preview Runtime & Port 8001 Lifecycle."""

import uuid
import pytest
from unittest.mock import AsyncMock, patch
from httpx import AsyncClient, ASGITransport

from app.core.security import create_preview_token, decode_preview_token
from app.main import create_application
from app.models.project import Project
from app.models.user import User
from app.runtime.preview_runtime_manager import PreviewRuntimeManager



@pytest.mark.asyncio
async def test_preview_runtime_manager_health_check_healthy():
    manager = PreviewRuntimeManager()
    with patch.object(manager, "_sync_http_get", return_value=(True, 200, {"status": "ok", "port": 8001})):
        healthy, msg, details = await manager.check_health()
        assert healthy is True
        assert "running on port 8001" in msg
        assert details.get("status") in ("ok", "RUNNING")


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
            assert "project_id=5ec6a638-4520-4c14-ad8b-b9d1aaa0df6c" in data["preview_url"]
            assert "app=taskflow" in data["preview_url"]
            assert data["active_mode"] == "taskflow"


@pytest.mark.asyncio
async def test_preview_runtime_status_snake_game():
    app = create_application()
    transport = ASGITransport(app=app)
    snake_project = Project(
        id=uuid.UUID("7a12b345-6789-4bcd-8ef0-123456789abc"),
        name="Snake Game Arcade",
        slug="snake-game-arcade",
        description="Retro arcade snake game with high score",
        owner_id=None,
    )
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        with patch("app.api.v1.endpoints.preview_runtime._resolve_project", new_callable=AsyncMock, return_value=snake_project), \
             patch("app.api.v1.endpoints.preview_runtime.preview_runtime_manager.check_health", new_callable=AsyncMock) as mock_health:
            mock_health.return_value = (True, "Application running on port 8001.", {})

            resp = await client.get("/api/v1/projects/7a12b345-6789-4bcd-8ef0-123456789abc/runtime/status")
            assert resp.status_code == 200
            data = resp.json()
            assert data["active_mode"] == "snake_game"
            assert "app=snake_game" in data["preview_url"]


@pytest.mark.asyncio
async def test_preview_runtime_html_endpoint():
    app = create_application()
    transport = ASGITransport(app=app)
    snake_project = Project(
        id=uuid.UUID("7a12b345-6789-4bcd-8ef0-123456789abc"),
        name="Arcade Snake",
        slug="arcade-snake",
        description="Retro game",
        owner_id=None,
    )
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        with patch("app.api.v1.endpoints.preview_runtime._resolve_project", new_callable=AsyncMock, return_value=snake_project):
            resp = await client.get("/api/v1/projects/7a12b345-6789-4bcd-8ef0-123456789abc/runtime/preview")
            assert resp.status_code == 200
            assert "text/html" in resp.headers["content-type"]
            html = resp.text
            assert "gameCanvas" in html
            assert "scoreboard" in html


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
            assert "runtime/preview" in data["preview_url"]


@pytest.mark.asyncio
async def test_create_and_decode_preview_token():
    user_id = uuid.uuid4()
    project_id = uuid.uuid4()

    token = create_preview_token(user_id=user_id, project_id=project_id, expires_minutes=15)
    assert isinstance(token, str)

    payload = decode_preview_token(token, expected_project_id=project_id)
    assert payload is not None
    assert payload["sub"] == str(user_id)
    assert payload["project_id"] == str(project_id)
    assert payload["scope"] == "preview"


@pytest.mark.asyncio
async def test_preview_token_mismatched_project_rejected():
    user_id = uuid.uuid4()
    project_a = uuid.uuid4()
    project_b = uuid.uuid4()

    token_a = create_preview_token(user_id=user_id, project_id=project_a)
    payload_b = decode_preview_token(token_a, expected_project_id=project_b)
    assert payload_b is None


@pytest.mark.asyncio
async def test_preview_token_expired_rejected():
    user_id = uuid.uuid4()
    project_id = uuid.uuid4()

    # Expired token (-1 minutes)
    token = create_preview_token(user_id=user_id, project_id=project_id, expires_minutes=-1)
    payload = decode_preview_token(token, expected_project_id=project_id)
    assert payload is None


@pytest.mark.asyncio
async def test_preview_runtime_private_project_unauthorized():
    from unittest.mock import MagicMock
    app = create_application()
    transport = ASGITransport(app=app)
    owner_id = uuid.uuid4()
    project_id = uuid.uuid4()

    dummy_project = Project(
        id=project_id,
        name="Private Snake",
        slug="private-snake",
        description="Private game",
        owner_id=owner_id,
    )

    async with AsyncClient(transport=transport, base_url="http://test") as client:
        mock_res = MagicMock()
        mock_res.scalar_one_or_none.return_value = dummy_project
        mock_db = AsyncMock()
        mock_db.execute.return_value = mock_res

        from app.api.dependencies import get_db, get_current_user_optional
        app.dependency_overrides[get_db] = lambda: mock_db
        app.dependency_overrides[get_current_user_optional] = lambda: None

        resp = await client.get(f"/api/v1/projects/{project_id}/runtime/preview")
        assert resp.status_code == 401
        assert "Authentication required" in resp.json()["detail"]
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_preview_runtime_private_project_forbidden():
    from unittest.mock import MagicMock
    app = create_application()
    transport = ASGITransport(app=app)
    owner_id = uuid.uuid4()
    other_user_id = uuid.uuid4()
    project_id = uuid.uuid4()

    dummy_project = Project(
        id=project_id,
        name="Private Snake",
        slug="private-snake",
        description="Private game",
        owner_id=owner_id,
    )
    other_user = User(
        id=other_user_id,
        email="other@example.com",
        is_active=True,
    )

    async with AsyncClient(transport=transport, base_url="http://test") as client:
        mock_res = MagicMock()
        mock_res.scalar_one_or_none.return_value = dummy_project
        mock_db = AsyncMock()
        mock_db.execute.return_value = mock_res

        from app.api.dependencies import get_db, get_current_user_optional
        app.dependency_overrides[get_db] = lambda: mock_db
        app.dependency_overrides[get_current_user_optional] = lambda: other_user

        resp = await client.get(f"/api/v1/projects/{project_id}/runtime/preview")
        assert resp.status_code == 403
        assert "do not have permission" in resp.json()["detail"]
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_preview_runtime_private_project_succeeds_with_preview_token():
    from unittest.mock import MagicMock
    app = create_application()
    transport = ASGITransport(app=app)
    owner_id = uuid.uuid4()
    project_id = uuid.uuid4()

    owner_user = User(
        id=owner_id,
        email="owner@example.com",
        is_active=True,
    )
    dummy_project = Project(
        id=project_id,
        name="Private Snake",
        slug="private-snake",
        description="Private game",
        owner_id=owner_id,
    )

    valid_preview_token = create_preview_token(user_id=owner_id, project_id=project_id, expires_minutes=15)

    async with AsyncClient(transport=transport, base_url="http://test") as client:
        mock_db = AsyncMock()
        mock_res_user = MagicMock()
        mock_res_user.scalar_one_or_none.return_value = owner_user
        mock_res_proj = MagicMock()
        mock_res_proj.scalar_one_or_none.return_value = dummy_project

        mock_db.execute.side_effect = [mock_res_user, mock_res_proj]

        from app.api.dependencies import get_db, get_current_user_optional
        app.dependency_overrides[get_db] = lambda: mock_db
        app.dependency_overrides[get_current_user_optional] = lambda: None

        resp = await client.get(f"/api/v1/projects/{project_id}/runtime/preview?app=snake_game&preview_token={valid_preview_token}")
        assert resp.status_code == 200
        assert "text/html" in resp.headers["content-type"]
        assert "frame-ancestors" in resp.headers["content-security-policy"]
        assert "gameCanvas" in resp.text
        app.dependency_overrides.clear()



@pytest.mark.asyncio
async def test_preview_runtime_status_production_mode():
    from app.core.config import settings
    app = create_application()
    transport = ASGITransport(app=app)
    project_id = uuid.uuid4()
    owner_id = uuid.uuid4()

    owner_user = User(id=owner_id, email="owner@example.com", is_active=True)
    dummy_project = Project(
        id=project_id,
        name="Snake Game Arcade",
        slug="snake-arcade",
        description="Arcade snake",
        owner_id=owner_id,
    )

    async with AsyncClient(transport=transport, base_url="http://test") as client:
        with patch.object(settings, "ENVIRONMENT", "production"), \
             patch("app.api.v1.endpoints.preview_runtime._resolve_project", new_callable=AsyncMock, return_value=dummy_project), \
             patch("app.api.v1.endpoints.preview_runtime.preview_runtime_manager.check_health", new_callable=AsyncMock) as mock_health:

            mock_health.return_value = (True, "Application running on port 443.", {"status": "RUNNING", "port": 443})
            from app.api.dependencies import get_current_user_optional
            app.dependency_overrides[get_current_user_optional] = lambda: owner_user

            resp = await client.get(f"/api/v1/projects/{project_id}/runtime/status")
            assert resp.status_code == 200
            data = resp.json()
            assert data["status"] == "RUNNING"
            assert data["port"] == 443
            assert data["is_healthy"] is True
            assert data["active_mode"] == "snake_game"
            assert data["preview_token"] is not None
            assert f"preview_token={data['preview_token']}" in data["preview_url"]
            app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_preview_runtime_modes_rendering():
    """Verify that all application modes render their specialized prototypes."""
    app = create_application()
    transport = ASGITransport(app=app)
    project_id = uuid.uuid4()

    modes_to_check = [
        ("snake_game", "gameCanvas"),
        ("taskflow", "TaskFlow"),
        ("eventhub", "EventHub"),
        ("ecommerce", "Modern E-Commerce Platform"),
        ("management", "Live Management Portal"),
    ]

    async with AsyncClient(transport=transport, base_url="http://test") as client:
        for mode, expected_text in modes_to_check:
            dummy_project = Project(
                id=project_id,
                name=f"App {mode}",
                slug=f"app-{mode}",
                description="Test preview mode",
                owner_id=None,
            )
            with patch("app.api.v1.endpoints.preview_runtime._resolve_project", new_callable=AsyncMock, return_value=dummy_project):
                resp = await client.get(f"/api/v1/projects/{project_id}/runtime/preview?app={mode}")
                assert resp.status_code == 200
                assert expected_text in resp.text



