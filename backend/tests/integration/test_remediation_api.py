"""Integration Tests for Phase 11E Remediation Proposal, Approval, Application & Verification API."""

import uuid
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from unittest.mock import AsyncMock, patch

from app.agents.code_generation.contracts import CodeGenerationOutput, CodeGenerationPlan, GeneratedFile
from app.agents.execution import AgentExecutor
from app.agents.failure_analysis.contracts import (
    ClaimType,
    DiagnosticClaim,
    EvidenceReference,
    FailureConfidence,
    FailureDiagnosis,
    FailureType,
)
from app.agents.providers.mock import MockLLMProvider
from app.agents.remediation.contracts import (
    ChangeOperation,
    ProposedChange,
    RemediationProposalCandidate,
    RemediationProposalStatus,
    RiskLevel,
)
from app.api.dependencies import get_agent_executor, get_sandbox_executor
from app.main import app
from app.models.project import Project, ProjectStatus
from app.models.workflow_execution import WorkflowExecution, WorkflowStatus
from app.sandbox.base import AbstractSandboxExecutor
from app.sandbox.contracts import ExecutionRequest, ExecutionResult, ExecutionStatus, ExecutionType
from app.sandbox.static_analysis.contracts import (
    DiagnosticCategory,
    DiagnosticSeverity,
    StaticAnalysisRequest,
    StaticAnalysisResult,
    StaticAnalysisStatus,
    StaticDiagnostic,
)


@pytest.fixture
def mock_agent_and_sandbox_dependencies():
    """Mock LLM provider returning a valid RemediationProposalCandidate and mock sandbox."""
    mock_prov = MockLLMProvider()
    canned_proposal = RemediationProposalCandidate(
        title="Initialize compute return variable",
        summary="Defines the calculation return value to resolve the runtime NameError.",
        rationale="The service function returns an unassigned identifier. Returning 42 satisfies tests.",
        changes=[
            ProposedChange(
                file_path="app/main.py",
                operation=ChangeOperation.MODIFY,
                original_region="return undefined_val",
                proposed_region="return 42",
                reason="Return fixed calculation result",
                evidence_ids=["ev-sandbox-err"],
            )
        ],
        expected_effect="Eliminates the runtime NameError and passes tests.",
        verification_plan="Run static analysis and Docker sandbox pytest.",
        risk_level=RiskLevel.LOW,
        requirement_links=[],
        architecture_links=[],
        database_links=[],
    )
    mock_prov.register_structured_response(canned_proposal)
    executor = AgentExecutor(provider=mock_prov)

    # Mock Sandbox Executor
    class MockSandbox(AbstractSandboxExecutor):
        async def is_available(self) -> bool:
            return True

        async def execute(self, request, code_output):
            return ExecutionResult(
                execution_id=uuid.uuid4(),
                project_id=request.project_id,
                execution_type=request.execution_type,
                status=ExecutionStatus.PASSED,
                exit_code=0,
                stdout="1 passed in 0.05s",
                stderr="",
                duration_seconds=0.05,
                tests_passed=1,
                tests_failed=0,
            )

    sandbox = MockSandbox()

    app.dependency_overrides[get_agent_executor] = lambda: executor
    app.dependency_overrides[get_sandbox_executor] = lambda: sandbox

    yield executor, sandbox

    app.dependency_overrides.pop(get_agent_executor, None)
    app.dependency_overrides.pop(get_sandbox_executor, None)


async def setup_project_with_failure(db_session: AsyncSession) -> tuple[Project, WorkflowExecution]:
    """Helper to seed a project and a workflow execution with code artifact and failure analysis."""
    proj = Project(
        id=uuid.uuid4(),
        name="Remediation Test Project",
        slug=f"remediation-test-{uuid.uuid4().hex[:6]}",
        status=ProjectStatus.IN_PROGRESS,
    )
    db_session.add(proj)
    await db_session.flush()

    code_artifact = CodeGenerationOutput(
        plan=CodeGenerationPlan(
            project_type="backend-service",
            language="python",
            framework="fastapi",
            database="sqlite",
            package_manager="pip",
            files=[
                {"path": "app/main.py", "purpose": "Entry", "file_type": "SOURCE"},
                {"path": "tests/test_main.py", "purpose": "Tests", "file_type": "SOURCE"},
            ],
            rationale="FastAPI test project.",
        ),
        generated_files=[
            GeneratedFile(
                path="app/main.py",
                content="def compute():\n    return undefined_val\n",
                language="python",
                size_bytes=40,
            ),
            GeneratedFile(
                path="tests/test_main.py",
                content="from app.main import compute\ndef test_compute():\n    assert compute() == 42\n",
                language="python",
                size_bytes=65,
            ),
        ],
        total_files=2,
        total_size_bytes=105,
        summary="Initial scaffold with bug.",
    )

    failure_diagnosis = FailureDiagnosis(
        failure_type=FailureType.TEST_FAILURE,
        title="Pytest failure in compute",
        summary="A NameError occurred because undefined_val is not defined.",
        root_cause="The returned value was undefined at line 2 in app/main.py.",
        severity=DiagnosticSeverity.ERROR,
        affected_files=["app/main.py"],
        evidence=[
            EvidenceReference(
                evidence_id="ev-sandbox-err",
                source="execution",
                code="NameError",
                file_path="app/main.py",
                line=2,
                snippet="return undefined_val",
                description="Runtime NameError",
            )
        ],
        claims=[
            DiagnosticClaim(
                claim_type=ClaimType.FACT,
                statement="Execution terminated with exit code 1.",
                evidence_ids=["ev-sandbox-err"],
            )
        ],
        requirement_links=[],
        architecture_links=[],
        database_links=[],
        suggested_remediation="Return 42 from compute function.",
        limitations=[],
        confidence=FailureConfidence.HIGH,
    )

    wf = WorkflowExecution(
        workflow_execution_id=uuid.uuid4(),
        project_id=proj.id,
        workflow_id="code_generation",
        workflow_version="1.0.0",
        status=WorkflowStatus.COMPLETED,
        artifacts={
            "code-generation": code_artifact.model_dump(mode="json"),
            "failure_analysis": failure_diagnosis.model_dump(mode="json"),
        },
    )
    db_session.add(wf)
    await db_session.commit()
    return proj, wf


# ==============================================================================
# API Integration Tests
# ==============================================================================

@pytest.mark.asyncio
async def test_remediation_lifecycle_end_to_end(
    client: AsyncClient,
    db_session: AsyncSession,
    mock_agent_and_sandbox_dependencies,
):
    """Full lifecycle: create proposal -> retrieve -> approve -> apply -> verify new version."""
    project, wf = await setup_project_with_failure(db_session)
    proj_id = str(project.id)

    # 1. CREATE PROPOSAL
    resp = await client.post(f"/api/v1/projects/{proj_id}/remediation/proposals")
    assert resp.status_code == 201
    prop_data = resp.json()
    proposal_id = prop_data["proposal_id"]
    assert prop_data["status"] == "AWAITING_APPROVAL"
    assert prop_data["risk_level"] == "LOW"
    assert "app/main.py" in prop_data["affected_files"]
    assert "-    return undefined_val" in prop_data["unified_diff"]
    assert "+    return 42" in prop_data["unified_diff"]

    # 2. RETRIEVE PROPOSAL
    get_resp = await client.get(f"/api/v1/projects/{proj_id}/remediation/proposals/{proposal_id}")
    assert get_resp.status_code == 200
    assert get_resp.json()["proposal_id"] == proposal_id

    # 3. APPLY WITHOUT APPROVAL MUST BE REJECTED (409 Conflict)
    apply_fail = await client.post(f"/api/v1/projects/{proj_id}/remediation/proposals/{proposal_id}/apply")
    assert apply_fail.status_code == 409
    assert "must be explicitly APPROVED" in apply_fail.json()["detail"]

    # 4. EXPLICIT APPROVAL
    appr_resp = await client.post(f"/api/v1/projects/{proj_id}/remediation/proposals/{proposal_id}/approve")
    assert appr_resp.status_code == 200
    assert appr_resp.json()["status"] == "APPROVED"
    assert appr_resp.json()["approved_at"] is not None

    # 5. APPLY APPROVED PROPOSAL
    apply_resp = await client.post(f"/api/v1/projects/{proj_id}/remediation/proposals/{proposal_id}/apply")
    assert apply_resp.status_code == 200
    apply_body = apply_resp.json()

    # 6. VERIFICATION RESULTS
    proposal_after = apply_body["proposal"]
    verification = apply_body["verification"]
    assert proposal_after["status"] == "VERIFIED"
    assert proposal_after["resulting_artifact_version"] == 2
    assert verification["status"] == "VERIFIED"
    assert verification["static_analysis_passed"] is True
    assert verification["sandbox_passed"] is True

    # 7. CHECK VERSION PRESERVATION IN DB
    await db_session.refresh(wf)
    artifacts = wf.artifacts
    # Original artifact preserved under code_generation_v1
    assert "code_generation_v1" in artifacts
    orig_files = artifacts["code_generation_v1"]["generated_files"]
    assert any("return undefined_val" in f["content"] for f in orig_files)

    # Active code-generation artifact updated to v2 with patch applied
    active_files = artifacts["code-generation"]["generated_files"]
    assert any("return 42" in f["content"] for f in active_files)


@pytest.mark.asyncio
async def test_remediation_reject_proposal(
    client: AsyncClient,
    db_session: AsyncSession,
    mock_agent_and_sandbox_dependencies,
):
    """Proposal rejection transitions to REJECTED and forbids subsequent application."""
    project, wf = await setup_project_with_failure(db_session)
    proj_id = str(project.id)

    # Create proposal
    create_resp = await client.post(f"/api/v1/projects/{proj_id}/remediation/proposals")
    proposal_id = create_resp.json()["proposal_id"]

    # Reject proposal
    reject_resp = await client.post(
        f"/api/v1/projects/{proj_id}/remediation/proposals/{proposal_id}/reject",
        json={"reason": "Engineer opted for architectural refactoring instead."},
    )
    assert reject_resp.status_code == 200
    assert reject_resp.json()["status"] == "REJECTED"
    assert reject_resp.json()["rejection_reason"] == "Engineer opted for architectural refactoring instead."

    # Attempt to apply rejected proposal must fail (409 Conflict)
    apply_resp = await client.post(f"/api/v1/projects/{proj_id}/remediation/proposals/{proposal_id}/apply")
    assert apply_resp.status_code == 409


@pytest.mark.asyncio
async def test_unauthorized_project_access(client: AsyncClient, mock_agent_and_sandbox_dependencies):
    """Accessing remediation for non-existent project returns 404."""
    fake_proj_id = str(uuid.uuid4())
    fake_prop_id = str(uuid.uuid4())

    resp = await client.get(f"/api/v1/projects/{fake_proj_id}/remediation/proposals/{fake_prop_id}")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_double_approval_idempotency(
    client: AsyncClient,
    db_session: AsyncSession,
    mock_agent_and_sandbox_dependencies,
):
    """Approving an already approved proposal is idempotent and succeeds without error."""
    project, wf = await setup_project_with_failure(db_session)
    proj_id = str(project.id)

    create_resp = await client.post(f"/api/v1/projects/{proj_id}/remediation/proposals")
    proposal_id = create_resp.json()["proposal_id"]

    # First approval
    resp1 = await client.post(f"/api/v1/projects/{proj_id}/remediation/proposals/{proposal_id}/approve")
    assert resp1.status_code == 200
    assert resp1.json()["status"] == "APPROVED"

    # Second approval (idempotent)
    resp2 = await client.post(f"/api/v1/projects/{proj_id}/remediation/proposals/{proposal_id}/approve")
    assert resp2.status_code == 200
    assert resp2.json()["status"] == "APPROVED"


@pytest.mark.asyncio
async def test_double_apply_fails(
    client: AsyncClient,
    db_session: AsyncSession,
    mock_agent_and_sandbox_dependencies,
):
    """Applying an already applied/verified proposal is rejected with 409 Conflict."""
    project, wf = await setup_project_with_failure(db_session)
    proj_id = str(project.id)

    create_resp = await client.post(f"/api/v1/projects/{proj_id}/remediation/proposals")
    proposal_id = create_resp.json()["proposal_id"]

    # Approve
    await client.post(f"/api/v1/projects/{proj_id}/remediation/proposals/{proposal_id}/approve")

    # First apply
    apply1 = await client.post(f"/api/v1/projects/{proj_id}/remediation/proposals/{proposal_id}/apply")
    assert apply1.status_code == 200

    # Second apply must fail (409 Conflict)
    apply2 = await client.post(f"/api/v1/projects/{proj_id}/remediation/proposals/{proposal_id}/apply")
    assert apply2.status_code == 409
    assert "must be explicitly APPROVED" in apply2.json()["detail"]


@pytest.mark.asyncio
async def test_verification_failure_preserves_original_artifact(
    client: AsyncClient,
    db_session: AsyncSession,
    mock_agent_and_sandbox_dependencies,
):
    """When verification fails (e.g. tests fail), status is VERIFICATION_FAILED and original artifact is preserved."""
    executor, sandbox = mock_agent_and_sandbox_dependencies

    # Configure sandbox to return test failure
    sandbox.execute = AsyncMock(
        return_value=ExecutionResult(
            execution_id=uuid.uuid4(),
            project_id=uuid.uuid4(),
            execution_type=ExecutionType.TEST,
            status=ExecutionStatus.FAILED,
            exit_code=1,
            stdout="AssertionError: assert 42 == 99",
            stderr="",
            duration_seconds=0.04,
            tests_passed=0,
            tests_failed=1,
        )
    )

    project, wf = await setup_project_with_failure(db_session)
    proj_id = str(project.id)

    create_resp = await client.post(f"/api/v1/projects/{proj_id}/remediation/proposals")
    proposal_id = create_resp.json()["proposal_id"]

    await client.post(f"/api/v1/projects/{proj_id}/remediation/proposals/{proposal_id}/approve")
    apply_resp = await client.post(f"/api/v1/projects/{proj_id}/remediation/proposals/{proposal_id}/apply")
    assert apply_resp.status_code == 200
    data = apply_resp.json()

    assert data["proposal"]["status"] == "VERIFICATION_FAILED"
    assert data["verification"]["status"] == "VERIFICATION_FAILED"
    assert data["verification"]["sandbox_passed"] is False

    # Check that the original artifact remained active!
    await db_session.refresh(wf)
    active_code = wf.artifacts["code-generation"]["generated_files"]
    assert any("return undefined_val" in f["content"] for f in active_code)

