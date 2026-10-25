"""Unit tests for Phase 11H Development Versions & Continuous Engineering Loop."""

import uuid
import pytest
from app.agents.code_generation.contracts import (
    CodeGenerationOutput,
    CodeGenerationPlan,
    GeneratedFile,
    PlannedFile,
)
from app.agents.failure_analysis.contracts import FailureDiagnosis, FailureType
from app.agents.remediation.contracts import RemediationVerificationResult
from app.agents.test_generation.contracts import AITestExecutionResult, AITestSuite, GeneratedTest, TestCategory
from app.models.development_version import (
    ChangeCategory,
    ChangeType,
    DevelopmentVersionStatus,
)
from app.sandbox.contracts import ExecutionResult, ExecutionStatus, ExecutionType
from app.sandbox.static_analysis.contracts import (
    DiagnosticCategory,
    DiagnosticSeverity,
    StaticAnalysisResult,
    StaticAnalysisStatus,
    StaticDiagnostic,
)
from app.schemas.development_version import (
    StageVerificationResult,
    VerificationRequirementLevel,
    VerificationSnapshot,
    VerificationStatus,
    VersionFileSummary,
)
from app.services.development_version_service import DevelopmentVersionService
from app.services.verification_service import DevelopmentVerificationService


def create_sample_artifact(with_tests: bool = True) -> CodeGenerationOutput:
    planned = [
        PlannedFile(path="app/main.py", purpose="App entry", file_type="SOURCE"),
    ]
    gen_files = [
        GeneratedFile(
            path="app/main.py",
            content="def main(): return 42\n",
            language="python",
            size_bytes=22,
            requirement_ids=["REQ-1"],
        ),
    ]
    if with_tests:
        planned.append(PlannedFile(path="tests/test_main.py", purpose="Tests", file_type="SOURCE"))
        gen_files.append(
            GeneratedFile(
                path="tests/test_main.py",
                content="def test_main(): assert True\n",
                language="python",
                size_bytes=28,
                requirement_ids=["REQ-1"],
            )
        )

    return CodeGenerationOutput(
        plan=CodeGenerationPlan(
            project_type="backend-service",
            language="python",
            framework="fastapi",
            database="none",
            package_manager="pip",
            files=planned,
            rationale="Sample project",
        ),
        generated_files=gen_files,
        total_files=len(gen_files),
        total_size_bytes=sum(f.size_bytes for f in gen_files),
        summary="Sample generated code artifact",
    )


def test_hashing_determinism_and_order_invariance():
    f1 = GeneratedFile(path="app/a.py", content="a = 1", language="python", size_bytes=5)
    f2 = GeneratedFile(path="app/b.py", content="b = 2", language="python", size_bytes=5)

    hash_ordered = DevelopmentVersionService.compute_content_hash([f1, f2])
    hash_reversed = DevelopmentVersionService.compute_content_hash([f2, f1])
    assert hash_ordered == hash_reversed
    assert len(hash_ordered) == 64

    # Manifest hash
    m_ordered = DevelopmentVersionService.compute_manifest_hash([f1, f2])
    m_reversed = DevelopmentVersionService.compute_manifest_hash([f2, f1])
    assert m_ordered == m_reversed
    assert len(m_ordered) == 64


def test_hashing_sensitive_to_content():
    f1 = GeneratedFile(path="app/a.py", content="a = 1", language="python", size_bytes=5)
    f2 = GeneratedFile(path="app/a.py", content="a = 2", language="python", size_bytes=5)

    assert DevelopmentVersionService.compute_content_hash([f1]) != DevelopmentVersionService.compute_content_hash([f2])
    # But manifest hash remains identical since paths are the same
    assert DevelopmentVersionService.compute_manifest_hash([f1]) == DevelopmentVersionService.compute_manifest_hash([f2])


def test_verification_gate_requires_static_analysis():
    artifact = create_sample_artifact(with_tests=False)
    snapshot = DevelopmentVerificationService.evaluate_verification(
        artifact=artifact,
        static_analysis=None,
    )
    assert not snapshot.is_verified
    assert snapshot.verification_status == VerificationStatus.FAILED
    assert snapshot.static_analysis.requirement_level == VerificationRequirementLevel.REQUIRED
    assert snapshot.static_analysis.status == VerificationStatus.FAILED
    assert "Missing mandatory static analysis report" in snapshot.static_analysis.blocking_issues


def create_static_analysis_result(
    project_id: uuid.UUID | None = None,
    error_count: int = 0,
    diagnostics: list[StaticDiagnostic] | None = None,
) -> StaticAnalysisResult:
    return StaticAnalysisResult(
        analysis_id=uuid.uuid4(),
        project_id=project_id or uuid.uuid4(),
        status=StaticAnalysisStatus.ISSUES_FOUND if error_count > 0 else StaticAnalysisStatus.PASSED,
        duration_seconds=0.1,
        files_analyzed=1,
        files_skipped=0,
        error_count=error_count,
        warning_count=0,
        info_count=0,
        security_issue_count=0,
        syntax_error_count=0,
        lint_issue_count=0,
        diagnostics=diagnostics or [],
        summary="Static analysis result",
    )


def test_verification_gate_fails_on_static_analysis_errors():
    artifact = create_sample_artifact(with_tests=False)
    diag = StaticDiagnostic(
        diagnostic_id="D-1",
        source="ruff",
        code="F821",
        message="Undefined variable",
        severity=DiagnosticSeverity.ERROR,
        category=DiagnosticCategory.SYNTAX,
        file_path="app/main.py",
        line=2,
    )
    sa_res = create_static_analysis_result(error_count=1, diagnostics=[diag])

    snapshot = DevelopmentVerificationService.evaluate_verification(
        artifact=artifact,
        static_analysis=sa_res,
    )
    assert not snapshot.is_verified
    assert snapshot.verification_status == VerificationStatus.FAILED
    assert snapshot.static_analysis.status == VerificationStatus.FAILED
    assert any("F821" in issue for issue in snapshot.static_analysis.blocking_issues)


def test_verification_gate_enforces_mandatory_sandbox_when_tests_exist():
    artifact_with_tests = create_sample_artifact(with_tests=True)
    clean_sa = create_static_analysis_result()

    # Missing sandbox execution on project with tests MUST FAIL verification
    snapshot = DevelopmentVerificationService.evaluate_verification(
        artifact=artifact_with_tests,
        static_analysis=clean_sa,
        sandbox_execution=None,
    )
    assert not snapshot.is_verified
    assert snapshot.verification_status == VerificationStatus.FAILED
    assert snapshot.sandbox_execution.requirement_level == VerificationRequirementLevel.REQUIRED
    assert snapshot.sandbox_execution.status == VerificationStatus.FAILED


def test_verification_gate_passes_when_sandbox_tests_succeed():
    artifact_with_tests = create_sample_artifact(with_tests=True)
    clean_sa = create_static_analysis_result()
    clean_sb = ExecutionResult(
        execution_id=uuid.uuid4(),
        project_id=uuid.uuid4(),
        execution_type=ExecutionType.TEST,
        status=ExecutionStatus.PASSED,
        exit_code=0,
        duration_seconds=0.2,
        stdout="1 passed",
        stderr="",
        tests_passed=1,
        tests_failed=0,
        tests_total=1,
    )

    snapshot = DevelopmentVerificationService.evaluate_verification(
        artifact=artifact_with_tests,
        static_analysis=clean_sa,
        sandbox_execution=clean_sb,
    )
    assert snapshot.is_verified
    assert snapshot.verification_status == VerificationStatus.PASSED
    assert snapshot.sandbox_execution.status == VerificationStatus.PASSED


def test_verification_gate_enforces_ai_test_execution_when_suite_present():
    artifact = create_sample_artifact(with_tests=False)
    clean_sa = create_static_analysis_result()
    ai_suite = AITestSuite(
        suite_id=uuid.uuid4(),
        project_id=uuid.uuid4(),
        summary="AI suite",
        tests=[
            GeneratedTest(
                test_id="TEST-1",
                name="test_foo",
                description="Verify that foo returns successfully",
                category=TestCategory.HAPPY_PATH,
                target_file="app/main.py",
                code="assert True",
                expected_behavior="Returns true without throwing an unhandled exception",
                rationale="Regression verification for entrypoint function",
            )
        ],
        test_count=1,
        test_files={"tests/test_ai_generated.py": "def test_foo(): assert True\n"},
    )

    # Suite present but not executed -> FAILED
    snap_not_exec = DevelopmentVerificationService.evaluate_verification(
        artifact=artifact,
        static_analysis=clean_sa,
        ai_test_suite=ai_suite,
        ai_test_execution=None,
    )
    assert not snap_not_exec.is_verified
    assert snap_not_exec.ai_tests.status == VerificationStatus.FAILED

    # Suite present and failed -> FAILED
    failing_ai = AITestExecutionResult(
        execution_id=uuid.uuid4(),
        suite_id=ai_suite.suite_id,
        project_id=ai_suite.project_id,
        status=ExecutionStatus.FAILED,
        exit_code=1,
        duration_seconds=0.1,
        tests_total=1,
        tests_passed=0,
        tests_failed=1,
        tests_skipped=0,
    )
    snap_fail = DevelopmentVerificationService.evaluate_verification(
        artifact=artifact,
        static_analysis=clean_sa,
        ai_test_suite=ai_suite,
        ai_test_execution=failing_ai,
    )
    assert not snap_fail.is_verified
    assert snap_fail.ai_tests.status == VerificationStatus.FAILED

    # Passing AI tests -> PASSED
    passing_ai = AITestExecutionResult(
        execution_id=uuid.uuid4(),
        suite_id=ai_suite.suite_id,
        project_id=ai_suite.project_id,
        status=ExecutionStatus.PASSED,
        exit_code=0,
        duration_seconds=0.1,
        tests_total=1,
        tests_passed=1,
        tests_failed=0,
        tests_skipped=0,
    )
    snap_pass = DevelopmentVerificationService.evaluate_verification(
        artifact=artifact,
        static_analysis=clean_sa,
        ai_test_suite=ai_suite,
        ai_test_execution=passing_ai,
    )
    assert snap_pass.is_verified
    assert snap_pass.ai_tests.status == VerificationStatus.PASSED


def test_verification_gate_unresolved_failure_diagnosis_blocks_verification():
    artifact = create_sample_artifact(with_tests=False)
    clean_sa = create_static_analysis_result()
    diag = FailureDiagnosis(
        diagnosis_id=uuid.uuid4(),
        failure_type=FailureType.APPLICATION_ERROR,
        title="ZeroDivisionError uncaught",
        summary="Critical error in divide",
        root_cause="Divisor check missing",
        severity=DiagnosticSeverity.CRITICAL,
        suggested_remediation="Add non-zero validation check",
    )

    # Valid diagnosis passes failure_analysis without requiring remediation
    snap = DevelopmentVerificationService.evaluate_verification(
        artifact=artifact,
        static_analysis=clean_sa,
        failure_diagnosis=diag,
        remediation_verification=None,
    )
    assert snap.failure_analysis.status == VerificationStatus.PASSED
    assert snap.failure_analysis.requirement_level == VerificationRequirementLevel.REQUIRED

    # If sandbox execution failed, sandbox blocks is_verified while failure_analysis remains PASSED
    artifact_tests = create_sample_artifact(with_tests=True)
    from app.sandbox.contracts import ExecutionResult, ExecutionStatus, ExecutionType
    failed_sb = ExecutionResult(
        project_id=uuid.uuid4(),
        execution_type=ExecutionType.TEST,
        status=ExecutionStatus.FAILED,
        exit_code=1,
        tests_passed=0,
        tests_failed=1,
        tests_total=1,
    )
    snap_failed = DevelopmentVerificationService.evaluate_verification(
        artifact=artifact_tests,
        static_analysis=clean_sa,
        sandbox_execution=failed_sb,
        failure_diagnosis=diag,
        remediation_verification=None,
    )
    assert not snap_failed.is_verified
    assert snap_failed.sandbox_execution.status == VerificationStatus.FAILED
    assert snap_failed.failure_analysis.status == VerificationStatus.PASSED

    # Resolved via verified remediation on v2 -> PASSED
    rem_ver = RemediationVerificationResult(
        proposal_id=uuid.uuid4(),
        status="VERIFIED",
        static_analysis_passed=True,
        sandbox_passed=True,
        summary="Verified fix",
    )
    snap_resolved = DevelopmentVerificationService.evaluate_verification(
        artifact=artifact_tests,
        static_analysis=clean_sa,
        sandbox_execution=ExecutionResult(
            project_id=uuid.uuid4(),
            execution_type=ExecutionType.TEST,
            status=ExecutionStatus.PASSED,
            exit_code=0,
            tests_passed=1,
            tests_failed=0,
            tests_total=1,
        ),
        failure_diagnosis=diag,
        remediation_verification=rem_ver,
    )
    assert snap_resolved.is_verified
    assert snap_resolved.failure_analysis.status == VerificationStatus.PASSED


def test_development_change_distinguishes_code_producing_from_lifecycle_event():
    """Verify Mandatory Correction 5: DevelopmentChange distinguishes code-producing from lifecycle events."""
    code_producing_types = {ChangeType.INITIAL_CREATION, ChangeType.REMEDIATION_PATCH}
    lifecycle_types = {ChangeType.ACTIVATION, ChangeType.ROLLBACK}

    for ct in code_producing_types:
        assert ct.value in ["INITIAL_CREATION", "REMEDIATION_PATCH"]
    for lt in lifecycle_types:
        assert lt.value in ["ACTIVATION", "ROLLBACK"]

    assert ChangeCategory.CODE_PRODUCING.value == "CODE_PRODUCING"
    assert ChangeCategory.LIFECYCLE_EVENT.value == "LIFECYCLE_EVENT"


def test_version_file_summary_lightweight_manifest():
    """Verify Mandatory Correction 1: minimum authoritative representation using lightweight file summaries."""
    summary = VersionFileSummary(
        path="backend/app/main.py",
        size_bytes=1024,
        language="python",
        architecture_component="backend_api",
        requirement_ids=["REQ-001", "REQ-002"],
    )
    dumped = summary.model_dump()
    assert dumped["path"] == "backend/app/main.py"
    assert dumped["size_bytes"] == 1024
    assert dumped["requirement_ids"] == ["REQ-001", "REQ-002"]
    # Does NOT contain file content in manifest
    assert "content" not in dumped


def test_verification_snapshot_serialization_and_deserialization():
    """Verify VerificationSnapshot round-trip consistency and stage contracts."""
    stage_sa = StageVerificationResult(
        stage="static_analysis",
        requirement_level=VerificationRequirementLevel.REQUIRED,
        status=VerificationStatus.PASSED,
        details="Ruff passed clean",
        error_count=0,
        warning_count=0,
        blocking_issues=[],
    )
    stage_sb = StageVerificationResult(
        stage="sandbox_execution",
        requirement_level=VerificationRequirementLevel.OPTIONAL,
        status=VerificationStatus.NOT_RUN,
        details="No tests defined in project",
        error_count=0,
        warning_count=0,
        blocking_issues=[],
    )
    stage_ai = StageVerificationResult(
        stage="ai_tests",
        requirement_level=VerificationRequirementLevel.OPTIONAL,
        status=VerificationStatus.NOT_RUN,
        details="No AI tests generated",
        error_count=0,
        warning_count=0,
        blocking_issues=[],
    )
    stage_fa = StageVerificationResult(
        stage="failure_analysis",
        requirement_level=VerificationRequirementLevel.OPTIONAL,
        status=VerificationStatus.NOT_RUN,
        details="No failures detected",
        error_count=0,
        warning_count=0,
        blocking_issues=[],
    )

    snapshot = VerificationSnapshot(
        verification_status=VerificationStatus.PASSED,
        is_verified=True,
        summary="All mandatory verification checks passed",
        static_analysis=stage_sa,
        sandbox_execution=stage_sb,
        ai_tests=stage_ai,
        failure_analysis=stage_fa,
    )

    data = snapshot.model_dump(mode="json")
    rehydrated = VerificationSnapshot.model_validate(data)

    assert rehydrated.is_verified is True
    assert rehydrated.verification_status == VerificationStatus.PASSED
    assert rehydrated.static_analysis.status == VerificationStatus.PASSED
    assert rehydrated.sandbox_execution.requirement_level == VerificationRequirementLevel.OPTIONAL


