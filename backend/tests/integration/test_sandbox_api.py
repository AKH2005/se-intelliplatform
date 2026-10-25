"""Integration Tests for Sandbox API Endpoints."""

import uuid
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_sandbox_executor
from app.main import app
from app.models.project import Project, ProjectStatus
from app.models.workflow_execution import WorkflowExecution, WorkflowStatus
from app.sandbox.contracts import ExecutionStatus
from app.sandbox.mock_executor import MockSandboxExecutor
from tests.unit.test_sandbox import make_valid_code_output


@pytest.fixture
def mock_sandbox_executor():
    mock_exec = MockSandboxExecutor(default_status=ExecutionStatus.PASSED)
    app.dependency_overrides[get_sandbox_executor] = lambda: mock_exec
    yield mock_exec
    app.dependency_overrides.pop(get_sandbox_executor, None)


@pytest.mark.asyncio
async def test_get_sandbox_status(client: AsyncClient, mock_sandbox_executor):
    project_id = uuid.uuid4()
    resp = await client.get(f"/api/v1/projects/{project_id}/sandbox/status")
    assert resp.status_code == 200
    data = resp.json()
    assert "available" in data
    assert "security_policy" in data
    assert data["security_policy"]["network"] == "disabled"


@pytest.mark.asyncio
async def test_execute_sandbox_nonexistent_project(client: AsyncClient, mock_sandbox_executor):
    project_id = uuid.uuid4()
    payload = {
        "project_id": str(project_id),
        "execution_type": "TEST",
    }
    resp = await client.post(f"/api/v1/projects/{project_id}/sandbox/execute", json=payload)
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_execute_sandbox_no_code_artifact(client: AsyncClient, db_session: AsyncSession, mock_sandbox_executor):
    project = Project(
        id=uuid.uuid4(),
        name="Test Sandbox Project",
        slug="test-sandbox-project",
        status=ProjectStatus.IN_PROGRESS,
    )
    db_session.add(project)
    await db_session.commit()

    payload = {
        "project_id": str(project.id),
        "execution_type": "TEST",
    }
    resp = await client.post(f"/api/v1/projects/{project.id}/sandbox/execute", json=payload)
    assert resp.status_code == 422
    assert "no completed workflow execution" in resp.json()["detail"].lower()


@pytest.mark.asyncio
async def test_execute_sandbox_with_valid_artifact(
    client: AsyncClient,
    db_session: AsyncSession,
    mock_sandbox_executor,
):
    project = Project(
        id=uuid.uuid4(),
        name="Test Sandbox Project",
        slug="test-sandbox-project-valid",
        status=ProjectStatus.IN_PROGRESS,
    )
    db_session.add(project)

    code_output = make_valid_code_output()
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
        "execution_type": "TEST",
    }
    resp = await client.post(f"/api/v1/projects/{project.id}/sandbox/execute", json=payload)
    assert resp.status_code == 200
    result_data = resp.json()
    assert result_data["status"] == "PASSED"
    assert result_data["exit_code"] == 0
    assert result_data["tests_passed"] == 1


@pytest.mark.asyncio
async def test_execute_sandbox_rejects_arbitrary_commands(
    client: AsyncClient,
    mock_sandbox_executor,
):
    project_id = uuid.uuid4()
    # Attempting to supply unapproved extra fields (e.g. custom command or docker options)
    payload = {
        "project_id": str(project_id),
        "execution_type": "TEST",
        "custom_shell_command": "curl http://attacker.com",
    }
    resp = await client.post(f"/api/v1/projects/{project_id}/sandbox/execute", json=payload)
    assert resp.status_code == 422  # Extra fields forbidden by Pydantic
