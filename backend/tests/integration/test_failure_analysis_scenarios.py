"""Integration Scenario Tests for Failure Analysis Agent covering 10 distinct failure modes."""

import uuid
import pytest
from datetime import datetime, timezone

from app.agents.code_generation.contracts import GeneratedFile
from app.agents.execution import AgentExecutor
from app.agents.failure_analysis.agent import FailureAnalysisAgent
from app.agents.failure_analysis.contracts import (
    ClaimType,
    DiagnosticClaim,
    EvidenceReference,
    FailureConfidence,
    FailureDiagnosis,
    FailureType,
)
from app.agents.failure_analysis.service import FailureAnalysisService
from app.agents.providers.mock import MockLLMProvider
from app.sandbox.contracts import ExecutionResult, ExecutionStatus, ExecutionType
from app.sandbox.static_analysis.contracts import (
    DiagnosticCategory,
    DiagnosticSeverity,
    StaticAnalysisResult,
    StaticAnalysisStatus,
    StaticDiagnostic,
)
from app.schemas.context import ProjectContextResponse, RequirementStatistics
from app.schemas.project import ProjectResponse


@pytest.fixture
def base_context():
    project_id = uuid.uuid4()
    now = datetime.now(timezone.utc)
    return ProjectContextResponse(
        project=ProjectResponse(
            id=project_id,
            name="Scenarios Project",
            slug="scenarios-project",
            description="Diagnostic scenarios testing",
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


def make_diagnosis(
    failure_type: FailureType,
    title: str,
    evidence_id: str,
    file_path: str,
    code: str,
    severity: DiagnosticSeverity = DiagnosticSeverity.ERROR,
) -> FailureDiagnosis:
    return FailureDiagnosis(
        failure_type=failure_type,
        title=title,
        summary=f"Diagnostic summary for {title}.",
        root_cause=f"In-depth root cause for {title}.",
        severity=severity,
        affected_files=[file_path],
        evidence=[
            EvidenceReference(
                evidence_id=evidence_id,
                source="static_analysis" if "diag" in evidence_id else "execution",
                code=code,
                file_path=file_path,
                line=1,
            )
        ],
        claims=[
            DiagnosticClaim(
                claim_type=ClaimType.FACT,
                statement=f"Detected {code} in {file_path}.",
                evidence_ids=[evidence_id],
            )
        ],
        suggested_remediation=f"Descriptive remediation steps for resolving {title}.",
        limitations=["Static analysis and execution logs were bounded."],
        confidence=FailureConfidence.HIGH,
    )


# Scenario 1: F821 undefined variable
@pytest.mark.asyncio
async def test_scenario_1_undefined_variable(base_context):
    prov = MockLLMProvider()
    expected = make_diagnosis(FailureType.LINT_ERROR, "Undefined Variable", "diag-f821", "app/main.py", "F821")
    prov.register_structured_response(expected)
    executor = AgentExecutor(provider=prov)
    agent = FailureAnalysisAgent()

    static_res = StaticAnalysisResult(
        analysis_id=uuid.uuid4(),
        project_id=base_context.project.id,
        status=StaticAnalysisStatus.ISSUES_FOUND,
        diagnostics=[
            StaticDiagnostic(
                diagnostic_id="diag-f821",
                category=DiagnosticCategory.LINT,
                severity=DiagnosticSeverity.ERROR,
                code="F821",
                message="undefined name 'token'",
                file_path="app/main.py",
                line=5,
                source="ruff",
            )
        ],
        files_analyzed=1,
        error_count=1,
        summary="F821 error",
    )

    res = await executor.execute(
        agent=agent,
        context=base_context,
        static_analysis_result=static_res,
        code_output=[GeneratedFile(path="app/main.py", content="token = 1", language="python", size_bytes=9)],
    )
    assert res.output.failure_type == FailureType.LINT_ERROR
    assert res.output.evidence[0].code == "F821"


# Scenario 2: F401 unused import
@pytest.mark.asyncio
async def test_scenario_2_unused_import(base_context):
    prov = MockLLMProvider()
    expected = make_diagnosis(FailureType.LINT_ERROR, "Unused Import", "diag-f401", "app/main.py", "F401", DiagnosticSeverity.WARNING)
    prov.register_structured_response(expected)
    executor = AgentExecutor(provider=prov)

    res = await executor.execute(
        agent=FailureAnalysisAgent(),
        context=base_context,
        static_analysis_result=StaticAnalysisResult(
            analysis_id=uuid.uuid4(),
            project_id=base_context.project.id,
            status=StaticAnalysisStatus.ISSUES_FOUND,
            diagnostics=[
                StaticDiagnostic(
                    diagnostic_id="diag-f401",
                    category=DiagnosticCategory.LINT,
                    severity=DiagnosticSeverity.WARNING,
                    code="F401",
                    message="`os` imported but unused",
                    file_path="app/main.py",
                    line=1,
                    source="ruff",
                )
            ],
            files_analyzed=1,
            warning_count=1,
            summary="F401 warning",
        ),
        code_output=[GeneratedFile(path="app/main.py", content="import os", language="python", size_bytes=9)],
    )
    assert res.output.failure_type == FailureType.LINT_ERROR


# Scenario 3: missing dependency
@pytest.mark.asyncio
async def test_scenario_3_missing_dependency(base_context):
    prov = MockLLMProvider()
    expected = make_diagnosis(FailureType.DEPENDENCY_ERROR, "Missing Dependency", "diag-dep", "requirements.txt", "DEP_MISSING")
    prov.register_structured_response(expected)
    executor = AgentExecutor(provider=prov)

    res = await executor.execute(
        agent=FailureAnalysisAgent(),
        context=base_context,
        static_analysis_result=StaticAnalysisResult(
            analysis_id=uuid.uuid4(),
            project_id=base_context.project.id,
            status=StaticAnalysisStatus.ISSUES_FOUND,
            diagnostics=[
                StaticDiagnostic(
                    diagnostic_id="diag-dep",
                    category=DiagnosticCategory.DEPENDENCY,
                    severity=DiagnosticSeverity.WARNING,
                    code="DEP_MISSING",
                    message="Imported 'httpx' is not declared in requirements.txt",
                    file_path="requirements.txt",
                    source="dependency_analyzer",
                )
            ],
            files_analyzed=2,
            warning_count=1,
            summary="DEP_MISSING",
        ),
        code_output=[GeneratedFile(path="requirements.txt", content="fastapi", language="text", size_bytes=7)],
    )
    assert res.output.failure_type == FailureType.DEPENDENCY_ERROR


# Scenario 4: syntax error
@pytest.mark.asyncio
async def test_scenario_4_syntax_error(base_context):
    prov = MockLLMProvider()
    expected = make_diagnosis(FailureType.SYNTAX_ERROR, "Syntax Error in Main", "diag-syn", "app/main.py", "SYNTAX_ERROR")
    prov.register_structured_response(expected)
    executor = AgentExecutor(provider=prov)

    res = await executor.execute(
        agent=FailureAnalysisAgent(),
        context=base_context,
        static_analysis_result=StaticAnalysisResult(
            analysis_id=uuid.uuid4(),
            project_id=base_context.project.id,
            status=StaticAnalysisStatus.VALIDATION_ERROR,
            diagnostics=[
                StaticDiagnostic(
                    diagnostic_id="diag-syn",
                    category=DiagnosticCategory.SYNTAX,
                    severity=DiagnosticSeverity.ERROR,
                    code="SYNTAX_ERROR",
                    message="invalid syntax at line 2",
                    file_path="app/main.py",
                    line=2,
                    source="ast",
                )
            ],
            files_analyzed=1,
            error_count=1,
            summary="Syntax error",
        ),
        code_output=[GeneratedFile(path="app/main.py", content="def broken(\n", language="python", size_bytes=12)],
    )
    assert res.output.failure_type == FailureType.SYNTAX_ERROR


# Scenario 5: failing pytest assertion
@pytest.mark.asyncio
async def test_scenario_5_failing_assertion(base_context):
    prov = MockLLMProvider()
    expected = make_diagnosis(FailureType.ASSERTION_FAILURE, "Pytest Assertion Error", "sandbox_stdout", "tests/test_main.py", "ASSERT_FAIL")
    prov.register_structured_response(expected)
    executor = AgentExecutor(provider=prov)

    res = await executor.execute(
        agent=FailureAnalysisAgent(),
        context=base_context,
        execution_result=ExecutionResult(
            execution_id=uuid.uuid4(),
            project_id=base_context.project.id,
            execution_type=ExecutionType.TEST,
            status=ExecutionStatus.FAILED,
            exit_code=1,
            duration_seconds=0.3,
            stdout="assert 200 == 404",
            stderr="",
            is_truncated=False,
            tests_passed=0,
            tests_failed=1,
            tests_total=1,
            validation_errors=[],
            metadata={},
        ),
        code_output=[GeneratedFile(path="tests/test_main.py", content="def test(): assert 1 == 2", language="python", size_bytes=26)],
    )
    assert res.output.failure_type == FailureType.ASSERTION_FAILURE


# Scenario 6: runtime error
@pytest.mark.asyncio
async def test_scenario_6_runtime_error(base_context):
    prov = MockLLMProvider()
    expected = make_diagnosis(FailureType.RUNTIME_ERROR, "Runtime ZeroDivisionError", "sandbox_stderr", "app/main.py", "ZERO_DIV")
    prov.register_structured_response(expected)
    executor = AgentExecutor(provider=prov)

    res = await executor.execute(
        agent=FailureAnalysisAgent(),
        context=base_context,
        execution_result=ExecutionResult(
            execution_id=uuid.uuid4(),
            project_id=base_context.project.id,
            execution_type=ExecutionType.TEST,
            status=ExecutionStatus.FAILED,
            exit_code=1,
            duration_seconds=0.3,
            stdout="",
            stderr="ZeroDivisionError: division by zero",
            is_truncated=False,
            tests_passed=0,
            tests_failed=1,
            tests_total=1,
            validation_errors=[],
            metadata={},
        ),
        code_output=[GeneratedFile(path="app/main.py", content="x = 1 / 0", language="python", size_bytes=9)],
    )
    assert res.output.failure_type == FailureType.RUNTIME_ERROR


# Scenario 7: timeout
@pytest.mark.asyncio
async def test_scenario_7_timeout(base_context):
    prov = MockLLMProvider()
    expected = make_diagnosis(FailureType.TIMEOUT, "Execution Timeout Exceeded", "exit_code", "app/main.py", "TIMEOUT")
    prov.register_structured_response(expected)
    executor = AgentExecutor(provider=prov)

    res = await executor.execute(
        agent=FailureAnalysisAgent(),
        context=base_context,
        execution_result=ExecutionResult(
            execution_id=uuid.uuid4(),
            project_id=base_context.project.id,
            execution_type=ExecutionType.TEST,
            status=ExecutionStatus.TIMEOUT,
            exit_code=124,
            duration_seconds=30.0,
            stdout="Timeout expired while running tests",
            stderr="",
            is_truncated=False,
            tests_passed=0,
            tests_failed=0,
            tests_total=0,
            validation_errors=[],
            metadata={},
        ),
        code_output=[GeneratedFile(path="app/main.py", content="import time\ntime.sleep(60)", language="python", size_bytes=26)],
    )
    assert res.output.failure_type == FailureType.TIMEOUT


# Scenario 8: sandbox error
@pytest.mark.asyncio
async def test_scenario_8_sandbox_error(base_context):
    prov = MockLLMProvider()
    expected = make_diagnosis(FailureType.SANDBOX_ERROR, "Docker Sandbox Failure", "execution", "app/main.py", "SANDBOX_ERR")
    prov.register_structured_response(expected)
    executor = AgentExecutor(provider=prov)

    res = await executor.execute(
        agent=FailureAnalysisAgent(),
        context=base_context,
        execution_result=ExecutionResult(
            execution_id=uuid.uuid4(),
            project_id=base_context.project.id,
            execution_type=ExecutionType.TEST,
            status=ExecutionStatus.SANDBOX_ERROR,
            exit_code=-1,
            duration_seconds=0.05,
            stdout="",
            stderr="Failed to start sandbox container",
            is_truncated=False,
            tests_passed=0,
            tests_failed=0,
            tests_total=0,
            validation_errors=["Daemon uncontactable"],
            metadata={},
        ),
        code_output=[GeneratedFile(path="app/main.py", content="pass", language="python", size_bytes=4)],
    )
    assert res.output.failure_type == FailureType.SANDBOX_ERROR


# Scenario 9: insufficient evidence
@pytest.mark.asyncio
async def test_scenario_9_insufficient_evidence(base_context):
    prov = MockLLMProvider()
    expected = make_diagnosis(FailureType.UNKNOWN, "Indeterminate Failure", "execution", "app/main.py", "UNKNOWN", DiagnosticSeverity.INFO)
    prov.register_structured_response(expected)
    executor = AgentExecutor(provider=prov)

    res = await executor.execute(
        agent=FailureAnalysisAgent(),
        context=base_context,
        code_output=[GeneratedFile(path="app/main.py", content="pass", language="python", size_bytes=4)],
    )
    assert res.output.failure_type == FailureType.UNKNOWN


# Scenario 10: clean project skips trigger
def test_scenario_10_clean_project_trigger():
    exec_res = ExecutionResult(
        execution_id=uuid.uuid4(),
        project_id=uuid.uuid4(),
        execution_type=ExecutionType.TEST,
        status=ExecutionStatus.PASSED,
        exit_code=0,
        duration_seconds=0.1,
        stdout="passed",
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
        duration_seconds=0.05,
        files_analyzed=1,
        error_count=0,
        warning_count=0,
        summary="Passed cleanly",
    )
    should_run, reason = FailureAnalysisService.should_trigger_analysis(exec_res, static_res)
    assert should_run is False
    assert "zero errors" in reason.lower()
