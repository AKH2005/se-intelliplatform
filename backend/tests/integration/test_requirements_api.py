"""Integration Tests for Requirements REST API."""

import uuid
import pytest
from httpx import AsyncClient


@pytest.fixture
async def project_id(client: AsyncClient) -> str:
    """Create a project and return its ID string."""
    res = await client.post(
        "/api/v1/projects",
        json={"name": "Requirements Testing Project", "slug": f"req-test-{uuid.uuid4().hex[:8]}"},
    )
    assert res.status_code == 201
    return res.json()["id"]


@pytest.mark.asyncio
async def test_create_requirement_success(client: AsyncClient, project_id: str):
    """Verify POST /api/v1/projects/{project_id}/requirements returns 201 with schema."""
    payload = {
        "title": "OAuth2 PKCE Flow",
        "description": "Native mobile client authentication support.",
        "type": "FUNCTIONAL",
        "priority": "HIGH",
        "status": "DRAFT",
    }
    res = await client.post(f"/api/v1/projects/{project_id}/requirements", json=payload)
    assert res.status_code == 201
    data = res.json()
    assert data["title"] == payload["title"]
    assert data["description"] == payload["description"]
    assert data["type"] == "FUNCTIONAL"
    assert data["priority"] == "HIGH"
    assert data["status"] == "DRAFT"
    assert data["project_id"] == project_id
    assert data["is_archived"] is False
    assert "id" in data
    assert "created_at" in data
    assert "updated_at" in data


@pytest.mark.asyncio
async def test_create_requirement_validation_failure_returns_422(
    client: AsyncClient,
    project_id: str,
):
    """Verify invalid requirement payload returns RFC 7807 422 Problem Details."""
    invalid_payload = {
        "title": "",  # Empty title violates constraint
        "description": "Valid desc",
    }
    res = await client.post(f"/api/v1/projects/{project_id}/requirements", json=invalid_payload)
    assert res.status_code == 422
    problem = res.json()
    assert problem["status"] == 422
    assert problem["title"] == "Validation Error"
    assert "validation_errors" in problem
    assert "trace_id" in problem


@pytest.mark.asyncio
async def test_create_requirement_non_existent_project_returns_404(client: AsyncClient):
    """Verify creating requirement for non-existent project returns RFC 7807 404 Problem Details."""
    fake_project_id = str(uuid.uuid4())
    payload = {
        "title": "Valid Title",
        "description": "Valid Description",
    }
    res = await client.post(f"/api/v1/projects/{fake_project_id}/requirements", json=payload)
    assert res.status_code == 404
    problem = res.json()
    assert problem["status"] == 404
    assert problem["title"] == "Resource Not Found"
    assert fake_project_id in problem["detail"]


@pytest.mark.asyncio
async def test_get_and_list_requirements(client: AsyncClient, project_id: str):
    """Verify listing and retrieving requirements with pagination and filtering."""
    # Create two requirements
    r1 = await client.post(
        f"/api/v1/projects/{project_id}/requirements",
        json={"title": "Req 1", "description": "Desc 1", "type": "FUNCTIONAL"},
    )
    r2 = await client.post(
        f"/api/v1/projects/{project_id}/requirements",
        json={"title": "Req 2", "description": "Desc 2", "type": "NON_FUNCTIONAL"},
    )
    req1_id = r1.json()["id"]

    # Get single requirement
    get_res = await client.get(f"/api/v1/projects/{project_id}/requirements/{req1_id}")
    assert get_res.status_code == 200
    assert get_res.json()["title"] == "Req 1"

    # List all requirements
    list_res = await client.get(f"/api/v1/projects/{project_id}/requirements")
    assert list_res.status_code == 200
    items = list_res.json()
    assert len(items) >= 2

    # Filter by type
    filter_res = await client.get(f"/api/v1/projects/{project_id}/requirements?type=NON_FUNCTIONAL")
    assert filter_res.status_code == 200
    filtered_items = filter_res.json()
    assert len(filtered_items) == 1
    assert filtered_items[0]["type"] == "NON_FUNCTIONAL"


@pytest.mark.asyncio
async def test_update_requirement(client: AsyncClient, project_id: str):
    """Verify PATCH /api/v1/projects/{project_id}/requirements/{req_id} updates fields."""
    r = await client.post(
        f"/api/v1/projects/{project_id}/requirements",
        json={"title": "Original Title", "description": "Original Desc"},
    )
    req_id = r.json()["id"]

    patch_res = await client.patch(
        f"/api/v1/projects/{project_id}/requirements/{req_id}",
        json={"title": "Patched Title", "status": "APPROVED"},
    )
    assert patch_res.status_code == 200
    data = patch_res.json()
    assert data["title"] == "Patched Title"
    assert data["status"] == "APPROVED"
    assert data["description"] == "Original Desc"


@pytest.mark.asyncio
async def test_delete_requirement_archives_record(client: AsyncClient, project_id: str):
    """Verify DELETE /api/v1/projects/{project_id}/requirements/{req_id} soft-archives the record."""
    r = await client.post(
        f"/api/v1/projects/{project_id}/requirements",
        json={"title": "To Soft Delete", "description": "Must be preserved"},
    )
    req_id = r.json()["id"]

    del_res = await client.delete(f"/api/v1/projects/{project_id}/requirements/{req_id}")
    assert del_res.status_code == 200
    assert del_res.json()["is_archived"] is True

    # Record still exists and is retrievable
    get_res = await client.get(f"/api/v1/projects/{project_id}/requirements/{req_id}")
    assert get_res.status_code == 200
    assert get_res.json()["is_archived"] is True
