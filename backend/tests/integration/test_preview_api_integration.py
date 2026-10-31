"""Integration and Regression Tests for Live Preview APIs, Root Routing, & Project Isolation."""

import pytest
import uuid
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.services.preview_api_service import PreviewApiService
from app.api.v1.endpoints.preview_runtime import inject_preview_bridge


@pytest.mark.asyncio
async def test_preview_api_service_crud_and_isolation(db_session: AsyncSession):
    """Verify task CRUD operations and strict project isolation."""
    proj_a = str(uuid.uuid4())
    proj_b = str(uuid.uuid4())

    # Project A gets starter tasks
    tasks_a = await PreviewApiService.get_tasks(proj_a, session=db_session)
    assert len(tasks_a) >= 1
    assert all(t["project_id"] == proj_a for t in tasks_a)

    # Create task in Project A
    new_task_a = await PreviewApiService.create_task(
        {"title": "Implement Feature A", "priority": "HIGH", "status": "PENDING"},
        proj_a,
        session=db_session,
    )
    assert new_task_a["id"] > 0
    assert new_task_a["project_id"] == proj_a

    # Project B should NOT see Project A's task
    tasks_b = await PreviewApiService.get_tasks(proj_b, session=db_session)
    assert not any(t["id"] == new_task_a["id"] for t in tasks_b)

    # Update task in Project A
    updated = await PreviewApiService.update_task(new_task_a["id"], {"status": "COMPLETED"}, proj_a, session=db_session)
    assert updated is not None
    assert updated["status"] == "COMPLETED"

    # Delete task in Project A
    deleted = await PreviewApiService.delete_task(new_task_a["id"], proj_a, session=db_session)
    assert deleted is True

    # Confirm deletion
    assert await PreviewApiService.get_task(new_task_a["id"], proj_a, session=db_session) is None


@pytest.mark.asyncio
async def test_preview_api_service_scores_and_metrics(db_session: AsyncSession):
    """Verify Arcade/Snake Game scores and Executive Analytics metrics."""
    proj_id = str(uuid.uuid4())

    # Add score
    score_res = await PreviewApiService.add_score(score=450, player_name="TestArcade", project_id=proj_id, session=db_session)
    assert score_res["status"] == "SAVED"
    assert score_res["score"] == 450

    # Get scores
    scores = await PreviewApiService.get_scores(proj_id, session=db_session)
    assert any(s["score"] == 450 for s in scores)

    # Get metrics
    metrics = PreviewApiService.get_analytics_metrics(proj_id)
    assert "summary" in metrics
    assert "arr" in metrics["summary"]
    assert "kpis" in metrics
    assert len(metrics["kpis"]) > 0


@pytest.mark.asyncio
async def test_preview_root_compatibility_routes(client: AsyncClient):
    """Verify that root-level relative calls (/tasks, /api/tasks, /scores, /metrics) do not 404."""
    proj_id = f"proj-root-{uuid.uuid4().hex[:8]}"
    # GET /tasks with Referer
    res = await client.get(
        "/tasks",
        headers={"Referer": f"http://test/api/v1/projects/{proj_id}/runtime/preview?app=taskflow"}
    )
    assert res.status_code == 200
    tasks = res.json()
    assert isinstance(tasks, list)
    assert len(tasks) > 0

    # GET /api/tasks with X-Project-ID
    res = await client.get("/api/tasks", headers={"X-Project-ID": proj_id})
    assert res.status_code == 200

    # POST /tasks
    res = await client.post(
        "/tasks",
        headers={"X-Project-ID": proj_id},
        json={"title": "Root Task Test", "priority": "MEDIUM", "status": "PENDING"}
    )
    assert res.status_code == 201
    created = res.json()
    assert created["title"] == "Root Task Test"

    # PUT /tasks/{id}
    res = await client.put(
        f"/tasks/{created['id']}",
        headers={"X-Project-ID": proj_id},
        json={"status": "COMPLETED"}
    )
    assert res.status_code == 200
    assert res.json()["status"] == "COMPLETED"

    # DELETE /tasks/{id}
    res = await client.delete(f"/tasks/{created['id']}", headers={"X-Project-ID": proj_id})
    assert res.status_code == 200
    assert res.json()["status"] == "DELETED"

    # GET /scores
    res = await client.get("/scores")
    assert res.status_code == 200
    assert isinstance(res.json(), list)

    # POST /scores
    res = await client.post("/scores", json={"score": 210, "player_name": "TestPlayer"})
    assert res.status_code == 201

    # GET /metrics and /api/metrics
    res = await client.get("/metrics")
    assert res.status_code == 200
    assert "summary" in res.json()

    res = await client.get("/api/metrics")
    assert res.status_code == 200

    # GET /api/auth/me
    res = await client.get("/api/auth/me")
    assert res.status_code == 200
    assert res.json()["authenticated"] is True


@pytest.mark.asyncio
async def test_preview_html_bridge_injection():
    """Verify inject_preview_bridge produces valid script defining project environment."""
    test_html = "<!DOCTYPE html><html><head><title>Test App</title></head><body><h1>Hello</h1></body></html>"
    test_pid = "550e8400-e29b-41d4-a716-446655440000"
    test_tok = "test-preview-token-12345"

    injected = inject_preview_bridge(test_html, test_pid, test_tok)
    assert "__SE_PREVIEW_BRIDGE__" in injected
    assert f'window.__PREVIEW_PROJECT_ID__ = "{test_pid}"' in injected
    assert f'window.__PREVIEW_TOKEN__ = "{test_tok}"' in injected
    assert f'window.__PREVIEW_API_BASE__ = "/api/v1/projects/{test_pid}/runtime/api"' in injected
    assert "window.fetch = function" in injected

