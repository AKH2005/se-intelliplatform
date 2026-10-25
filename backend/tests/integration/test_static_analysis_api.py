"""Integration Tests for Static Analysis API Endpoints."""

import uuid
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_sandbox_executor
from app.main import app
from app.models.project import Project, ProjectStatus
from app.models.workflow_execution import WorkflowExecution, WorkflowStatus
from app.sandbox.mock_executor import MockSandboxExecutor
from tests.unit.test_sandbox import make_valid_code_output


@pytest.fixture
def mock_sandbox_executor():
    mock_exec = MockSandboxExecutor(mock_stdout="[]")
    app.dependency_overrides[get_sandbox_executor] = lambda: mock_exec
    yield mock_exec
    app.dependency_overrides.pop(get_sandbox_executor, None)


@pytest.mark.asyncio
async def test_run_static_analysis_nonexistent_project(client: AsyncClient, mock_sandbox_executor):
    project_id = uuid.uuid4()
    payload = {"project_id": str(project_id)}
    resp = await client.post(f"/api/v1/projects/{project_id}/analysis/static", json=payload)
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_run_static_analysis_no_artifact(client: AsyncClient, db_session: AsyncSession, mock_sandbox_executor):
    project = Project(
        id=uuid.uuid4(),
        name="Empty Project",
        slug="empty-project",
        status=ProjectStatus.IN_PROGRESS,
    )
    db_session.add(project)
    await db_session.commit()

    payload = {"project_id": str(project.id)}
    resp = await client.post(f"/api/v1/projects/{project.id}/analysis/static", json=payload)
    assert resp.status_code == 422
    assert "no completed workflow execution" in resp.json()["detail"].lower()


@pytest.mark.asyncio
async def test_run_static_analysis_success(
    client: AsyncClient,
    db_session: AsyncSession,
    mock_sandbox_executor,
):
    project = Project(
        id=uuid.uuid4(),
        name="Static Test Project",
        slug="static-test-project",
        status=ProjectStatus.IN_PROGRESS,
    )
    db_session.add(project)

    code_output = make_valid_code_output([
        ("app/main.py", "import os\ndef root(): return {'hello': 'world'}\n"),
        ("requirements.txt", "fastapi==0.115.0\n"),
        ("tests/test_main.py", "def test_root(): assert 1 == 1\n"),
    ])
    exec_id = uuid.uuid4()
    workflow_exec = WorkflowExecution(
        workflow_execution_id=exec_id,
        project_id=project.id,
        workflow_id="code-generation-workflow",
        workflow_version="1.0.0",
        status=WorkflowStatus.COMPLETED,
        artifacts={"code-generation": code_output.model_dump(mode="json")},
        errors=[],
        warnings=[],
        metadata_payload={},
    )
    db_session.add(workflow_exec)
    await db_session.commit()

    payload = {
        "project_id": str(project.id),
        "workflow_execution_id": str(exec_id),
    }
    resp = await client.post(f"/api/v1/projects/{project.id}/analysis/static", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert "analysis_id" in data
    assert data["status"] in ("PASSED", "ISSUES_FOUND")
    assert data["files_analyzed"] == 3
    assert data["test_file_count"] == 1

    # Verify persisted retrieval by analysis_id
    analysis_id = data["analysis_id"]
    get_resp = await client.get(f"/api/v1/projects/{project.id}/analysis/static/{analysis_id}")
    assert get_resp.status_code == 200
    get_data = get_resp.json()
    assert get_data["analysis_id"] == analysis_id


@pytest.mark.asyncio
async def test_run_static_analysis_rejects_extra_fields(client: AsyncClient, mock_sandbox_executor):
    project_id = uuid.uuid4()
    payload = {
        "project_id": str(project_id),
        "arbitrary_ruff_arg": "--unsafe-flags",
    }
    resp = await client.post(f"/api/v1/projects/{project_id}/analysis/static", json=payload)
    assert resp.status_code == 422
