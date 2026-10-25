"""Unit Tests for Phase 11D Failure Analysis Agent, Contracts, Source Selection, and Validation."""

import uuid
import pytest
from pydantic import ValidationError

from app.agents.code_generation.contracts import GeneratedFile
from app.agents.contracts import ValidationResult
from app.agents.exceptions import AgentValidationError
from app.agents.failure_analysis.contracts import (
    ClaimType,
    DiagnosticClaim,
    EvidenceReference,
    FailureAnalysisInput,
    FailureConfidence,
    FailureDiagnosis,
    FailureType,
    RelevantSourceFile,
)
from app.agents.failure_analysis.service import FailureAnalysisService
from app.agents.failure_analysis.source_selector import SourceSelector
from app.agents.failure_analysis.validator import FailureAnalysisValidator
from app.sandbox.contracts import ExecutionResult, ExecutionStatus
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

def test_failure_diagnosis_valid_contract():
    diag_id = uuid.uuid4()
    diagnosis = FailureDiagnosis(
        diagnosis_id=diag_id,
        failure_type=FailureType.TEST_FAILURE,
        title="Pytest Assertion Failure in Auth Suite",
        summary="A test assertion failed in test_auth.py during sandbox execution.",
        root_cause="The JWT payload does not contain required 'sub' claim.",
        severity=DiagnosticSeverity.ERROR,
        affected_files=["app/auth.py", "tests/test_auth.py"],
        evidence=[
            EvidenceReference(
                evidence_id="diag-1",
                source="static_analysis",
                code="F821",
                file_path="app/auth.py",
                line=42,
                snippet="sub = user.id",
                description="Undefined variable 'user'",
            ),
            EvidenceReference(
                evidence_id="sandbox_stdout",
                source="execution",
                code="ASSERTION_ERROR",
                file_path="tests/test_auth.py",
                line=15,
                snippet="assert response.status_code == 200",
                description="Sandbox pytest assertion error",
            ),
        ],
        claims=[
            DiagnosticClaim(
                claim_type=ClaimType.FACT,
                statement="Sandbox execution exited with exit code 1.",
                evidence_ids=["sandbox_stdout"],
            ),
            DiagnosticClaim(
                claim_type=ClaimType.INTERPRETATION,
                statement="The failure likely stems from an uninitialized user model in auth route.",
                evidence_ids=["diag-1"],
            ),
        ],
        requirement_links=["REQ-01"],
        architecture_links=["AuthService"],
        database_links=["User"],
        suggested_remediation="Initialize user record from repository before generating authorization token.",
        limitations=["Runtime memory states were not observable."],
        confidence=FailureConfidence.HIGH,
    )
    assert diagnosis.diagnosis_id == diag_id
    assert diagnosis.failure_type == FailureType.TEST_FAILURE
    assert len(diagnosis.affected_files) == 2
    assert len(diagnosis.evidence) == 2
    assert diagnosis.confidence == FailureConfidence.HIGH


def test_failure_diagnosis_rejects_invalid_failure_type():
    with pytest.raises(ValidationError):
        FailureDiagnosis(
            failure_type="COMPILATION_MISTAKE",  # Invalid enum
            title="Test",
            summary="Test summary",
            root_cause="Test root cause",
            severity=DiagnosticSeverity.ERROR,
            suggested_remediation="Test remediation",
        )


def test_failure_diagnosis_rejects_invalid_severity():
    with pytest.raises(ValidationError):
        FailureDiagnosis(
            failure_type=FailureType.RUNTIME_ERROR,
            title="Test",
            summary="Test summary",
            root_cause="Test root cause",
            severity="FATAL",  # Invalid enum
            suggested_remediation="Test remediation",
        )


def test_failure_diagnosis_rejects_extra_fields():
    with pytest.raises(ValidationError):
        FailureDiagnosis(
            failure_type=FailureType.RUNTIME_ERROR,
            title="Test",
            summary="Test summary",
            root_cause="Test root cause",
            severity=DiagnosticSeverity.ERROR,
            suggested_remediation="Test remediation",
            unauthorized_field="malicious_payload",
        )


# ==============================================================================
# 2. Output Validator & Anti-Hallucination Tests
# ==============================================================================

@pytest.fixture
def sample_analysis_input():
    return FailureAnalysisInput(
        project_id=uuid.uuid4(),
        all_project_files=["app/main.py", "app/auth.py", "tests/test_auth.py"],
        available_diagnostic_ids=["diag-uuid-1", "diag-uuid-2"],
        available_requirement_ids=["REQ-001", "REQ-002"],
        available_architecture_components=["AuthService", "DatabaseService"],
        available_database_entities=["User", "Session"],
    )


def test_validator_accepts_grounded_diagnosis(sample_analysis_input):
    diagnosis = FailureDiagnosis(
        failure_type=FailureType.LINT_ERROR,
        title="Unused import in main",
        summary="Summary of failure.",
        root_cause="Root cause of unused import.",
        severity=DiagnosticSeverity.WARNING,
        affected_files=["app/main.py"],
        evidence=[
            EvidenceReference(
                evidence_id="diag-uuid-1",
                source="static_analysis",
                code="F401",
                file_path="app/main.py",
                line=1,
            )
        ],
        claims=[
            DiagnosticClaim(
                claim_type=ClaimType.FACT,
                statement="Ruff reported F401 at line 1.",
                evidence_ids=["diag-uuid-1"],
            )
        ],
        requirement_links=["REQ-001"],
        architecture_links=["AuthService"],
        database_links=["User"],
        suggested_remediation="Remove the unused import from top of the file.",
        limitations=["Only static code was checked."],
    )
    val_res = FailureAnalysisValidator.validate(diagnosis, sample_analysis_input)
    assert val_res.is_valid is True
    assert len(val_res.errors) == 0


def test_validator_rejects_hallucinated_file(sample_analysis_input):
    diagnosis = FailureDiagnosis(
        failure_type=FailureType.SYNTAX_ERROR,
        title="Syntax error",
        summary="Detailed summary of syntax failure.",
        root_cause="Detailed root cause of syntax error.",
        severity=DiagnosticSeverity.ERROR,
        affected_files=["app/ghost_file.py"],  # Non-existent file
        suggested_remediation="Fix syntax by correcting missing colon.",
    )
    val_res = FailureAnalysisValidator.validate(diagnosis, sample_analysis_input)
    assert val_res.is_valid is False
    assert any("Hallucinated affected file 'app/ghost_file.py'" in err for err in val_res.errors)


def test_validator_rejects_hallucinated_diagnostic_id(sample_analysis_input):
    diagnosis = FailureDiagnosis(
        failure_type=FailureType.RUNTIME_ERROR,
        title="Runtime error",
        summary="Detailed summary of runtime failure.",
        root_cause="Detailed root cause of runtime error.",
        severity=DiagnosticSeverity.ERROR,
        evidence=[
            EvidenceReference(
                evidence_id="invented-diag-999",  # Hallucinated ID
                source="static_analysis",
                code="E999",
            )
        ],
        suggested_remediation="Fix runtime error by ensuring module is present.",
    )
    val_res = FailureAnalysisValidator.validate(diagnosis, sample_analysis_input)
    assert val_res.is_valid is False
    assert any("Hallucinated evidence reference 'invented-diag-999'" in err for err in val_res.errors)


def test_validator_rejects_hallucinated_requirement_link(sample_analysis_input):
    diagnosis = FailureDiagnosis(
        failure_type=FailureType.RUNTIME_ERROR,
        title="Runtime error",
        summary="Detailed summary of runtime failure.",
        root_cause="Detailed root cause of runtime error.",
        severity=DiagnosticSeverity.ERROR,
        requirement_links=["REQ-FAKE-99"],  # Hallucinated requirement
        suggested_remediation="Fix issue in accordance with specifications.",
    )
    val_res = FailureAnalysisValidator.validate(diagnosis, sample_analysis_input)
    assert val_res.is_valid is False
    assert any("Hallucinated requirement link 'REQ-FAKE-99'" in err for err in val_res.errors)


def test_validator_rejects_hallucinated_architecture_link(sample_analysis_input):
    diagnosis = FailureDiagnosis(
        failure_type=FailureType.RUNTIME_ERROR,
        title="Runtime error",
        summary="Detailed summary of runtime failure.",
        root_cause="Detailed root cause of runtime error.",
        severity=DiagnosticSeverity.ERROR,
        architecture_links=["PaymentMicroservice"],  # Hallucinated component
        suggested_remediation="Fix issue in service implementation.",
    )
    val_res = FailureAnalysisValidator.validate(diagnosis, sample_analysis_input)
    assert val_res.is_valid is False
    assert any("Hallucinated architecture link 'PaymentMicroservice'" in err for err in val_res.errors)


def test_validator_rejects_forbidden_patch_diff(sample_analysis_input):
    diagnosis = FailureDiagnosis(
        failure_type=FailureType.SYNTAX_ERROR,
        title="Syntax error",
        summary="Detailed summary of syntax failure.",
        root_cause="Detailed root cause of syntax error.",
        severity=DiagnosticSeverity.ERROR,
        suggested_remediation="Apply this diff:\ndiff --git a/app/main.py b/app/main.py\n@@ -1,3 +1,3 @@",
    )
    val_res = FailureAnalysisValidator.validate(diagnosis, sample_analysis_input)
    assert val_res.is_valid is False
    assert any("Forbidden code patch formatting detected" in err for err in val_res.errors)


def test_validator_rejects_code_snippet_in_remediation(sample_analysis_input):
    """Verify executable code expressions or statements in remediation are strictly rejected."""
    # Expression 1: return statement expression
    diagnosis1 = FailureDiagnosis(
        failure_type=FailureType.TEST_FAILURE,
        title="Calculation error",
        summary="Detailed summary of test failure.",
        root_cause="Detailed root cause.",
        severity=DiagnosticSeverity.ERROR,
        suggested_remediation="Fix the error by returning return sum(values) from the function.",
    )
    val_res1 = FailureAnalysisValidator.validate(diagnosis1, sample_analysis_input)
    assert val_res1.is_valid is False
    assert any("Forbidden code snippet or statement expression detected" in err for err in val_res1.errors)

    # Expression 2: Fenced code block
    diagnosis2 = FailureDiagnosis(
        failure_type=FailureType.TEST_FAILURE,
        title="Calculation error",
        summary="Detailed summary of test failure.",
        root_cause="Detailed root cause.",
        severity=DiagnosticSeverity.ERROR,
        suggested_remediation="Update function as follows:\n```python\ntotal_sum = sum(values)\n```",
    )
    val_res2 = FailureAnalysisValidator.validate(diagnosis2, sample_analysis_input)
    assert val_res2.is_valid is False
    assert any("Forbidden code snippet or statement expression detected" in err for err in val_res2.errors)


def test_validator_rejects_replace_instruction(sample_analysis_input):
    """Verify 'replace X with Y' source-code replacement instructions are rejected."""
    diagnosis = FailureDiagnosis(
        failure_type=FailureType.TEST_FAILURE,
        title="Calculation error",
        summary="Detailed summary of test failure.",
        root_cause="Detailed root cause.",
        severity=DiagnosticSeverity.ERROR,
        suggested_remediation="In app/calculator.py, replace total_sum with sum(values) to solve the defect.",
    )
    val_res = FailureAnalysisValidator.validate(diagnosis, sample_analysis_input)
    assert val_res.is_valid is False
    assert any("Forbidden source replacement instruction detected" in err for err in val_res.errors)


def test_validator_rejects_add_this_line_instruction(sample_analysis_input):
    """Verify 'add this line' line insertion instructions are rejected."""
    diagnosis = FailureDiagnosis(
        failure_type=FailureType.TEST_FAILURE,
        title="Calculation error",
        summary="Detailed summary of test failure.",
        root_cause="Detailed root cause.",
        severity=DiagnosticSeverity.ERROR,
        suggested_remediation="To resolve the issue, add this line before the return statement: total_sum = 0.",
    )
    val_res = FailureAnalysisValidator.validate(diagnosis, sample_analysis_input)
    assert val_res.is_valid is False
    assert any("Forbidden line insertion instruction detected" in err for err in val_res.errors)


def test_validator_accepts_conceptual_remediation(sample_analysis_input):
    """Verify strictly high-level conceptual and architectural remediation guidance is accepted."""
    conceptual_examples = [
        "Ensure the calculation result is initialized before it is returned.",
        "Correct the undefined variable reference in the calculation path.",
        "Verify that the implementation computes the requested sum before returning the result.",
    ]
    for text in conceptual_examples:
        diagnosis = FailureDiagnosis(
            failure_type=FailureType.TEST_FAILURE,
            title="Calculation error",
            summary="Detailed summary of test failure.",
            root_cause="Detailed root cause.",
            severity=DiagnosticSeverity.ERROR,
            suggested_remediation=text,
        )
        val_res = FailureAnalysisValidator.validate(diagnosis, sample_analysis_input)
        assert val_res.is_valid is True, f"Expected conceptual text to pass: '{text}'. Errors: {val_res.errors}"


# ==============================================================================
# 3. Source Selection & Bounding Tests
# ==============================================================================

def test_source_selection_priority_and_annotation():
    files = [
        GeneratedFile(path="app/main.py", content="import os\ndef root(): pass", language="python", size_bytes=24),
        GeneratedFile(path="app/service.py", content="def calc(x): return x * 2", language="python", size_bytes=26),
        GeneratedFile(path="tests/test_main.py", content="def test_root(): assert 1 == 1", language="python", size_bytes=30),
    ]

    static_res = StaticAnalysisResult(
        analysis_id=uuid.uuid4(),
        project_id=uuid.uuid4(),
        status=StaticAnalysisStatus.ISSUES_FOUND,
        diagnostics=[
            StaticDiagnostic(
                diagnostic_id="d1",
                category=DiagnosticCategory.LINT,
                severity=DiagnosticSeverity.WARNING,
                code="F401",
                message="unused import",
                file_path="app/main.py",
                line=1,
                source="ruff",
            )
        ],
        files_analyzed=3,
        warning_count=1,
        summary="1 warning",
    )

    selected = SourceSelector.select_relevant_source(
        files=files,
        static_analysis=static_res,
        execution_result=None,
    )

    assert len(selected) > 0
    # app/main.py should be first due to diagnostic reference
    assert selected[0].path == "app/main.py"
    assert "1 | import os" in selected[0].content


def test_source_selection_extracts_traceback_files():
    tb_text = """
Traceback (most recent call last):
  File "app/service.py", line 12, in calc
    raise ValueError("invalid value")
ValueError: invalid value
"""
    found = SourceSelector.extract_traceback_files(tb_text, {"app/main.py", "app/service.py"})
    assert "app/service.py" in found
    assert "app/main.py" not in found


def test_source_selection_bounds_max_files():
    files = [
        GeneratedFile(path=f"app/mod_{i}.py", content=f"# Module {i}", language="python", size_bytes=15)
        for i in range(15)
    ]
    selected = SourceSelector.select_relevant_source(files, None, None)
    assert len(selected) <= 10


# ==============================================================================
# 4. Trigger Logic Tests
# ==============================================================================

def test_trigger_logic_clean_run():
    from app.sandbox.contracts import ExecutionType
    exec_res = ExecutionResult(
        execution_id=uuid.uuid4(),
        project_id=uuid.uuid4(),
        execution_type=ExecutionType.TEST,
        status=ExecutionStatus.PASSED,
        exit_code=0,
        duration_seconds=0.5,
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
        project_id=uuid.uuid4(),
        status=StaticAnalysisStatus.PASSED,
        duration_seconds=0.1,
        files_analyzed=2,
        error_count=0,
        warning_count=0,
        summary="All passed",
    )

    should_run, reason = FailureAnalysisService.should_trigger_analysis(exec_res, static_res)
    assert should_run is False
    assert "All execution and static analysis checks passed" in reason


def test_trigger_logic_test_failure():
    from app.sandbox.contracts import ExecutionType
    exec_res = ExecutionResult(
        execution_id=uuid.uuid4(),
        project_id=uuid.uuid4(),
        execution_type=ExecutionType.TEST,
        status=ExecutionStatus.FAILED,
        exit_code=1,
        duration_seconds=0.5,
        stdout="1 failed",
        stderr="",
        is_truncated=False,
        tests_passed=0,
        tests_failed=1,
        tests_total=1,
        validation_errors=[],
        metadata={},
    )
    should_run, reason = FailureAnalysisService.should_trigger_analysis(exec_res, None)
    assert should_run is True
    assert "FAILED" in reason


def test_trigger_logic_static_error():
    static_res = StaticAnalysisResult(
        analysis_id=uuid.uuid4(),
        project_id=uuid.uuid4(),
        status=StaticAnalysisStatus.VALIDATION_ERROR,
        duration_seconds=0.1,
        files_analyzed=2,
        error_count=1,
        syntax_error_count=1,
        summary="Syntax error detected",
    )
    should_run, reason = FailureAnalysisService.should_trigger_analysis(None, static_res)
    assert should_run is True
    assert "VALIDATION_ERROR" in reason


# ==============================================================================
# 5. Agent Execution with MockLLMProvider Tests
# ==============================================================================

@pytest.fixture
def mock_agent_context():
    from app.schemas.context import ProjectContextResponse, RequirementStatistics
    from app.schemas.project import ProjectResponse
    from datetime import datetime, timezone

    project_id = uuid.uuid4()
    now = datetime.now(timezone.utc)
    return ProjectContextResponse(
        project=ProjectResponse(
            id=project_id,
            name="Test Project",
            slug="test-project",
            description="Test project description",
            created_at=now,
            updated_at=now,
        ),
        requirements=[],
        statistics=RequirementStatistics(
            total_requirements=0,
            active_requirements=0,
            functional_count=0,
            non_functional_count=0,
            constraint_count=0,
            by_priority={},
            by_status={},
            completion_percentage=0.0,
        ),
        context_version=1,
        generated_at=now,
    )


@pytest.mark.asyncio
async def test_failure_analysis_agent_mock_execution(mock_agent_context):
    from app.agents.execution import AgentExecutor
    from app.agents.failure_analysis.agent import FailureAnalysisAgent
    from app.agents.providers.mock import MockLLMProvider

    project_id = mock_agent_context.project.id

    expected_diagnosis = FailureDiagnosis(
        failure_type=FailureType.LINT_ERROR,
        title="Unused Variable Detected",
        summary="Variable x was declared but never referenced in function body.",
        root_cause="Developer left exploratory variable in local scope.",
        severity=DiagnosticSeverity.WARNING,
        affected_files=["app/main.py"],
        evidence=[
            EvidenceReference(
                evidence_id="diag-101",
                source="static_analysis",
                code="F841",
                file_path="app/main.py",
                line=3,
            )
        ],
        claims=[
            DiagnosticClaim(
                claim_type=ClaimType.FACT,
                statement="Diagnostic F841 reported at line 3.",
                evidence_ids=["diag-101"],
            )
        ],
        suggested_remediation="Remove unused local variable or prefix with underscore.",
    )

    mock_provider = MockLLMProvider()
    mock_provider.register_structured_response(expected_diagnosis)

    executor = AgentExecutor(provider=mock_provider)
    agent = FailureAnalysisAgent()

    analysis_input = FailureAnalysisInput(
        project_id=project_id,
        all_project_files=["app/main.py"],
        available_diagnostic_ids=["diag-101"],
    )

    result = await executor.execute(
        agent=agent,
        context=mock_agent_context,
        failure_analysis_input=analysis_input,
    )

    assert result.status.value == "COMPLETED"
    assert result.output.failure_type == FailureType.LINT_ERROR
    assert result.output.title == "Unused Variable Detected"
    assert len(mock_provider.call_history) == 1
    assert "DIAGNOSTIC REASONING" in mock_provider.call_history[0].messages[0].content or "Failure Analysis" in mock_provider.call_history[0].messages[0].content


@pytest.mark.asyncio
async def test_failure_analysis_agent_retries_transient_error(mock_agent_context):
    from app.agents.execution import AgentExecutor
    from app.agents.failure_analysis.agent import FailureAnalysisAgent
    from app.agents.providers.mock import MockLLMProvider

    project_id = mock_agent_context.project.id
    context = mock_agent_context

    expected_diagnosis = FailureDiagnosis(
        failure_type=FailureType.TEST_FAILURE,
        title="Pytest failure",
        summary="Unit test failed with assertion error.",
        root_cause="Expected 200 got 500.",
        severity=DiagnosticSeverity.ERROR,
        affected_files=["app/main.py"],
        suggested_remediation="Fix exception handler.",
    )

    mock_provider = MockLLMProvider()
    mock_provider.simulate_transient_failures(1)
    mock_provider.register_structured_response(expected_diagnosis)

    executor = AgentExecutor(provider=mock_provider, max_retries=2)
    agent = FailureAnalysisAgent()

    analysis_input = FailureAnalysisInput(
        project_id=project_id,
        all_project_files=["app/main.py"],
    )

    result = await executor.execute(
        agent=agent,
        context=context,
        failure_analysis_input=analysis_input,
    )

    assert result.status.value == "COMPLETED"
    assert result.output.title == "Pytest failure"
    assert len(mock_provider.call_history) == 2  # 1 transient failure + 1 retry success

