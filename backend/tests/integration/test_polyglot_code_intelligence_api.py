"""Integration tests for Phase 14 Polyglot Code Intelligence REST API."""

import uuid
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.development_version import DevelopmentVersion, DevelopmentVersionStatus
from app.models.project import Project, ProjectStatus


async def _create_test_project_with_polyglot_version(
    db_session: AsyncSession,
    name: str = "Polyglot Intelligence Project",
) -> tuple[Project, DevelopmentVersion]:
    project = Project(
        name=name,
        slug=f"polyglot-proj-{uuid.uuid4().hex[:8]}",
        status=ProjectStatus.IN_PROGRESS,
        settings={},
    )
    db_session.add(project)
    await db_session.flush()

    files = [
        {
            "path": "backend/app/main.py",
            "content": "from app.service import UserService\n\ndef run():\n    return UserService().get()\n",
        },
        {
            "path": "backend/app/service.py",
            "content": "class UserService:\n    def get(self):\n        return 'user'\n",
        },
        {
            "path": "frontend/src/api.ts",
            "content": "import { formatUser } from './utils';\nexport interface UserDto { id: string; }\nexport function fetchUser(): UserDto { return formatUser(); }\n",
        },
        {
            "path": "frontend/src/utils.js",
            "content": "export function formatUser() { return { id: 'u1' }; }\n",
        },
        {
            "path": "services/auth/AuthService.java",
            "content": "package com.example.auth;\n\npublic class AuthService {\n    public boolean authenticate(String token) {\n        return token != null;\n    }\n}\n",
        },
    ]

    v1 = DevelopmentVersion(
        project_id=project.id,
        version_number=1,
        artifact_key="art-polyglot-v1",
        status=DevelopmentVersionStatus.VERIFIED,
        content_hash="hash-polyglot-v1",
        manifest_hash="m-polyglot-v1",
        file_count=len(files),
        total_size_bytes=500,
        files_manifest=files,
        source_reason="Initial polyglot codebase",
        created_by="system",
        verification_summary={"verification_status": "PASSED", "is_verified": True},
    )
    db_session.add(v1)
    project.settings = {"active_version_id": str(v1.id)}
    await db_session.commit()
    await db_session.refresh(v1)
    return project, v1


@pytest.mark.asyncio
async def test_get_language_inventory_api(
    client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    """GET /api/v1/projects/{project_id}/code-intelligence/languages returns counts and percentages."""
    project, _ = await _create_test_project_with_polyglot_version(db_session)

    resp = await client.get(f"/api/v1/projects/{project.id}/code-intelligence/languages")
    assert resp.status_code == 200
    data = resp.json()

    assert data["project_id"] == str(project.id)
    assert data["total_files"] == 5
    assert "python" in data["counts"]
    assert "typescript" in data["counts"]
    assert "javascript" in data["counts"]
    assert "java" in data["counts"]
    assert data["counts"]["python"] == 2
    assert data["counts"]["typescript"] == 1
    assert data["counts"]["javascript"] == 1
    assert data["counts"]["java"] == 1


@pytest.mark.asyncio
async def test_get_code_intelligence_summary_api(
    client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    """GET /api/v1/projects/{project_id}/code-intelligence/summary returns high-level metrics."""
    project, v1 = await _create_test_project_with_polyglot_version(db_session)

    resp = await client.get(f"/api/v1/projects/{project.id}/code-intelligence/summary")
    assert resp.status_code == 200
    data = resp.json()

    assert data["project_id"] == str(project.id)
    assert data["version_id"] == str(v1.id)
    assert data["total_files"] == 5
    assert data["total_symbols"] > 0
    assert data["total_edges"] > 0
    assert data["language_breakdown"]["python"] == 2
    assert data["language_breakdown"]["typescript"] == 1


@pytest.mark.asyncio
async def test_get_dependency_graph_api(
    client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    """GET /api/v1/projects/{project_id}/code-intelligence/graph returns forward and reverse adjacencies."""
    project, _ = await _create_test_project_with_polyglot_version(db_session)

    resp = await client.get(f"/api/v1/projects/{project.id}/code-intelligence/graph")
    assert resp.status_code == 200
    data = resp.json()

    assert data["project_id"] == str(project.id)
    assert data["files_count"] == 5
    fwd = data["forward_adjacency"]
    rev = data["reverse_adjacency"]

    assert isinstance(fwd, dict)
    assert isinstance(rev, dict)
    assert "backend/app/main.py" in fwd


@pytest.mark.asyncio
async def test_get_file_code_intelligence_api(
    client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    """GET /api/v1/projects/{project_id}/code-intelligence/file returns detailed symbols and imports."""
    project, _ = await _create_test_project_with_polyglot_version(db_session)

    resp = await client.get(
        f"/api/v1/projects/{project.id}/code-intelligence/file",
        params={"file_path": "frontend/src/api.ts"},
    )
    assert resp.status_code == 200
    data = resp.json()

    assert data["file_path"] == "frontend/src/api.ts"
    assert data["language"] == "typescript"
    assert len(data["symbols"]) > 0
    assert any(s["name"] == "UserDto" for s in data["symbols"])
    assert any(s["name"] == "fetchUser" for s in data["symbols"])


@pytest.mark.asyncio
async def test_project_isolation_and_not_found(
    client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    """Ensure strict project isolation and 404 error handling."""
    proj_a, v_a = await _create_test_project_with_polyglot_version(db_session, "Project A")
    proj_b, _ = await _create_test_project_with_polyglot_version(db_session, "Project B")

    # Non-existent project returns 404
    random_id = uuid.uuid4()
    resp = await client.get(f"/api/v1/projects/{random_id}/code-intelligence/summary")
    assert resp.status_code == 404

    # Version belonging to Project A queried under Project B returns 404
    resp_cross = await client.get(
        f"/api/v1/projects/{proj_b.id}/code-intelligence/summary",
        params={"version_id": str(v_a.id)},
    )
    assert resp_cross.status_code == 404

    # File not present in project returns 404
    resp_file = await client.get(
        f"/api/v1/projects/{proj_a.id}/code-intelligence/file",
        params={"file_path": "non/existent/File.java"},
    )
    assert resp_file.status_code == 404
