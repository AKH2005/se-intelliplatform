"""Integration tests for Code Studio REST API endpoints."""

import io
import uuid
import zipfile
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.code_generation.contracts import (
    CodeGenerationOutput,
    CodeGenerationPlan,
    FileType,
    GeneratedFile,
    PlannedFile,
)
from app.core.security import create_access_token
from app.models.development_version import DevelopmentVersion, DevelopmentVersionStatus
from app.models.project import Project, ProjectStatus
from app.models.user import User
from app.models.workflow_execution import WorkflowExecution, WorkflowExecutionStatus


def _make_code_output(gen_files: list[GeneratedFile]) -> CodeGenerationOutput:
    planned = [
        PlannedFile(path=f.path, purpose=f"Test file {f.path}", file_type=FileType.SOURCE)
        for f in gen_files
    ]
    plan = CodeGenerationPlan(
        files=planned,
        rationale="Integration test generation plan rationale.",
    )
    return CodeGenerationOutput(
        plan=plan,
        generated_files=gen_files,
        total_files=len(gen_files),
        total_size_bytes=sum(f.size_bytes for f in gen_files),
        summary="Test generated files output summary.",
    )


async def _seed_test_project_with_version(
    db_session: AsyncSession,
    owner_id: uuid.UUID | None = None,
) -> tuple[Project, DevelopmentVersion]:
    proj = Project(
        name="Integration Studio Project",
        slug=f"studio-proj-{uuid.uuid4().hex[:8]}",
        status=ProjectStatus.IN_PROGRESS,
        owner_id=owner_id,
    )
    db_session.add(proj)
    await db_session.commit()

    main_py = "def run():\n    return 'initial v1'\n"
    readme_md = "# Studio Project\nDocumentation.\n"
    gen_files = [
        GeneratedFile(path="app/main.py", content=main_py, size_bytes=len(main_py), language="python"),
        GeneratedFile(path="README.md", content=readme_md, size_bytes=len(readme_md), language="markdown"),
    ]
    code_out = _make_code_output(gen_files)

    wf_id = uuid.uuid4()
    wf = WorkflowExecution(
        workflow_execution_id=wf_id,
        project_id=proj.id,
        workflow_id="code-generation",
        workflow_version="1.0.0",
        status=WorkflowExecutionStatus.COMPLETED,
        artifacts={"code-generation": code_out.model_dump(mode="json")},
    )
    db_session.add(wf)

    v1_id = uuid.uuid4()
    v1 = DevelopmentVersion(
        id=v1_id,
        project_id=proj.id,
        version_number=1,
        workflow_execution_id=wf_id,
        artifact_key="code-generation",
        status=DevelopmentVersionStatus.VERIFIED,
        content_hash="hash_v1",
        manifest_hash="man_v1",
        file_count=2,
        total_size_bytes=len(main_py) + len(readme_md),
        files_manifest=[
            {"path": "app/main.py", "size_bytes": len(main_py), "language": "python"},
            {"path": "README.md", "size_bytes": len(readme_md), "language": "markdown"},
        ],
    )
    db_session.add(v1)
    proj.settings = {"active_version_id": str(v1_id)}
    await db_session.commit()
    return proj, v1


@pytest.mark.asyncio
async def test_get_file_tree_empty_and_populated(client: AsyncClient, db_session: AsyncSession):
    """GET /api/v1/projects/{id}/files returns empty state or full hierarchy."""
    # 1. Empty project
    empty_proj = Project(name="Empty Proj", slug="empty-test", status=ProjectStatus.DRAFT)
    db_session.add(empty_proj)
    await db_session.commit()

    r_empty = await client.get(f"/api/v1/projects/{empty_proj.id}/files")
    assert r_empty.status_code == 200
    d_empty = r_empty.json()
    assert d_empty["has_generated_code"] is False
    assert d_empty["total_files"] == 0
    assert d_empty["root_nodes"] == []

    # 2. Populated project
    proj, v1 = await _seed_test_project_with_version(db_session)
    r_pop = await client.get(f"/api/v1/projects/{proj.id}/files")
    assert r_pop.status_code == 200
    d_pop = r_pop.json()
    assert d_pop["has_generated_code"] is True
    assert d_pop["version_number"] == 1
    assert d_pop["total_files"] == 2
    assert len(d_pop["root_nodes"]) == 2  # app (dir) and README.md (file)


@pytest.mark.asyncio
async def test_get_file_content_success_and_errors(client: AsyncClient, db_session: AsyncSession):
    """GET /api/v1/projects/{id}/files/{path} retrieves file or returns appropriate error."""
    proj, v1 = await _seed_test_project_with_version(db_session)

    # Success
    r = await client.get(f"/api/v1/projects/{proj.id}/files/app/main.py")
    assert r.status_code == 200
    data = r.json()
    assert data["path"] == "app/main.py"
    assert data["language"] == "python"
    assert "initial v1" in data["content"]
    assert data["version_number"] == 1

    # Missing file -> 404
    r_missing = await client.get(f"/api/v1/projects/{proj.id}/files/nonexistent.ts")
    assert r_missing.status_code == 404

    # Traversal -> 422
    r_trav = await client.get(f"/api/v1/projects/{proj.id}/files/app%2F..%2F..%2Fsecret.py")
    assert r_trav.status_code == 422


@pytest.mark.asyncio
async def test_save_file_and_verify_persistence_and_export(client: AsyncClient, db_session: AsyncSession):
    """Full lifecycle: save file, verify version created, verify persistence, and verify ZIP download."""
    proj, v1 = await _seed_test_project_with_version(db_session)

    # 1. Edit app/main.py
    new_code = "def run():\n    return 'updated v2 code studio'\n"
    save_payload = {
        "content": new_code,
        "parent_version_id": str(v1.id),
        "reason": "Updated run logic via Code Studio integration test",
    }
    r_save = await client.put(f"/api/v1/projects/{proj.id}/files/app/main.py", json=save_payload)
    assert r_save.status_code == 200
    save_data = r_save.json()
    assert save_data["success"] is True
    assert save_data["version_number"] == 2
    assert save_data["validation"]["status"] == "PASSED"
    new_v_id = save_data["version_id"]

    # 2. Re-read the file: verified that change persists
    r_read = await client.get(f"/api/v1/projects/{proj.id}/files/app/main.py")
    assert r_read.status_code == 200
    read_data = r_read.json()
    assert read_data["content"] == new_code
    assert read_data["version_number"] == 2

    # 3. Verify unrelated file is preserved in the active tree
    r_readme = await client.get(f"/api/v1/projects/{proj.id}/files/README.md")
    assert r_readme.status_code == 200
    assert "# Studio Project" in r_readme.json()["content"]

    # 4. Verify ZIP download reflects the new version with edited code
    r_zip = await client.get(f"/api/v1/projects/{proj.id}/download")
    assert r_zip.status_code == 200
    assert r_zip.headers["content-type"] == "application/zip"

    with zipfile.ZipFile(io.BytesIO(r_zip.content), "r") as zf:
        namelist = zf.namelist()
        assert "app/main.py" in namelist
        assert "README.md" in namelist
        saved_zip_content = zf.read("app/main.py").decode("utf-8")
        assert saved_zip_content == new_code


@pytest.mark.asyncio
async def test_save_concurrency_conflict_returns_409(client: AsyncClient, db_session: AsyncSession):
    """PUT with stale parent_version_id returns 409 Conflict."""
    proj, v1 = await _seed_test_project_with_version(db_session)

    # First valid save -> advances to v2
    save1 = {
        "content": "def run():\n    return 'v2'\n",
        "parent_version_id": str(v1.id),
    }
    r1 = await client.put(f"/api/v1/projects/{proj.id}/files/app/main.py", json=save1)
    assert r1.status_code == 200

    # Second save attempts to use v1 (stale)
    save_stale = {
        "content": "def run():\n    return 'stale'\n",
        "parent_version_id": str(v1.id),
    }
    r_conflict = await client.put(f"/api/v1/projects/{proj.id}/files/app/main.py", json=save_stale)
    assert r_conflict.status_code == 409
    assert "Version conflict" in r_conflict.json()["detail"]


@pytest.mark.asyncio
async def test_save_syntax_error_returns_422_without_version_advance(client: AsyncClient, db_session: AsyncSession):
    """Saving Python code with syntax error returns 422 and does not advance version."""
    proj, v1 = await _seed_test_project_with_version(db_session)

    broken_payload = {
        "content": "def syntax_broken(:\n    return False",
        "parent_version_id": str(v1.id),
    }
    r_err = await client.put(f"/api/v1/projects/{proj.id}/files/app/main.py", json=broken_payload)
    assert r_err.status_code == 422
    assert "Validation failed" in r_err.json()["detail"]

    # Active version remains v1 with original content
    r_active = await client.get(f"/api/v1/projects/{proj.id}/files/app/main.py")
    assert r_active.status_code == 200
    assert "initial v1" in r_active.json()["content"]
    assert r_active.json()["version_number"] == 1


@pytest.mark.asyncio
async def test_authorization_prevents_unauthorized_access(client: AsyncClient, db_session: AsyncSession):
    """Project owned by User A cannot be accessed or modified by User B."""
    user_a = User(id=uuid.uuid4(), name="User A", email="user_a@test.com", hashed_password="pw", is_active=True)
    user_b = User(id=uuid.uuid4(), name="User B", email="user_b@test.com", hashed_password="pw", is_active=True)
    db_session.add_all([user_a, user_b])
    await db_session.commit()

    proj, v1 = await _seed_test_project_with_version(db_session, owner_id=user_a.id)

    token_b = create_access_token(data={"sub": str(user_b.id)})
    headers_b = {"Authorization": f"Bearer {token_b}"}

    # User B reading files tree -> 403
    r_tree = await client.get(f"/api/v1/projects/{proj.id}/files", headers=headers_b)
    assert r_tree.status_code == 403

    # User B reading file content -> 403
    r_content = await client.get(f"/api/v1/projects/{proj.id}/files/app/main.py", headers=headers_b)
    assert r_content.status_code == 403

    # User B saving file -> 403
    save_payload = {"content": "print('exploit')", "parent_version_id": str(v1.id)}
    r_save = await client.put(f"/api/v1/projects/{proj.id}/files/app/main.py", json=save_payload, headers=headers_b)
    assert r_save.status_code == 403


@pytest.mark.asyncio
async def test_fullstack_project_file_tree_content_and_download(client: AsyncClient, db_session: AsyncSession):
    """Full-stack project exposes frontend and backend in file tree, content endpoint, and ZIP package."""
    proj = Project(
        name="Fullstack React Task Manager",
        slug=f"fullstack-proj-{uuid.uuid4().hex[:8]}",
        status=ProjectStatus.IN_PROGRESS,
    )
    db_session.add(proj)
    await db_session.commit()

    pkg_json = '{\n  "name": "minitask-frontend",\n  "dependencies": { "react": "^18.3.1" }\n}'
    app_tsx = "import React from 'react';\nexport default function App() { return <div>Tasks</div>; }\n"
    main_py = "from fastapi import FastAPI\napp = FastAPI()\n"
    readme_md = "# Fullstack Task Manager\nSetup instructions.\n"

    gen_files = [
        GeneratedFile(path="frontend/package.json", content=pkg_json, size_bytes=len(pkg_json), language="json"),
        GeneratedFile(path="frontend/src/App.tsx", content=app_tsx, size_bytes=len(app_tsx), language="typescript"),
        GeneratedFile(path="backend/app/main.py", content=main_py, size_bytes=len(main_py), language="python"),
        GeneratedFile(path="README.md", content=readme_md, size_bytes=len(readme_md), language="markdown"),
    ]
    code_out = _make_code_output(gen_files)

    wf_id = uuid.uuid4()
    wf = WorkflowExecution(
        workflow_execution_id=wf_id,
        project_id=proj.id,
        workflow_id="code-generation",
        workflow_version="1.0.0",
        status=WorkflowExecutionStatus.COMPLETED,
        artifacts={"code-generation": code_out.model_dump(mode="json")},
    )
    db_session.add(wf)

    v1_id = uuid.uuid4()
    v1 = DevelopmentVersion(
        id=v1_id,
        project_id=proj.id,
        version_number=1,
        workflow_execution_id=wf_id,
        artifact_key="code-generation",
        status=DevelopmentVersionStatus.VERIFIED,
        content_hash="hash_fs_v1",
        manifest_hash="man_fs_v1",
        file_count=4,
        total_size_bytes=sum(f.size_bytes for f in gen_files),
        files_manifest=[
            {"path": f.path, "size_bytes": f.size_bytes, "language": f.language}
            for f in gen_files
        ],
    )
    db_session.add(v1)
    proj.settings = {"active_version_id": str(v1_id)}
    await db_session.commit()

    # 1. Test File Tree returns frontend and backend directories
    r_tree = await client.get(f"/api/v1/projects/{proj.id}/files")
    assert r_tree.status_code == 200
    data = r_tree.json()
    assert data["has_generated_code"] is True
    assert data["total_files"] == 4

    dir_names = [n["name"] for n in data["root_nodes"] if n["type"] == "directory"]
    assert "frontend" in dir_names
    assert "backend" in dir_names

    # 2. Test File Content for frontend/src/App.tsx correctly identifies language
    r_file = await client.get(f"/api/v1/projects/{proj.id}/files/frontend/src/App.tsx")
    assert r_file.status_code == 200
    file_data = r_file.json()
    assert file_data["path"] == "frontend/src/App.tsx"
    assert file_data["name"] == "App.tsx"
    assert file_data["language"] == "typescript"
    assert "export default function App" in file_data["content"]

    # 3. Test File Content for frontend/package.json
    r_pkg = await client.get(f"/api/v1/projects/{proj.id}/files/frontend/package.json")
    assert r_pkg.status_code == 200
    assert r_pkg.json()["language"] == "json"

    # 4. Test Project ZIP download packages both frontend and backend
    r_zip = await client.get(f"/api/v1/projects/{proj.id}/download")
    assert r_zip.status_code == 200
    assert r_zip.headers["content-type"] == "application/zip"

    with zipfile.ZipFile(io.BytesIO(r_zip.content)) as zf:
        namelist = zf.namelist()
        assert any("frontend/package.json" in name for name in namelist)
        assert any("frontend/src/App.tsx" in name for name in namelist)
        assert any("backend/app/main.py" in name for name in namelist)
        assert any("README.md" in name for name in namelist)
