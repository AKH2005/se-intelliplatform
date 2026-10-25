"""Integration Tests for Phase 11G: AI Test Failure Analysis & Unified Verification API."""

import uuid
from datetime import datetime, timezone
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.execution import AgentExecutor
from app.agents.failure_analysis.contracts import (
    ClaimType,
    DiagnosticClaim,
    DiagnosticSeverity,
    EvidenceReference,
    FailureConfidence,
    FailureDiagnosis,
    FailureSource,
    FailureType,
)
from app.agents.providers.mock import MockLLMProvider
from app.agents.test_generation.contracts import (
    AITestCaseResult,
    AITestExecutionResult,
    AITestSuite,
    GeneratedTest,
    TestCategory,
)
from app.api.dependencies import get_agent_executor
from app.main import app
from app.models.project import Project, ProjectStatus
from app.models.workflow_execution import WorkflowExecution, WorkflowStatus
from app.sandbox.contracts import ExecutionStatus
from tests.unit.test_sandbox import make_valid_code_output


@pytest.fixture
def mock_failure_agent_executor():
    mock_prov = MockLLMProvider()
    canned_diagnosis = FailureDiagnosis(
        failure_type=FailureType.TEST_FAILURE,
        failure_source=FailureSource.AI_TEST,
        title="ZeroDivisionError in Calculator Division Method",
        summary="Test test_divide_by_zero_raises failed with uncaught ZeroDivisionError.",
        root_cause="The divide method lacks defensive validation for zero divisors before performing floating point division.",
        severity=DiagnosticSeverity.ERROR,
        affected_files=["app/calculator.py"],
        evidence=[
            EvidenceReference(
                evidence_id="TEST-001",
                source="ai_test",
                code="test_divide_by_zero_raises",
                file_path="app/calculator.py",
                line=12,
                snippet="return a / b",
                description="Failed assertion expecting handled ValueError",
            ),
            EvidenceReference(
                evidence_id="ai_test_stdout",
                source="execution",
                description="Pytest output trace showing ZeroDivisionError",
            ),
        ],
        claims=[
            DiagnosticClaim(
                claim_type=ClaimType.FACT,
                statement="AI Test TEST-001 failed with ZeroDivisionError.",
                evidence_ids=["TEST-001"],
            ),
            DiagnosticClaim(
                claim_type=ClaimType.INTERPRETATION,
                statement="The implementation does not defensively check if denominator is zero.",
                evidence_ids=["TEST-001", "ai_test_stdout"],
            ),
            DiagnosticClaim(
                claim_type=ClaimType.RECOMMENDATION,
                statement="Introduce zero check in divide method before arithmetic execution.",
                evidence_ids=[],
            ),
        ],
        suggested_remediation="Verify that the denominator argument is non-zero before dividing.",
        limitations=["Only static code and pytest outputs were inspected."],
        confidence=FailureConfidence.HIGH,
    )
    mock_prov.register_structured_response(canned_diagnosis)
    executor = AgentExecutor(provider=mock_prov)

    app.dependency_overrides[get_agent_executor] = lambda: executor
    yield executor
    app.dependency_overrides.pop(get_agent_executor, None)


async def _seed_project_with_ai_test_failure(db_session: AsyncSession):
    project = Project(
        id=uuid.uuid4(),
        name="AI Test Failure Project",
        slug="ai-test-failure-project",
        status=ProjectStatus.IN_PROGRESS,
    )
    db_session.add(project)
    await db_session.commit()

    code_output = make_valid_code_output()
    # Ensure calculator.py exists in generated files
    for f in code_output.generated_files:
        if f.path == "app/main.py":
            f.path = "app/calculator.py"

    suite_id = uuid.uuid4()
    ai_suite = AITestSuite(
        suite_id=suite_id,
        project_id=project.id,
        summary="Test suite for calculator module",
        tests=[
            GeneratedTest(
                test_id="TEST-001",
                name="test_divide_by_zero_raises",
                description="Checks zero division",
                category=TestCategory.ERROR_HANDLING,
                target_file="app/calculator.py",
                target_symbol="divide",
                requirement_ids=[],
                architecture_component="CalculatorService",
                rationale="Defensive programming",
                code="def test_divide_by_zero_raises(): pass",
                expected_behavior="Raises ValueError",
            )
        ],
        test_count=1,
        requirement_traceability={},
        source_artifact_reference="code_generation",
        test_files={"tests/test_ai_generated.py": "def test_divide_by_zero_raises(): pass"},
    )

    ai_exec = AITestExecutionResult(
        execution_id=uuid.uuid4(),
        suite_id=suite_id,
        project_id=project.id,
        status=ExecutionStatus.FAILED,
        exit_code=1,
        duration_seconds=0.35,
        tests_total=1,
        tests_passed=0,
        tests_failed=1,
        tests_skipped=0,
        stdout="tests/test_ai_generated.py::test_divide_by_zero_raises FAILED\n1 failed in 0.05s",
        stderr="",
        failure_summaries=["ZeroDivisionError: division by zero at app/calculator.py:12"],
        test_results=[
            AITestCaseResult(name="test_divide_by_zero_raises", status="FAILED", duration_seconds=0.05)
        ],
    )

    exec_id = uuid.uuid4()
    workflow_exec = WorkflowExecution(
        workflow_execution_id=exec_id,
        project_id=project.id,
        workflow_id="ai-testing-workflow",
        workflow_version="1.0.0",
        status=WorkflowStatus.COMPLETED,
        artifacts={
            "code_generation": code_output.model_dump(mode="json"),
            "ai_test_suite": ai_suite.model_dump(mode="json"),
            "ai_test_execution": ai_exec.model_dump(mode="json"),
        },
        errors=[],
        warnings=[],
        metadata_payload={},
    )
    db_session.add(workflow_exec)
    await db_session.commit()

    return project, workflow_exec, ai_suite, ai_exec


@pytest.mark.asyncio
async def test_analyze_ai_test_failure_endpoint(
    client: AsyncClient,
    db_session: AsyncSession,
    mock_failure_agent_executor,
):
    """POST /projects/{id}/tests/ai/{suite_id}/analyze-failure produces and persists structured diagnosis."""
    project, wf_exec, ai_suite, _ = await _seed_project_with_ai_test_failure(db_session)

    resp = await client.post(
        f"/api/v1/projects/{project.id}/tests/ai/{ai_suite.suite_id}/analyze-failure",
        json={"workflow_execution_id": str(wf_exec.workflow_execution_id)},
    )
    assert resp.status_code == 200
    data = resp.json()

    assert data["failure_type"] == "TEST_FAILURE"
    assert data["failure_source"] == "AI_TEST"
    assert "ZeroDivisionError" in data["title"]
    assert "app/calculator.py" in data["affected_files"]
    assert len(data["evidence"]) >= 1
    assert data["evidence"][0]["evidence_id"] == "TEST-001"

    diagnosis_id = data["diagnosis_id"]

    # Verify persisted in workflow execution artifacts
    await db_session.refresh(wf_exec)
    assert "failure_analysis" in wf_exec.artifacts
    assert "ai_test_failure_analysis" in wf_exec.artifacts
    assert wf_exec.artifacts["ai_test_failure_analysis"]["diagnosis_id"] == diagnosis_id

    # Verify retrieval via GET /projects/{id}/analysis/failure/{diagnosis_id}
    get_resp = await client.get(f"/api/v1/projects/{project.id}/analysis/failure/{diagnosis_id}")
    assert get_resp.status_code == 200
    get_data = get_resp.json()
    assert get_data["diagnosis_id"] == diagnosis_id
    assert get_data["failure_source"] == "AI_TEST"


@pytest.mark.asyncio
async def test_run_failure_analysis_with_ai_test_source_filter(
    client: AsyncClient,
    db_session: AsyncSession,
    mock_failure_agent_executor,
):
    """POST /projects/{id}/analysis/failure with failure_source='AI_TEST' targets AI test execution."""
    project, wf_exec, _, _ = await _seed_project_with_ai_test_failure(db_session)

    resp = await client.post(
        f"/api/v1/projects/{project.id}/analysis/failure",
        json={
            "workflow_execution_id": str(wf_exec.workflow_execution_id),
            "force": True,
            "failure_source": "AI_TEST",
        },
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["failure_source"] == "AI_TEST"
    assert data["failure_type"] == "TEST_FAILURE"
