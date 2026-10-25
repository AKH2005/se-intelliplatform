"""Unit Tests for Phase 11E Remediation Proposal Agent, Validator, Diff Generator, Contracts & Security."""

import copy
import inspect
import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock
import pytest
from pydantic import ValidationError

from app.agents.code_generation.contracts import CodeGenerationOutput, CodeGenerationPlan, GeneratedFile
from app.agents.failure_analysis.contracts import (
    ClaimType,
    DiagnosticClaim,
    EvidenceReference,
    FailureConfidence,
    FailureDiagnosis,
    FailureType,
    RelevantSourceFile,
)
from app.agents.remediation.agent import RemediationProposalAgent
from app.agents.remediation.contracts import (
    ChangeOperation,
    ProposedChange,
    RemediationProposal,
    RemediationProposalCandidate,
    RemediationProposalInput,
    RemediationProposalStatus,
    RemediationVerificationResult,
    RiskLevel,
)
from app.agents.remediation.diff_generator import DiffGenerator
from app.agents.remediation.service import RemediationService
from app.agents.remediation.validator import RemediationProposalValidator
from app.core.exceptions import ConflictError
from app.models.workflow_execution import WorkflowExecution
from app.sandbox.contracts import ExecutionResult, ExecutionStatus, ExecutionType
from app.sandbox.static_analysis.contracts import (
    DiagnosticCategory,
    DiagnosticSeverity,
    StaticAnalysisResult,
    StaticAnalysisStatus,
    StaticDiagnostic,
)


# ==============================================================================
# 1. Contract Tests
# ==============================================================================

def test_proposed_change_valid():
    change = ProposedChange(
        file_path="app/main.py",
        operation=ChangeOperation.MODIFY,
        original_region="return x",
        proposed_region="return x + 1",
        reason="Increment x to satisfy test criteria",
        evidence_ids=["ev-1"],
    )
    assert change.file_path == "app/main.py"
    assert change.operation == ChangeOperation.MODIFY
    assert change.evidence_ids == ["ev-1"]


def test_proposed_change_rejects_invalid_operation():
    with pytest.raises(ValidationError):
        ProposedChange(
            file_path="app/main.py",
            operation="RENAME",  # Invalid enum value
            original_region="",
            proposed_region="",
            reason="Rename file",
        )


def test_remediation_proposal_valid_contract():
    prop_id = uuid.uuid4()
    diag_id = str(uuid.uuid4())
    proj_id = uuid.uuid4()
    proposal = RemediationProposal(
        proposal_id=prop_id,
        diagnosis_id=diag_id,
        project_id=proj_id,
        title="Fix undefined variable in service",
        summary="Initializes calculation variable prior to return.",
        rationale="Eliminates runtime NameError by declaring variable.",
        changes=[
            ProposedChange(
                file_path="app/main.py",
                operation=ChangeOperation.MODIFY,
                original_region="return undefined_var",
                proposed_region="return {'status': 'ok'}",
                reason="Return valid dict",
            )
        ],
        affected_files=["app/main.py"],
        unified_diff="--- app/main.py\n+++ app/main.py\n@@ -1,1 +1,1 @@\n-return undefined_var\n+return {'status': 'ok'}",
        expected_effect="Tests pass without NameError.",
        verification_plan="Run static analysis and sandbox pytest.",
        risk_level=RiskLevel.LOW,
        status=RemediationProposalStatus.AWAITING_APPROVAL,
        parent_artifact_version=1,
    )
    assert proposal.proposal_id == prop_id
    assert proposal.status == RemediationProposalStatus.AWAITING_APPROVAL
    assert proposal.risk_level == RiskLevel.LOW
    assert proposal.parent_artifact_version == 1
    assert proposal.resulting_artifact_version is None


def test_remediation_proposal_rejects_invalid_status():
    with pytest.raises(ValidationError):
        RemediationProposal(
            proposal_id=uuid.uuid4(),
            diagnosis_id=str(uuid.uuid4()),
            project_id=uuid.uuid4(),
            title="Title",
            summary="Summary",
            rationale="Rationale",
            changes=[],
            affected_files=[],
            unified_diff="",
            expected_effect="Effect",
            verification_plan="Plan",
            risk_level=RiskLevel.LOW,
            status="AUTOMATICALLY_HEALED",  # Invalid status
            parent_artifact_version=1,
        )


# ==============================================================================
# 2. Diff Generator Tests
# ==============================================================================

def test_diff_generator_modify():
    current_files = {"app/main.py": "line1\nline2\nreturn False\nline4\n"}
    changes = [
        ProposedChange(
            file_path="app/main.py",
            operation=ChangeOperation.MODIFY,
            original_region="return False",
            proposed_region="return True",
            reason="Fix return bool",
        )
    ]
    diff, updated = DiffGenerator.apply_changes_to_files(current_files, changes)
    assert "-return False" in diff
    assert "+return True" in diff
    assert updated["app/main.py"] == "line1\nline2\nreturn True\nline4\n"


def test_diff_generator_add():
    current_files = {"app/main.py": "print('hello')\n"}
    changes = [
        ProposedChange(
            file_path="app/utils.py",
            operation=ChangeOperation.ADD,
            original_region="",
            proposed_region="def helper(): return 42\n",
            reason="Add missing helper",
        )
    ]
    diff, updated = DiffGenerator.apply_changes_to_files(current_files, changes)
    assert "b/app/utils.py" in diff
    assert "+def helper(): return 42" in diff
    assert "app/utils.py" in updated
    assert updated["app/utils.py"] == "def helper(): return 42\n"


def test_diff_generator_delete():
    current_files = {"app/main.py": "print('hello')\n", "app/deprecated.py": "bad\n"}
    changes = [
        ProposedChange(
            file_path="app/deprecated.py",
            operation=ChangeOperation.DELETE,
            original_region="",
            proposed_region="",
            reason="Remove deprecated file",
        )
    ]
    diff, updated = DiffGenerator.apply_changes_to_files(current_files, changes)
    assert "a/app/deprecated.py" in diff
    assert "app/deprecated.py" not in updated


def test_diff_generator_fails_when_original_region_not_found():
    current_files = {"app/main.py": "def run(): return 1\n"}
    changes = [
        ProposedChange(
            file_path="app/main.py",
            operation=ChangeOperation.MODIFY,
            original_region="def non_existent():",
            proposed_region="def run(): return 2",
            reason="Mismatch",
        )
    ]
    with pytest.raises(ValueError, match="original_region was not found"):
        DiffGenerator.apply_changes_to_files(current_files, changes)


# ==============================================================================
# 3. Deterministic Proposal Validator Tests
# ==============================================================================

@pytest.fixture
def sample_proposal_context():
    current_files = {
        "app/main.py": "def compute():\n    return undefined_val\n",
        "tests/test_main.py": "from app.main import compute\ndef test_compute():\n    assert compute() == 10\n",
    }
    manifest_paths = list(current_files.keys())
    allowed_evidence = {"ev-sandbox-err", "ev-static-f821"}
    allowed_reqs = {"REQ-CALC-01"}
    allowed_arch = {"ComputeService"}
    allowed_db = {"ComputeRecord"}

    diagnosis = FailureDiagnosis(
        failure_type=FailureType.TEST_FAILURE,
        title="Pytest failure in compute",
        summary="Summary of the test failure in the pytest test suite.",
        root_cause="The returned calculation value was undefined at line 2.",
        severity=DiagnosticSeverity.ERROR,
        affected_files=["app/main.py"],
        evidence=[
            EvidenceReference(
                evidence_id="ev-sandbox-err",
                source="execution",
                code="AssertionError",
                file_path="tests/test_main.py",
                line=3,
                snippet="assert compute() == 10",
                description="Assertion failure",
            )
        ],
        claims=[
            DiagnosticClaim(
                claim_type=ClaimType.FACT,
                statement="Exit code 1",
                evidence_ids=["ev-sandbox-err"],
            )
        ],
        requirement_links=["REQ-CALC-01"],
        architecture_links=["ComputeService"],
        database_links=["ComputeRecord"],
        suggested_remediation="Return 10 from compute.",
        limitations=[],
        confidence=FailureConfidence.HIGH,
    )

    analysis_input = RemediationProposalInput(
        project_id=uuid.uuid4(),
        workflow_execution_id=uuid.uuid4(),
        diagnosis=diagnosis,
        relevant_files=[
            RelevantSourceFile(
                path="app/main.py",
                content=current_files["app/main.py"],
                selection_reason="Contains failing compute logic",
            )
        ],
        project_manifest=manifest_paths,
        available_requirement_ids=list(allowed_reqs),
        available_architecture_components=list(allowed_arch),
        available_database_entities=list(allowed_db),
        current_artifact_version=1,
    )

    return current_files, analysis_input


def test_validator_accepts_valid_proposal(sample_proposal_context):
    current_files, analysis_input = sample_proposal_context
    candidate = RemediationProposalCandidate(
        title="Initialize compute return variable",
        summary="Defines the return value to resolve NameError.",
        rationale="Function references undefined variable.",
        changes=[
            ProposedChange(
                file_path="app/main.py",
                operation=ChangeOperation.MODIFY,
                original_region="return undefined_val",
                proposed_region="return 10",
                reason="Return fixed calculation result",
                evidence_ids=["ev-sandbox-err"],
            )
        ],
        expected_effect="Test passes with status code 200.",
        verification_plan="Run static analysis and pytest.",
        risk_level=RiskLevel.LOW,
        requirement_links=["REQ-CALC-01"],
        architecture_links=["ComputeService"],
        database_links=["ComputeRecord"],
    )
    result = RemediationProposalValidator.validate(
        candidate=candidate,
        analysis_input=analysis_input,
        current_files=current_files,
    )
    assert result.is_valid is True
    assert len(result.errors) == 0


def test_validator_rejects_hallucinated_file(sample_proposal_context):
    current_files, analysis_input = sample_proposal_context
    candidate = RemediationProposalCandidate(
        title="Fix non-existent file",
        summary="Fix summary describing proposed change.",
        rationale="Fix rationale for non-existent file.",
        changes=[
            ProposedChange(
                file_path="app/hallucinated.py",
                operation=ChangeOperation.MODIFY,
                original_region="something",
                proposed_region="something_else",
                reason="Modify non-existent file",
            )
        ],
        expected_effect="Expected effect of the fix.",
        verification_plan="Run test suite.",
        risk_level=RiskLevel.LOW,
    )
    result = RemediationProposalValidator.validate(
        candidate=candidate,
        analysis_input=analysis_input,
        current_files=current_files,
    )
    assert result.is_valid is False
    assert any("does not exist in project manifest" in err for err in result.errors)


def test_validator_rejects_path_traversal(sample_proposal_context):
    current_files, analysis_input = sample_proposal_context
    candidate = RemediationProposalCandidate(
        title="Fix traversal exploit",
        summary="Summary explaining directory traversal.",
        rationale="Rationale for proposed change.",
        changes=[
            ProposedChange(
                file_path="../etc/passwd",
                operation=ChangeOperation.ADD,
                original_region="",
                proposed_region="malicious",
                reason="Exploit attempt",
            )
        ],
        expected_effect="Expected effect of the fix.",
        verification_plan="Run test suite.",
        risk_level=RiskLevel.HIGH,
    )
    result = RemediationProposalValidator.validate(
        candidate=candidate,
        analysis_input=analysis_input,
        current_files=current_files,
    )
    assert result.is_valid is False
    assert any("traversal" in err.lower() for err in result.errors)


def test_validator_rejects_absolute_path(sample_proposal_context):
    current_files, analysis_input = sample_proposal_context
    candidate = RemediationProposalCandidate(
        title="Fix absolute path",
        summary="Summary explaining absolute path attempt.",
        rationale="Rationale for absolute path attempt.",
        changes=[
            ProposedChange(
                file_path="/var/log/app.log",
                operation=ChangeOperation.ADD,
                original_region="",
                proposed_region="log",
                reason="Exploit attempt",
            )
        ],
        expected_effect="Expected effect of the fix.",
        verification_plan="Run test suite.",
        risk_level=RiskLevel.HIGH,
    )
    result = RemediationProposalValidator.validate(
        candidate=candidate,
        analysis_input=analysis_input,
        current_files=current_files,
    )
    assert result.is_valid is False
    assert any("absolute" in err.lower() for err in result.errors)


def test_validator_rejects_forbidden_env_files(sample_proposal_context):
    current_files, analysis_input = sample_proposal_context
    candidate = RemediationProposalCandidate(
        title="Fix dotenv file",
        summary="Summary explaining secret configuration.",
        rationale="Rationale for adding configuration file.",
        changes=[
            ProposedChange(
                file_path=".env",
                operation=ChangeOperation.ADD,
                original_region="",
                proposed_region="SECRET_KEY=12345",
                reason="Add secrets",
            )
        ],
        expected_effect="Expected effect of the fix.",
        verification_plan="Run test suite.",
        risk_level=RiskLevel.HIGH,
    )
    result = RemediationProposalValidator.validate(
        candidate=candidate,
        analysis_input=analysis_input,
        current_files=current_files,
    )
    assert result.is_valid is False
    assert any("forbidden" in err.lower() for err in result.errors)


def test_validator_rejects_secrets(sample_proposal_context):
    current_files, analysis_input = sample_proposal_context
    candidate = RemediationProposalCandidate(
        title="Fix with hardcoded secret",
        summary="Summary explaining hardcoded secret attempt.",
        rationale="Rationale for proposed credentials.",
        changes=[
            ProposedChange(
                file_path="app/main.py",
                operation=ChangeOperation.MODIFY,
                original_region="return undefined_val",
                proposed_region="api_key = 'ghp_ABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890'\nreturn api_key",
                reason="Hardcode token",
            )
        ],
        expected_effect="Expected effect of the fix.",
        verification_plan="Run test suite.",
        risk_level=RiskLevel.HIGH,
    )
    result = RemediationProposalValidator.validate(
        candidate=candidate,
        analysis_input=analysis_input,
        current_files=current_files,
    )
    assert result.is_valid is False
    assert any("secret pattern" in err.lower() for err in result.errors)


def test_validator_rejects_hallucinated_requirements(sample_proposal_context):
    current_files, analysis_input = sample_proposal_context
    candidate = RemediationProposalCandidate(
        title="Fix compute return",
        summary="Summary explaining valid compute fix.",
        rationale="Rationale for the calculation fix.",
        changes=[
            ProposedChange(
                file_path="app/main.py",
                operation=ChangeOperation.MODIFY,
                original_region="return undefined_val",
                proposed_region="return 10",
                reason="Fix value",
            )
        ],
        expected_effect="Expected effect of the fix.",
        verification_plan="Run test suite.",
        risk_level=RiskLevel.LOW,
        requirement_links=["REQ-IMAGINARY-999"],
    )
    result = RemediationProposalValidator.validate(
        candidate=candidate,
        analysis_input=analysis_input,
        current_files=current_files,
    )
    assert result.is_valid is False
    assert any("REQ-IMAGINARY-999" in err for err in result.errors)


def test_validator_rejects_oversized_patch(sample_proposal_context):
    current_files, analysis_input = sample_proposal_context
    candidate = RemediationProposalCandidate(
        title="Oversized patch proposal",
        summary="Summary for oversized patch content.",
        rationale="Rationale for large file addition.",
        changes=[
            ProposedChange(
                file_path="app/file1.py",
                operation=ChangeOperation.ADD,
                original_region="",
                proposed_region="x" * 30000,
                reason="File 1 addition",
            ),
            ProposedChange(
                file_path="app/file2.py",
                operation=ChangeOperation.ADD,
                original_region="",
                proposed_region="x" * 30000,
                reason="File 2 addition",
            ),
        ],
        expected_effect="Expected effect of the fix.",
        verification_plan="Run test suite.",
        risk_level=RiskLevel.LOW,
    )
    result = RemediationProposalValidator.validate(
        candidate=candidate,
        analysis_input=analysis_input,
        current_files=current_files,
    )
    assert result.is_valid is False
    assert any("exceeds" in err.lower() for err in result.errors)


def test_validator_rejects_duplicate_changes_on_same_file(sample_proposal_context):
    current_files, analysis_input = sample_proposal_context
    candidate = RemediationProposalCandidate(
        title="Duplicate change proposal",
        summary="Summary for duplicate modifications.",
        rationale="Rationale for multiple modifications.",
        changes=[
            ProposedChange(
                file_path="app/main.py",
                operation=ChangeOperation.MODIFY,
                original_region="return undefined_val",
                proposed_region="return 10",
                reason="Fix value 1",
            ),
            ProposedChange(
                file_path="app/main.py",
                operation=ChangeOperation.MODIFY,
                original_region="return undefined_val",
                proposed_region="return 20",
                reason="Fix value 2",
            ),
        ],
        expected_effect="Expected effect of the fix.",
        verification_plan="Run test suite.",
        risk_level=RiskLevel.LOW,
    )
    result = RemediationProposalValidator.validate(
        candidate=candidate,
        analysis_input=analysis_input,
        current_files=current_files,
    )
    assert result.is_valid is False
    assert any("duplicate modification" in err.lower() for err in result.errors)


# ==============================================================================
# 4. Approval State Machine & Application Logic Tests
# ==============================================================================

@pytest.mark.asyncio
async def test_apply_proposal_rejects_unapproved_status():
    """Verify that apply_proposal strictly rejects unapproved proposals (e.g. AWAITING_APPROVAL)."""
    service = RemediationService(
        session=MagicMock(),
        workflow_service=MagicMock(),
        executor=MagicMock(),
        context_engine=MagicMock(),
    )
    proj_id = uuid.uuid4()
    prop_id = uuid.uuid4()

    unapproved_proposal = RemediationProposal(
        proposal_id=prop_id,
        diagnosis_id=str(uuid.uuid4()),
        project_id=proj_id,
        title="Unapproved proposal",
        summary="Summary of unapproved proposal.",
        rationale="Rationale for test.",
        changes=[
            ProposedChange(
                file_path="app/main.py",
                operation=ChangeOperation.MODIFY,
                original_region="x = 1",
                proposed_region="x = 2",
                reason="Fix value",
            )
        ],
        affected_files=["app/main.py"],
        unified_diff="--- a/app/main.py\n+++ b/app/main.py\n",
        expected_effect="Effect of the patch.",
        verification_plan="Run test suite.",
        risk_level=RiskLevel.LOW,
        status=RemediationProposalStatus.AWAITING_APPROVAL,
    )

    service.get_proposal = AsyncMock(return_value=unapproved_proposal)
    service._resolve_target_execution = AsyncMock()

    with pytest.raises(ConflictError, match="must be explicitly APPROVED before application"):
        await service.apply_proposal(project_id=proj_id, proposal_id=prop_id)


@pytest.mark.asyncio
async def test_apply_proposal_rejects_rejected_status():
    """Verify that apply_proposal strictly rejects REJECTED proposals."""
    service = RemediationService(
        session=MagicMock(),
        workflow_service=MagicMock(),
        executor=MagicMock(),
        context_engine=MagicMock(),
    )
    proj_id = uuid.uuid4()
    prop_id = uuid.uuid4()

    rejected_proposal = RemediationProposal(
        proposal_id=prop_id,
        diagnosis_id=str(uuid.uuid4()),
        project_id=proj_id,
        title="Rejected proposal",
        summary="Summary of rejected proposal.",
        rationale="Rationale for test.",
        changes=[
            ProposedChange(
                file_path="app/main.py",
                operation=ChangeOperation.MODIFY,
                original_region="x = 1",
                proposed_region="x = 2",
                reason="Fix value",
            )
        ],
        affected_files=["app/main.py"],
        unified_diff="--- a/app/main.py\n+++ b/app/main.py\n",
        expected_effect="Effect of the patch.",
        verification_plan="Run test suite.",
        risk_level=RiskLevel.LOW,
        status=RemediationProposalStatus.REJECTED,
    )

    service.get_proposal = AsyncMock(return_value=rejected_proposal)
    service._resolve_target_execution = AsyncMock()

    with pytest.raises(ConflictError, match="must be explicitly APPROVED before application"):
        await service.apply_proposal(project_id=proj_id, proposal_id=prop_id)


# ==============================================================================
# 5. Security Audit Tests
# ==============================================================================

def test_remediation_agent_has_no_direct_execution_authority():
    """Verify RemediationProposalAgent does NOT import or use subprocess, os.system, or eval."""
    source = inspect.getsource(RemediationProposalAgent)
    forbidden = ["subprocess", "os.system", "eval(", "exec(", "shutil.rmtree", "docker.sock"]
    for keyword in forbidden:
        assert keyword not in source, f"Forbidden keyword '{keyword}' found in RemediationProposalAgent!"


def test_remediation_service_has_no_host_execution():
    """Verify RemediationService applies patches strictly in-memory and delegates to sandbox."""
    source = inspect.getsource(RemediationService)
    assert "subprocess" not in source
    assert "os.system" not in source
    assert "eval(" not in source
    assert "exec(" not in source
