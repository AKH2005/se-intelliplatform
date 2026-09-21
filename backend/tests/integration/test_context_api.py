"""Integration Tests for Project Context & Snapshots REST API."""

import uuid
import pytest
from httpx import AsyncClient


@pytest.fixture
async def project_id(client: AsyncClient) -> str:
    """Create a project and return its ID string."""
    res = await client.post(
        "/api/v1/projects",
        json={"name": "Context Testing Core", "slug": f"ctx-test-{uuid.uuid4().hex[:8]}"},
    )
    assert res.status_code == 201
    return res.json()["id"]


@pytest.mark.asyncio
async def test_get_project_context_empty_and_populated(
    client: AsyncClient,
    project_id: str,
):
    """Verify GET /api/v1/projects/{project_id}/context returns canonical structure and statistics."""
    # 1. Empty project
    res1 = await client.get(f"/api/v1/projects/{project_id}/context")
    assert res1.status_code == 200
    ctx1 = res1.json()
    assert ctx1["project"]["id"] == project_id
    assert len(ctx1["requirements"]) == 0
    assert ctx1["statistics"]["total_requirements"] == 0
    assert ctx1["statistics"]["active_requirements"] == 0
    assert ctx1["statistics"]["completion_percentage"] == 0.0
    assert "generated_at" in ctx1
    assert "X-Correlation-ID" in res1.headers

    # 2. Add requirements
    await client.post(
        f"/api/v1/projects/{project_id}/requirements",
        json={"title": "R1", "description": "D1", "status": "IMPLEMENTED"},
    )
    await client.post(
        f"/api/v1/projects/{project_id}/requirements",
        json={"title": "R2", "description": "D2", "status": "DRAFT"},
    )

    res2 = await client.get(f"/api/v1/projects/{project_id}/context")
    assert res2.status_code == 200
    ctx2 = res2.json()
    assert len(ctx2["requirements"]) == 2
    assert ctx2["statistics"]["active_requirements"] == 2
    # 1 out of 2 implemented -> 50.0%
    assert ctx2["statistics"]["completion_percentage"] == 50.0


@pytest.mark.asyncio
async def test_get_context_non_existent_project_returns_404(client: AsyncClient):
    """Verify non-existent project returns RFC 7807 404 Problem Details."""
    fake_id = str(uuid.uuid4())
    res = await client.get(f"/api/v1/projects/{fake_id}/context")
    assert res.status_code == 404
    problem = res.json()
    assert problem["status"] == 404
    assert problem["title"] == "Resource Not Found"
    assert fake_id in problem["detail"]


@pytest.mark.asyncio
async def test_snapshot_lifecycle_api(client: AsyncClient, project_id: str):
    """Verify creating immutable snapshots, sequential versions (v1 -> v2), and retrieval."""
    # 1. Create first requirement and snapshot v1
    await client.post(
        f"/api/v1/projects/{project_id}/requirements",
        json={"title": "Requirement Alpha", "description": "Desc Alpha"},
    )
    snap1_res = await client.post(
        f"/api/v1/projects/{project_id}/context/snapshots",
        json={"summary": "Milestone Alpha Snapshot"},
    )
    assert snap1_res.status_code == 201
    snap1_data = snap1_res.json()
    assert snap1_data["version"] == 1
    assert snap1_data["project_id"] == project_id
    assert snap1_data["summary"] == "Milestone Alpha Snapshot"
    assert snap1_data["context_data"]["context_version"] == 1
    assert snap1_data["context_data"]["statistics"]["total_requirements"] == 1

    # 2. Add second requirement and snapshot v2
    await client.post(
        f"/api/v1/projects/{project_id}/requirements",
        json={"title": "Requirement Beta", "description": "Desc Beta"},
    )
    snap2_res = await client.post(
        f"/api/v1/projects/{project_id}/context/snapshots",
        json={"summary": "Milestone Beta Snapshot"},
    )
    assert snap2_res.status_code == 201
    snap2_data = snap2_res.json()
    assert snap2_data["version"] == 2
    assert snap2_data["context_data"]["statistics"]["total_requirements"] == 2

    # 3. List snapshots returns [v2, v1]
    list_res = await client.get(f"/api/v1/projects/{project_id}/context/snapshots")
    assert list_res.status_code == 200
    snapshots = list_res.json()
    assert len(snapshots) == 2
    assert snapshots[0]["version"] == 2
    assert snapshots[1]["version"] == 1

    # 4. Fetch specific historical snapshot v1
    get_v1 = await client.get(f"/api/v1/projects/{project_id}/context/snapshots/1")
    assert get_v1.status_code == 200
    assert get_v1.json()["version"] == 1
    assert get_v1.json()["context_data"]["statistics"]["total_requirements"] == 1

    # 5. Fetch non-existent snapshot version returns 404
    not_found_res = await client.get(f"/api/v1/projects/{project_id}/context/snapshots/999")
    assert not_found_res.status_code == 404
    assert not_found_res.json()["title"] == "Resource Not Found"
