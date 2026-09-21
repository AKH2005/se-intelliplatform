"""Integration Tests for Projects CRUD API."""

import uuid
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_create_project_success(client: AsyncClient):
    """Verify successfully creating a project returns 201 Created and response schema."""
    payload = {
        "name": "Cloud Native Platform",
        "slug": "cloud-native-platform",
        "description": "Cloud native microservices architecture",
        "status": "DRAFT",
        "settings": {"cloud": "aws"},
    }
    response = await client.post("/api/v1/projects", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == payload["name"]
    assert data["slug"] == payload["slug"]
    assert data["status"] == "DRAFT"
    assert data["settings"] == {"cloud": "aws"}
    assert "id" in data
    assert "created_at" in data
    assert "updated_at" in data


@pytest.mark.asyncio
async def test_create_project_duplicate_slug_returns_conflict(client: AsyncClient):
    """Verify duplicate slug returns RFC 7807 409 Conflict."""
    payload = {
        "name": "Project Alpha",
        "slug": "project-alpha",
    }
    # First creation
    res1 = await client.post("/api/v1/projects", json=payload)
    assert res1.status_code == 201

    # Second creation with identical slug
    res2 = await client.post("/api/v1/projects", json=payload)
    assert res2.status_code == 409
    problem = res2.json()
    assert problem["status"] == 409
    assert problem["title"] == "Resource Conflict"
    assert "already exists" in problem["detail"]
    assert "trace_id" in problem


@pytest.mark.asyncio
async def test_create_project_invalid_payload_returns_422(client: AsyncClient):
    """Verify malformed input returns RFC 7807 422 Unprocessable Entity."""
    payload = {
        "name": "",  # Empty name violates validation
        "slug": "INVALID SLUG",
    }
    response = await client.post("/api/v1/projects", json=payload)
    assert response.status_code == 422
    problem = response.json()
    assert problem["status"] == 422
    assert problem["title"] == "Validation Error"
    assert "validation_errors" in problem


@pytest.mark.asyncio
async def test_get_project_by_id_success(client: AsyncClient):
    """Verify retrieving an existing project by UUID."""
    # Create project
    create_res = await client.post(
        "/api/v1/projects",
        json={"name": "Retrieval Test", "slug": "retrieval-test"},
    )
    assert create_res.status_code == 201
    project_id = create_res.json()["id"]

    # Fetch project
    get_res = await client.get(f"/api/v1/projects/{project_id}")
    assert get_res.status_code == 200
    data = get_res.json()
    assert data["id"] == project_id
    assert data["slug"] == "retrieval-test"


@pytest.mark.asyncio
async def test_get_project_not_found(client: AsyncClient):
    """Verify non-existent project ID returns RFC 7807 404 Not Found."""
    non_existent_id = str(uuid.uuid4())
    response = await client.get(f"/api/v1/projects/{non_existent_id}")
    assert response.status_code == 404
    problem = response.json()
    assert problem["status"] == 404
    assert problem["title"] == "Resource Not Found"
    assert non_existent_id in problem["detail"]


@pytest.mark.asyncio
async def test_list_projects(client: AsyncClient):
    """Verify listing projects with pagination."""
    # Seed two projects
    await client.post("/api/v1/projects", json={"name": "P1", "slug": "project-one"})
    await client.post("/api/v1/projects", json={"name": "P2", "slug": "project-two"})

    response = await client.get("/api/v1/projects?limit=10")
    assert response.status_code == 200
    items = response.json()
    assert isinstance(items, list)
    assert len(items) >= 2


@pytest.mark.asyncio
async def test_update_project_success(client: AsyncClient):
    """Verify updating project fields via PATCH."""
    create_res = await client.post(
        "/api/v1/projects",
        json={"name": "Original Name", "slug": "orig-slug", "status": "DRAFT"},
    )
    project_id = create_res.json()["id"]

    patch_res = await client.patch(
        f"/api/v1/projects/{project_id}",
        json={"name": "Updated Name", "status": "IN_PROGRESS"},
    )
    assert patch_res.status_code == 200
    data = patch_res.json()
    assert data["name"] == "Updated Name"
    assert data["status"] == "IN_PROGRESS"
    assert data["slug"] == "orig-slug"


@pytest.mark.asyncio
async def test_archive_project_lifecycle(client: AsyncClient):
    """Verify archiving project safely sets status to ARCHIVED without deletion."""
    create_res = await client.post(
        "/api/v1/projects",
        json={"name": "To Archive", "slug": "to-archive"},
    )
    project_id = create_res.json()["id"]

    del_res = await client.delete(f"/api/v1/projects/{project_id}")
    assert del_res.status_code == 200
    assert del_res.json()["status"] == "ARCHIVED"

    # Verify project still exists in database
    get_res = await client.get(f"/api/v1/projects/{project_id}")
    assert get_res.status_code == 200
    assert get_res.json()["status"] == "ARCHIVED"
