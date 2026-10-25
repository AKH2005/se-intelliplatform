"""Unit tests for Phase 11G: AI Test Failure Analysis & Unified Verification."""

import uuid
from datetime import datetime, timezone
import pytest

from app.agents.contracts import AgentType, ValidationResult
from app.agents.failure_analysis.agent import FailureAnalysisAgent
from app.agents.failure_analysis.contracts import (
    ClaimType,
    DiagnosticClaim,
    DiagnosticSeverity,
    EvidenceReference,
    FailureConfidence,
    FailureDiagnosis,
    FailureSource,
    FailureType,
    UnifiedFailureAnalysisInput,
)
from app.agents.failure_analysis.prompts import build_failure_analysis_prompt
from app.agents.failure_analysis.source_selector import SourceSelector
from app.agents.failure_analysis.validator import FailureAnalysisValidator
from app.agents.code_generation.contracts import GeneratedFile
from app.agents.test_generation.contracts import (
    AITestCaseResult,
    AITestExecutionResult,
    AITestSuite,
    GeneratedTest,
    TestCategory,
)
from app.sandbox.contracts import ExecutionStatus
from app.schemas.context import (
    ProjectContextResponse,
    RequirementStatistics,
)
from app.schemas.project import ProjectResponse


@pytest.fixture
def sample_project_context() -> ProjectContextResponse:
    pid = uuid.uuid4()
    return ProjectContextResponse(
        project=ProjectResponse(
            id=pid,
            name="Calculator Service",
            slug="calculator-service",
            description="Mathematical service",
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        ),
        requirements=[],
        statistics=RequirementStatistics(
            total_requirements=0,
            active_requirements=0,
            functional_count=0,
            non_functional_count=0,
            constraint_count=0,
            completion_percentage=0.0,
        ),
        context_version=1,
        generated_at=datetime.now(timezone.utc),
    )


@pytest.fixture
def sample_ai_test_suite() -> AITestSuite:
    suite_id = uuid.uuid4()
    pid = uuid.uuid4()
    return AITestSuite(
        suite_id=suite_id,
        project_id=pid,
        summary="AI-generated test suite for calculator",
        tests=[
            GeneratedTest(
                test_id="TEST-001",
                name="test_divide_by_zero_raises",
                description="Verifies divide by zero raises ValueError",
                category=TestCategory.ERROR_HANDLING,
                target_file="app/calculator.py",
                target_symbol="divide",
                requirement_ids=["REQ-001"],
                architecture_component="core",
                rationale="Defensive programming requirement",
                code="def test_divide_by_zero_raises():\n    with pytest.raises(ValueError):\n        divide(10, 0)",
                expected_behavior="Raises ValueError on zero denominator",
            ),
            GeneratedTest(
                test_id="TEST-002",
                name="test_addition_valid",
                description="Verifies addition returns sum",
                category=TestCategory.HAPPY_PATH,
                target_file="app/calculator.py",
                target_symbol="add",
                requirement_ids=["REQ-001"],
                architecture_component="core",
                rationale="Basic arithmetic correctness",
                code="def test_addition_valid():\n    assert add(2, 3) == 5",
                expected_behavior="Returns 5",
            ),
        ],
        test_count=2,
        requirement_traceability={"REQ-001": ["TEST-001", "TEST-002"]},
        source_artifact_reference="code_generation",
        test_files={"tests/test_ai_generated.py": "def test_divide_by_zero_raises(): pass\ndef test_addition_valid(): pass"},
    )


@pytest.fixture
def sample_failing_ai_test_exec(sample_ai_test_suite: AITestSuite) -> AITestExecutionResult:
    return AITestExecutionResult(
        execution_id=uuid.uuid4(),
        suite_id=sample_ai_test_suite.suite_id,
        project_id=sample_ai_test_suite.project_id,
        status=ExecutionStatus.FAILED,
        exit_code=1,
        duration_seconds=1.45,
        tests_total=2,
        tests_passed=1,
        tests_failed=1,
        tests_skipped=0,
        stdout=(
            "tests/test_ai_generated.py::test_addition_valid PASSED [ 50%]\n"
            "tests/test_ai_generated.py::test_divide_by_zero_raises FAILED [100%]\n\n"
            "=== FAILURES ===\n"
            "_ test_divide_by_zero_raises _\n"
            "tests/test_ai_generated.py:12: in test_divide_by_zero_raises\n"
            "    divide(10, 0)\n"
            "app/calculator.py:25: in divide\n"
            "    return a / b\n"
            "E   ZeroDivisionError: division by zero\n"
            "=== 1 failed, 1 passed in 0.42s ==="
        ),
        stderr="",
        failure_summaries=[
            "ZeroDivisionError: division by zero at app/calculator.py:25 in divide"
        ],
        test_results=[
            AITestCaseResult(name="test_addition_valid", status="PASSED", duration_seconds=0.01),
            AITestCaseResult(name="test_divide_by_zero_raises", status="FAILED", duration_seconds=0.02, message="ZeroDivisionError: division by zero"),
        ],
    )


def test_failure_source_enum():
    """Verify all failure sources exist and are strongly typed."""
    assert FailureSource.AI_TEST == "AI_TEST"
    assert FailureSource.STATIC_ANALYSIS == "STATIC_ANALYSIS"
    assert FailureSource.SANDBOX == "SANDBOX"
    assert FailureSource.APPLICATION == "APPLICATION"
    assert FailureSource.VALIDATION == "VALIDATION"
    assert FailureSource.ENVIRONMENT == "ENVIRONMENT"
    assert FailureSource.DEPENDENCY == "DEPENDENCY"


def test_extended_failure_taxonomy():
    """Verify controlled failure taxonomy includes both baseline and extended categories."""
    assert FailureType.TEST_FAILURE == "TEST_FAILURE"
    assert FailureType.ASSERTION_FAILURE == "ASSERTION_FAILURE"
    assert FailureType.TEST_ERROR == "TEST_ERROR"
    assert FailureType.APPLICATION_ERROR == "APPLICATION_ERROR"
    assert FailureType.STATIC_ANALYSIS_ISSUE == "STATIC_ANALYSIS_ISSUE"
    assert FailureType.ENVIRONMENT_ERROR == "ENVIRONMENT_ERROR"
    assert FailureType.TIMEOUT == "TIMEOUT"
    assert FailureType.RESOURCE_LIMIT == "RESOURCE_LIMIT"
    assert FailureType.SANDBOX_ERROR == "SANDBOX_ERROR"
    assert FailureType.VALIDATION_ERROR == "VALIDATION_ERROR"
    assert FailureType.UNKNOWN == "UNKNOWN"


def test_unified_failure_analysis_input_instantiation(
    sample_ai_test_suite: AITestSuite,
    sample_failing_ai_test_exec: AITestExecutionResult,
):
    """Verify UnifiedFailureAnalysisInput encapsulates AI test execution artifacts cleanly."""
    inp = UnifiedFailureAnalysisInput(
        project_id=sample_ai_test_suite.project_id,
        ai_test_execution_result=sample_failing_ai_test_exec,
        ai_test_suite=sample_ai_test_suite,
        failure_source=FailureSource.AI_TEST,
        all_project_files=["app/calculator.py", "app/main.py"],
        available_test_ids=["TEST-001", "test_divide_by_zero_raises"],
        available_requirement_ids=["REQ-001"],
    )

    assert inp.failure_source == FailureSource.AI_TEST
    assert inp.ai_test_execution_result.tests_failed == 1
    assert "TEST-001" in inp.available_test_ids


def test_source_selector_prioritizes_failing_ai_test_target(
    sample_ai_test_suite: AITestSuite,
    sample_failing_ai_test_exec: AITestExecutionResult,
):
    """Verify SourceSelector prioritizes the target file and traceback of the failing AI test."""
    files = [
        GeneratedFile(
            path="app/calculator.py",
            content="def add(a, b):\n    return a + b\n\ndef divide(a, b):\n    return a / b\n",
            language="python",
            size_bytes=80,
            architecture_component="core",
            requirement_ids=["REQ-001"],
        ),
        GeneratedFile(
            path="app/main.py",
            content="from app.calculator import add\nprint(add(1, 2))\n",
            language="python",
            size_bytes=50,
            architecture_component="entrypoint",
            requirement_ids=["REQ-001"],
        ),
    ]

    selected = SourceSelector.select_relevant_source(
        files=files,
        ai_test_execution_result=sample_failing_ai_test_exec,
        ai_test_suite=sample_ai_test_suite,
    )

    assert len(selected) >= 1
    first_path = selected[0].path
    assert first_path == "app/calculator.py"
    assert "Target application file for failing AI test" in selected[0].selection_reason


def test_validator_accepts_valid_ai_test_evidence(
    sample_ai_test_suite: AITestSuite,
    sample_failing_ai_test_exec: AITestExecutionResult,
):
    """Verify FailureAnalysisValidator accepts evidence referencing AI test IDs and outputs."""
    inp = UnifiedFailureAnalysisInput(
        project_id=sample_ai_test_suite.project_id,
        ai_test_execution_result=sample_failing_ai_test_exec,
        ai_test_suite=sample_ai_test_suite,
        failure_source=FailureSource.AI_TEST,
        all_project_files=["app/calculator.py"],
        available_test_ids=["TEST-001", "test_divide_by_zero_raises"],
        available_requirement_ids=["REQ-001"],
        available_architecture_components=["core"],
    )

    diagnosis = FailureDiagnosis(
        failure_type=FailureType.TEST_FAILURE,
        failure_source=FailureSource.AI_TEST,
        title="ZeroDivisionError in Calculator Division Handler",
        summary="Test test_divide_by_zero_raises failed with ZeroDivisionError instead of expected ValueError.",
        root_cause="The divide function lacks a denominator check and delegates directly to Python division operator.",
        severity=DiagnosticSeverity.ERROR,
        affected_files=["app/calculator.py"],
        evidence=[
            EvidenceReference(
                evidence_id="TEST-001",
                source="ai_test",
                code="test_divide_by_zero_raises",
                file_path="app/calculator.py",
                line=25,
                snippet="return a / b",
                description="Test expects handled ValueError upon zero denominator",
            ),
            EvidenceReference(
                evidence_id="ai_test_stdout",
                source="execution",
                description="Traceback output from pytest run",
            ),
        ],
        claims=[
            DiagnosticClaim(
                claim_type=ClaimType.FACT,
                statement="Test TEST-001 failed with ZeroDivisionError during division by zero.",
                evidence_ids=["TEST-001"],
            ),
            DiagnosticClaim(
                claim_type=ClaimType.INTERPRETATION,
                statement="The divide method does not validate the input denominator before calculation.",
                evidence_ids=["TEST-001", "ai_test_stdout"],
            ),
            DiagnosticClaim(
                claim_type=ClaimType.RECOMMENDATION,
                statement="Introduce validation for zero divisor and raise the required exception.",
                evidence_ids=[],
            ),
        ],
        requirement_links=["REQ-001"],
        architecture_links=["core"],
        database_links=[],
        suggested_remediation="Verify that the denominator is non-zero before attempting arithmetic division.",
        limitations=["Analysis based on pytest execution traceback and target file content."],
        confidence=FailureConfidence.HIGH,
    )

    res = FailureAnalysisValidator.validate(diagnosis, inp)
    assert res.is_valid, f"Validation failed unexpectedly: {res.errors}"


def test_validator_rejects_hallucinated_test_id(
    sample_ai_test_suite: AITestSuite,
    sample_failing_ai_test_exec: AITestExecutionResult,
):
    """Verify validator strictly rejects fabricated/hallucinated test IDs."""
    inp = UnifiedFailureAnalysisInput(
        project_id=sample_ai_test_suite.project_id,
        ai_test_execution_result=sample_failing_ai_test_exec,
        ai_test_suite=sample_ai_test_suite,
        failure_source=FailureSource.AI_TEST,
        all_project_files=["app/calculator.py"],
        available_test_ids=["TEST-001"],
    )

    diagnosis = FailureDiagnosis(
        failure_type=FailureType.TEST_FAILURE,
        title="ZeroDivisionError",
        summary="Test failure observed.",
        root_cause="Divisor check missing.",
        severity=DiagnosticSeverity.ERROR,
        affected_files=["app/calculator.py"],
        evidence=[
            EvidenceReference(
                evidence_id="HALLUCINATED-TEST-999",
                source="ai_test",
                description="Non-existent test reference",
            ),
        ],
        claims=[],
        suggested_remediation="Validate denominator conceptually.",
    )

    res = FailureAnalysisValidator.validate(diagnosis, inp)
    assert not res.is_valid
    assert any("HALLUCINATED-TEST-999" in err for err in res.errors)


def test_validator_rejects_code_patch_in_remediation():
    """Verify strict read-only boundary rejecting code patches and replacement directives."""
    inp = UnifiedFailureAnalysisInput(
        project_id=uuid.uuid4(),
        all_project_files=["app/calculator.py"],
    )

    diagnosis = FailureDiagnosis(
        failure_type=FailureType.TEST_FAILURE,
        title="ZeroDivisionError",
        summary="Test failure observed.",
        root_cause="Divisor check missing.",
        severity=DiagnosticSeverity.ERROR,
        affected_files=["app/calculator.py"],
        evidence=[],
        claims=[],
        suggested_remediation="replace the body with return a / b if b != 0 else 0",
    )

    res = FailureAnalysisValidator.validate(diagnosis, inp)
    assert not res.is_valid
    assert any("Forbidden" in err for err in res.errors)


def test_prompt_builder_includes_ai_test_sections(
    sample_ai_test_suite: AITestSuite,
    sample_failing_ai_test_exec: AITestExecutionResult,
):
    """Verify build_failure_analysis_prompt embeds AI test execution logs and test definitions."""
    inp = UnifiedFailureAnalysisInput(
        project_id=sample_ai_test_suite.project_id,
        ai_test_execution_result=sample_failing_ai_test_exec,
        ai_test_suite=sample_ai_test_suite,
        failure_source=FailureSource.AI_TEST,
        all_project_files=["app/calculator.py"],
        available_test_ids=["TEST-001", "test_divide_by_zero_raises"],
    )

    prompt = build_failure_analysis_prompt(inp)
    assert "AI-GENERATED TEST EXECUTION EVIDENCE" in prompt
    assert "ZeroDivisionError" in prompt
    assert "test_divide_by_zero_raises" in prompt
    assert "TEST-001" in prompt
    assert "Primary Failure Source: AI_TEST" in prompt


def test_service_should_trigger_analysis_on_ai_test_failure(
    sample_failing_ai_test_exec: AITestExecutionResult,
):
    """Verify FailureAnalysisService.should_trigger_analysis detects failed AI tests."""
    from app.agents.failure_analysis.service import FailureAnalysisService

    # 1. AI tests failed
    should_run, reason = FailureAnalysisService.should_trigger_analysis(
        execution_result=None,
        static_analysis_result=None,
        ai_test_execution_result=sample_failing_ai_test_exec,
    )
    assert should_run is True
    assert "AI test execution" in reason

    # 2. All clean
    passing_ai_test = sample_failing_ai_test_exec.model_copy(
        update={"status": ExecutionStatus.PASSED, "exit_code": 0, "tests_failed": 0, "tests_passed": 2}
    )
    should_run_clean, _ = FailureAnalysisService.should_trigger_analysis(
        execution_result=None,
        static_analysis_result=None,
        ai_test_execution_result=passing_ai_test,
    )
    assert should_run_clean is False


@pytest.mark.asyncio
async def test_agent_analyze_extracts_ai_tests_from_kwargs(
    sample_project_context: ProjectContextResponse,
    sample_ai_test_suite: AITestSuite,
    sample_failing_ai_test_exec: AITestExecutionResult,
):
    """Verify FailureAnalysisAgent.analyze constructs FailureAnalysisInput with AI test context."""
    agent = FailureAnalysisAgent()
    await agent.initialize()

    result = await agent.analyze(
        sample_project_context,
        ai_test_execution=sample_failing_ai_test_exec,
        ai_test_suite=sample_ai_test_suite,
        failure_source=FailureSource.AI_TEST,
    )

    inp = result["analysis_input"]
    assert inp.failure_source == FailureSource.AI_TEST
    assert inp.ai_test_execution_result == sample_failing_ai_test_exec
    assert "TEST-001" in inp.available_test_ids
    assert "test_divide_by_zero_raises" in inp.available_test_ids


def test_validator_rejects_nonexistent_file_path(
    sample_ai_test_suite: AITestSuite,
    sample_failing_ai_test_exec: AITestExecutionResult,
):
    """Verify validator strictly rejects nonexistent file references."""
    inp = UnifiedFailureAnalysisInput(
        project_id=sample_ai_test_suite.project_id,
        ai_test_execution_result=sample_failing_ai_test_exec,
        ai_test_suite=sample_ai_test_suite,
        failure_source=FailureSource.AI_TEST,
        all_project_files=["app/calculator.py"],
        available_test_ids=["TEST-001"],
    )

    diagnosis = FailureDiagnosis(
        failure_type=FailureType.TEST_FAILURE,
        title="ZeroDivisionError",
        summary="Test failure observed.",
        root_cause="Divisor check missing.",
        severity=DiagnosticSeverity.ERROR,
        affected_files=["app/nonexistent_file.py"],
        evidence=[],
        claims=[],
        suggested_remediation="Validate denominator conceptually.",
    )

    res = FailureAnalysisValidator.validate(diagnosis, inp)
    assert not res.is_valid
    assert any("app/nonexistent_file.py" in err for err in res.errors)

