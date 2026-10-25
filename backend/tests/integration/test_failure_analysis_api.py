"""Integration Tests for Failure Analysis API Endpoints."""

import uuid
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.failure_analysis.contracts import (
    ClaimType,
    DiagnosticClaim,
    EvidenceReference,
    FailureConfidence,
    FailureDiagnosis,
    FailureType,
)
from app.api.dependencies import get_agent_executor
from app.agents.execution import AgentExecutor
from app.agents.providers.mock import MockLLMProvider
from app.main import app
from app.models.project import Project, ProjectStatus
from app.models.workflow_execution import WorkflowExecution, WorkflowStatus
from app.sandbox.contracts import ExecutionResult, ExecutionStatus, ExecutionType
from app.sandbox.static_analysis.contracts import (
    DiagnosticCategory,
    DiagnosticSeverity,
    StaticAnalysisResult,
    StaticAnalysisStatus,
    StaticDiagnostic,
)
from tests.unit.test_sandbox import make_valid_code_output


@pytest.fixture
def mock_agent_executor():
    mock_prov = MockLLMProvider()
    canned_diagnosis = FailureDiagnosis(
        failure_type=FailureType.TEST_FAILURE,
        title="Integration Test Assertion Failure",
        summary="Pytest returned failure exit code during sandbox run.",
        root_cause="Assertion failed in test_main.py asserting root status is ok.",
        severity=DiagnosticSeverity.ERROR,
        affected_files=["app/main.py", "tests/test_main.py"],
        evidence=[
            EvidenceReference(
                evidence_id="sandbox_stdout",
                source="execution",
                code="ASSERTION_FAILED",
                file_path="tests/test_main.py",
                line=2,
            )
        ],
        claims=[
            DiagnosticClaim(
                claim_type=ClaimType.FACT,
                statement="Exit code 1 returned from containerized pytest.",
                evidence_ids=["sandbox_stdout"],
            )
        ],
        suggested_remediation="Correct the returned status code in app/main.py.",
        limitations=["Heap memory was not recorded."],
        confidence=FailureConfidence.HIGH,
    )
    mock_prov.register_structured_response(canned_diagnosis)
    executor = AgentExecutor(provider=mock_prov)

    app.dependency_overrides[get_agent_executor] = lambda: executor
    yield executor
    app.dependency_overrides.pop(get_agent_executor, None)


@pytest.mark.asyncio
async def test_run_failure_analysis_nonexistent_project(client: AsyncClient, mock_agent_executor):
    project_id = uuid.uuid4()
    payload = {"workflow_execution_id": None, "force": False}
    resp = await client.post(f"/api/v1/projects/{project_id}/analysis/failure", json=payload)
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_run_failure_analysis_no_artifact(client: AsyncClient, db_session: AsyncSession, mock_agent_executor):
    project = Project(
        id=uuid.uuid4(),
        name="Empty FA Project",
        slug="empty-fa-project",
        status=ProjectStatus.IN_PROGRESS,
    )
    db_session.add(project)
    await db_session.commit()

    payload = {"workflow_execution_id": None, "force": False}
    resp = await client.post(f"/api/v1/projects/{project.id}/analysis/failure", json=payload)
    assert resp.status_code == 422
    assert "no workflow execution" in resp.json()["detail"].lower()


@pytest.mark.asyncio
async def test_run_failure_analysis_clean_skipped(
    client: AsyncClient,
    db_session: AsyncSession,
    mock_agent_executor,
):
    """When static analysis and execution both passed, failure analysis skips cleanly without calling LLM."""
    project = Project(
        id=uuid.uuid4(),
        name="Clean Project",
        slug="clean-project",
        status=ProjectStatus.IN_PROGRESS,
    )
    db_session.add(project)

    code_output = make_valid_code_output([
        ("app/main.py", "def root(): return {'hello': 'world'}\n"),
        ("requirements.txt", "fastapi==0.115.0\n"),
        ("tests/test_main.py", "def test_root(): assert 1 == 1\n"),
    ])

    exec_res = ExecutionResult(
        execution_id=uuid.uuid4(),
        project_id=project.id,
        execution_type=ExecutionType.TEST,
        status=ExecutionStatus.PASSED,
        exit_code=0,
        duration_seconds=0.25,
        stdout="1 passed",
        stderr="",
        is_truncated=False,
        tests_passed=1,
        tests_failed=0,
        tests_total=1,
        validation_errors=[],
        metadata={},
    )
    static_res = StaticAnalysisResult(
        analysis_id=uuid.uuid4(),
        project_id=project.id,
        status=StaticAnalysisStatus.PASSED,
        duration_seconds=0.1,
        files_analyzed=3,
        error_count=0,
        warning_count=0,
        summary="0 errors, 0 warnings",
    )

    exec_id = uuid.uuid4()
    workflow_exec = WorkflowExecution(
        workflow_execution_id=exec_id,
        project_id=project.id,
        workflow_id="code-generation-workflow",
        workflow_version="1.0.0",
        status=WorkflowStatus.COMPLETED,
        artifacts={
            "code-generation": code_output.model_dump(mode="json"),
            "sandbox_execution": exec_res.model_dump(mode="json"),
            "static_analysis": static_res.model_dump(mode="json"),
        },
        errors=[],
        warnings=[],
        metadata_payload={},
    )
    db_session.add(workflow_exec)
    await db_session.commit()

    resp = await client.post(
        f"/api/v1/projects/{project.id}/analysis/failure",
        json={"workflow_execution_id": str(exec_id), "force": False},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["title"] == "No Failure Detected"
    assert data["model_metadata"]["trigger_status"] == "SKIPPED_CLEAN"
    # Verify no LLM call was dispatched to mock provider
    assert len(mock_agent_executor.provider.call_history) == 0


@pytest.mark.asyncio
async def test_run_failure_analysis_failing_execution(
    client: AsyncClient,
    db_session: AsyncSession,
    mock_agent_executor,
):
    """When sandbox test execution failed, failure analysis is triggered and diagnoses root cause."""
    project = Project(
        id=uuid.uuid4(),
        name="Failing Project",
        slug="failing-project",
        status=ProjectStatus.IN_PROGRESS,
    )
    db_session.add(project)

    code_output = make_valid_code_output([
        ("app/main.py", "def root(): return {'hello': 'world'}\n"),
        ("requirements.txt", "fastapi==0.115.0\n"),
        ("tests/test_main.py", "def test_root(): assert 1 == 2\n"),
    ])

    exec_res = ExecutionResult(
        execution_id=uuid.uuid4(),
        project_id=project.id,
        execution_type=ExecutionType.TEST,
        status=ExecutionStatus.FAILED,
        exit_code=1,
        duration_seconds=0.45,
        stdout="FAILED tests/test_main.py::test_root - assert 1 == 2\n1 failed in 0.05s",
        stderr="",
        is_truncated=False,
        tests_passed=0,
        tests_failed=1,
        tests_total=1,
        validation_errors=[],
        metadata={},
    )

    exec_id = uuid.uuid4()
    workflow_exec = WorkflowExecution(
        workflow_execution_id=exec_id,
        project_id=project.id,
        workflow_id="code-generation-workflow",
        workflow_version="1.0.0",
        status=WorkflowStatus.COMPLETED,
        artifacts={
            "code-generation": code_output.model_dump(mode="json"),
            "sandbox_execution": exec_res.model_dump(mode="json"),
        },
        errors=[],
        warnings=[],
        metadata_payload={},
    )
    db_session.add(workflow_exec)
    await db_session.commit()

    resp = await client.post(
        f"/api/v1/projects/{project.id}/analysis/failure",
        json={"workflow_execution_id": str(exec_id), "force": False},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["failure_type"] == "TEST_FAILURE"
    assert "Integration Test Assertion Failure" in data["title"]
    assert "diagnosis_id" in data
    assert len(data["affected_files"]) > 0

    diagnosis_id = data["diagnosis_id"]

    # Verify persisted retrieval via GET endpoint
    get_resp = await client.get(f"/api/v1/projects/{project.id}/analysis/failure/{diagnosis_id}")
    assert get_resp.status_code == 200
    get_data = get_resp.json()
    assert get_data["diagnosis_id"] == diagnosis_id
    assert get_data["title"] == data["title"]
