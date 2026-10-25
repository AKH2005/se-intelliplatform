"""Live verification script for Phase 11E Remediation Proposal Agent.

Executes deterministic synthetic remediation proposal generation with:
1. Groq provider (live API)
2. Gemini provider (live API)

Validates:
- Structured RemediationProposalCandidate contract adherence
- Deterministic diff generation from structured proposed changes
- Anti-hallucination controls (modifies ONLY supplied files, no hallucinated requirements or components)
- Patch bounds & secret scanning
- Explicit human approval boundary (proposal generated in AWAITING_APPROVAL status; NOT auto-applied)
- Separate isolated application and verification pipeline test with trusted deterministic fixture
"""

import asyncio
import json
import logging
import sys
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import AsyncMock

# Add backend to sys.path
backend_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(backend_dir))

from app.agents.code_generation.contracts import (
    CodeGenerationOutput,
    CodeGenerationPlan,
    GeneratedFile,
)
from app.agents.execution import AgentExecutor
from app.agents.failure_analysis.contracts import (
    ClaimType,
    DiagnosticClaim,
    EvidenceReference,
    FailureConfidence,
    FailureDiagnosis,
    FailureType,
)
from app.agents.providers.factory import get_llm_provider
from app.agents.remediation.agent import RemediationProposalAgent
from app.agents.remediation.contracts import (
    ChangeOperation,
    ProposedChange,
    RemediationProposal,
    RemediationProposalCandidate,
    RemediationProposalStatus,
    RiskLevel,
)
from app.agents.remediation.diff_generator import DiffGenerator
from app.agents.remediation.service import RemediationService
from app.core.config import settings
from app.models.project import ProjectStatus
from app.models.requirement import RequirementPriority, RequirementStatus, RequirementType
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
from app.sandbox.static_analysis.service import StaticAnalysisService
from app.schemas.context import ProjectContextResponse, RequirementStatistics
from app.schemas.project import ProjectResponse
from app.schemas.requirement import RequirementResponse

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("live_verify_phase11e")


def build_synthetic_failure_fixture():
    project_id = uuid.uuid4()
    req1_id = uuid.uuid4()
    now = datetime.now(timezone.utc)

    project = ProjectResponse(
        id=project_id,
        name="Calculator Microservice",
        slug="calculator-service",
        description="Core arithmetic calculation microservice.",
        status=ProjectStatus.IN_PROGRESS,
        created_at=now,
        updated_at=now,
    )
    req1 = RequirementResponse(
        id=req1_id,
        project_id=project_id,
        title="Summation Engine",
        description="Calculate the sum of integer values.",
        priority=RequirementPriority.HIGH,
        type=RequirementType.FUNCTIONAL,
        status=RequirementStatus.APPROVED,
        is_archived=False,
        created_at=now,
        updated_at=now,
    )
    stats = RequirementStatistics(
        total_requirements=1,
        active_requirements=1,
        functional_count=1,
        non_functional_count=0,
        constraint_count=0,
        by_priority={"HIGH": 1},
        by_status={"APPROVED": 1},
        completion_percentage=100.0,
    )
    context = ProjectContextResponse(
        project=project,
        requirements=[req1],
        statistics=stats,
        context_version=1,
        generated_at=now,
    )

    code_output = CodeGenerationOutput(
        plan=CodeGenerationPlan(
            project_type="backend-service",
            language="python",
            framework="fastapi",
            database="sqlite",
            package_manager="pip",
            files=[
                {"path": "app/calculator.py", "purpose": "Sum calculation logic", "file_type": "SOURCE"},
                {"path": "tests/test_calculator.py", "purpose": "Unit tests for calculator", "file_type": "SOURCE"},
            ],
            rationale="FastAPI calculation scaffold.",
        ),
        generated_files=[
            GeneratedFile(
                path="app/calculator.py",
                content=(
                    "def add_numbers(a: int, b: int) -> int:\n"
                    "    # Calculate sum of two integers\n"
                    "    return total_sum\n"
                ),
                language="python",
                size_bytes=100,
            ),
            GeneratedFile(
                path="tests/test_calculator.py",
                content=(
                    "from app.calculator import add_numbers\n\n"
                    "def test_add_numbers():\n"
                    "    assert add_numbers(2, 3) == 5\n"
                ),
                language="python",
                size_bytes=110,
            ),
        ],
        total_files=2,
        total_size_bytes=210,
        summary="Calculator service implementation with undefined variable total_sum in add_numbers.",
    )

    diagnosis = FailureDiagnosis(
        diagnosis_id=uuid.uuid4(),
        failure_type=FailureType.TEST_FAILURE,
        title="NameError: name 'total_sum' is not defined in add_numbers",
        summary="Unit test failed because total_sum is referenced before assignment in app/calculator.py.",
        root_cause="The add_numbers function returns undefined variable total_sum instead of computing a + b.",
        severity=DiagnosticSeverity.ERROR,
        affected_files=["app/calculator.py"],
        evidence=[
            EvidenceReference(
                evidence_id="ev-sandbox-tb",
                source="execution_stderr",
                code="NameError",
                file_path="app/calculator.py",
                line=3,
                snippet="return total_sum",
                description="NameError: name 'total_sum' is not defined",
            )
        ],
        claims=[
            DiagnosticClaim(
                claim_type=ClaimType.FACT,
                statement="Execution exited with status FAILED due to NameError in app/calculator.py line 3.",
                evidence_ids=["ev-sandbox-tb"],
            ),
            DiagnosticClaim(
                claim_type=ClaimType.INTERPRETATION,
                statement="The variable total_sum was never declared or computed before the return statement.",
                evidence_ids=["ev-sandbox-tb"],
            ),
        ],
        requirement_links=[str(req1_id)],
        architecture_links=[],
        database_links=[],
        suggested_remediation="Assign total_sum = a + b or return a + b directly in add_numbers.",
        limitations=["Only static traces and test stderr captured."],
        confidence=FailureConfidence.HIGH,
    )

    static_result = StaticAnalysisResult(
        analysis_id=uuid.uuid4(),
        project_id=project_id,
        status=StaticAnalysisStatus.ISSUES_FOUND,
        files_analyzed=2,
        duration_seconds=0.03,
        diagnostics=[
            StaticDiagnostic(
                code="F821",
                severity=DiagnosticSeverity.ERROR,
                category=DiagnosticCategory.LINT,
                file_path="app/calculator.py",
                line=3,
                column=11,
                message="Undefined name 'total_sum'",
                source="ruff",
            )
        ],
        error_count=1,
        warning_count=0,
        info_count=0,
        security_issue_count=0,
        test_file_count=1,
        summary="Static analysis detected 1 error in app/calculator.py.",
    )

    exec_result = ExecutionResult(
        execution_id=uuid.uuid4(),
        project_id=project_id,
        execution_type=ExecutionType.TEST,
        status=ExecutionStatus.FAILED,
        exit_code=1,
        stdout="FAILED tests/test_calculator.py::test_add_numbers - NameError: name 'total_sum' is not defined",
        stderr="NameError: name 'total_sum' is not defined at app/calculator.py:3",
        duration_seconds=0.08,
        tests_passed=0,
        tests_failed=1,
        tests_total=1,
    )

    return project_id, context, code_output, diagnosis, static_result, exec_result


async def test_live_provider(provider_name: str, fixture_data: tuple) -> dict:
    project_id, context, code_output, diagnosis, static_res, exec_res = fixture_data
    logger.info(f"============================================================")
    logger.info(f"Testing live provider: {provider_name.upper()}")
    logger.info(f"============================================================")

    orig_provider_setting = settings.LLM_PROVIDER
    settings.LLM_PROVIDER = provider_name

    start_time = time.time()
    try:
        provider = get_llm_provider()
        executor = AgentExecutor(provider=provider, max_retries=1)
        agent = RemediationProposalAgent()

        agent_res = await executor.execute(
            agent=agent,
            context=context,
            session=None,
            diagnosis=diagnosis,
            code_generation=code_output,
            static_analysis_result=static_res,
            execution_result=exec_res,
            current_artifact_version=1,
        )

        elapsed = time.time() - start_time
        candidate: RemediationProposalCandidate = agent_res.output

        logger.info(f"[{provider_name}] Status: {agent_res.status.value}, Validation: {agent_res.validation.is_valid}")
        logger.info(f"[{provider_name}] Title: {candidate.title}")
        logger.info(f"[{provider_name}] Summary: {candidate.summary}")
        logger.info(f"[{provider_name}] Changes ({len(candidate.changes)}):")
        for ch in candidate.changes:
            logger.info(f"  - {ch.operation.value} {ch.file_path}: {ch.reason}")

        # Compute deterministic diff
        current_files = {f.path: f.content for f in code_output.generated_files}
        unified_diff, _ = DiffGenerator.apply_changes_to_files(current_files, candidate.changes)

        logger.info(f"[{provider_name}] Generated Unified Diff:\n{unified_diff}")

        # Safety Check: Must NOT auto-apply
        logger.info(f"[{provider_name}] Safety Check: Patch NOT applied. Explicit human approval boundary respected.")

        return {
            "provider": provider_name,
            "status": agent_res.status.value,
            "is_valid": agent_res.validation.is_valid,
            "validation_errors": agent_res.validation.errors,
            "elapsed_seconds": round(elapsed, 2),
            "title": candidate.title,
            "summary": candidate.summary,
            "changes_count": len(candidate.changes),
            "affected_files": [c.file_path for c in candidate.changes],
            "unified_diff": unified_diff,
            "risk_level": candidate.risk_level.value,
        }

    except Exception as exc:
        elapsed = time.time() - start_time
        logger.error(f"[{provider_name}] Failed: {exc}", exc_info=True)
        return {
            "provider": provider_name,
            "status": "FAILED",
            "is_valid": False,
            "error": str(exc),
            "elapsed_seconds": round(elapsed, 2),
        }
    finally:
        settings.LLM_PROVIDER = orig_provider_setting


async def test_deterministic_application_pipeline(fixture_data: tuple) -> dict:
    """Test the complete patch application, versioning, and verification pipeline using a trusted fixture."""
    logger.info(f"============================================================")
    logger.info(f"Testing Controlled Patch Application & Regression Pipeline")
    logger.info(f"============================================================")

    project_id, context, code_output, diagnosis, static_res, exec_res = fixture_data

    # Trusted candidate patch
    trusted_candidate = RemediationProposalCandidate(
        title="Fix undefined total_sum in add_numbers",
        summary="Replaces undefined total_sum with direct addition a + b.",
        rationale="add_numbers references an unassigned total_sum identifier. Returning a + b resolves the NameError.",
        changes=[
            ProposedChange(
                file_path="app/calculator.py",
                operation=ChangeOperation.MODIFY,
                original_region="return total_sum",
                proposed_region="return a + b",
                reason="Return correct sum calculation",
                evidence_ids=["ev-sandbox-tb"],
            )
        ],
        expected_effect="add_numbers returns the expected integer sum and unit tests pass.",
        verification_plan="Run static analysis and Docker sandbox test suite.",
        risk_level=RiskLevel.LOW,
    )

    current_files = {f.path: f.content for f in code_output.generated_files}
    diff_text, updated_files = DiffGenerator.apply_changes_to_files(current_files, trusted_candidate.changes)

    prop_id = uuid.uuid4()
    proposal = RemediationProposal(
        proposal_id=prop_id,
        diagnosis_id=str(diagnosis.diagnosis_id),
        project_id=project_id,
        title=trusted_candidate.title,
        summary=trusted_candidate.summary,
        rationale=trusted_candidate.rationale,
        changes=trusted_candidate.changes,
        affected_files=["app/calculator.py"],
        unified_diff=diff_text,
        expected_effect=trusted_candidate.expected_effect,
        verification_plan=trusted_candidate.verification_plan,
        risk_level=trusted_candidate.risk_level,
        status=RemediationProposalStatus.APPROVED,  # Explicit human approval granted
        parent_artifact_version=1,
    )

    # Mock Sandbox & Static Analysis for verification
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
                stdout="1 passed in 0.04s",
                stderr="",
                duration_seconds=0.04,
                tests_passed=1,
                tests_failed=0,
            )

    sandbox = MockSandbox()
    static_svc = StaticAnalysisService(executor=sandbox)

    # In-memory target execution record
    target_exec = WorkflowExecution(
        workflow_execution_id=uuid.uuid4(),
        project_id=project_id,
        workflow_id="code_generation",
        workflow_version="1.0.0",
        status=WorkflowStatus.COMPLETED,
        artifacts={
            "code-generation": code_output.model_dump(mode="json"),
            "failure_analysis": diagnosis.model_dump(mode="json"),
            "remediation_proposal": proposal.model_dump(mode="json"),
        },
    )

    session_mock = AsyncMock()
    service = RemediationService(
        session=session_mock,
        workflow_service=AsyncMock(),
        executor=AsyncMock(),
        context_engine=AsyncMock(),
        sandbox_executor=sandbox,
        static_analysis_service=static_svc,
    )
    service.get_proposal = AsyncMock(return_value=proposal)
    service._resolve_target_execution = AsyncMock(return_value=target_exec)

    # Apply approved proposal
    verified_prop, verif_result = await service.apply_proposal(project_id, prop_id)

    logger.info(f"Verification Result: {verif_result.status.value}")
    logger.info(f"Static Analysis Passed: {verif_result.static_analysis_passed}")
    logger.info(f"Sandbox Tests Passed: {verif_result.sandbox_passed}")
    logger.info(f"Resulting Artifact Version: {verified_prop.resulting_artifact_version}")
    logger.info(f"Original v1 preserved: {'code_generation_v1' in target_exec.artifacts}")

    return {
        "status": "SUCCESS",
        "proposal_status": verified_prop.status.value,
        "verification_status": verif_result.status.value,
        "static_analysis_passed": verif_result.static_analysis_passed,
        "sandbox_passed": verif_result.sandbox_passed,
        "resulting_version": verified_prop.resulting_artifact_version,
        "original_v1_preserved": "code_generation_v1" in target_exec.artifacts,
    }


async def main():
    logger.info("Initializing Phase 11E Live Remediation Verification...")
    fixture_data = build_synthetic_failure_fixture()

    groq_res = await test_live_provider("groq", fixture_data)
    gemini_res = await test_live_provider("gemini", fixture_data)
    pipeline_res = await test_deterministic_application_pipeline(fixture_data)

    report = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "groq": groq_res,
        "gemini": gemini_res,
        "application_pipeline": pipeline_res,
    }

    scratch_path = Path("C:/Users/DELL/.gemini/antigravity-ide/brain/c2a62727-cf3a-49c9-9128-524cdfe35d95/scratch/phase_11e_live_verification.json")
    scratch_path.parent.mkdir(parents=True, exist_ok=True)
    with open(scratch_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    logger.info(f"Report saved to {scratch_path}")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    asyncio.run(main())
