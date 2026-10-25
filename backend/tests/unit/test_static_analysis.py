"""Unit Tests for Static Analysis Contracts, AST Analysis, Dependency Analysis, and Test Discovery."""

import uuid
import pytest
from pydantic import ValidationError

from app.sandbox.static_analysis.ast_analyzer import ASTAnalyzer
from app.sandbox.static_analysis.contracts import (
    DiagnosticCategory,
    DiagnosticSeverity,
    StaticAnalysisRequest,
    StaticAnalysisResult,
    StaticAnalysisStatus,
    StaticDiagnostic,
)
from app.sandbox.static_analysis.dependency_analyzer import DependencyAnalyzer
from app.sandbox.static_analysis.ruff_analyzer import RuffAnalyzer
from app.sandbox.static_analysis.test_discovery import TestDiscovery
from app.sandbox.mock_executor import MockSandboxExecutor
from tests.unit.test_sandbox import make_valid_code_output


# ==============================================================================
# 1. Contract Tests
# ==============================================================================

def test_static_diagnostic_valid():
    diag = StaticDiagnostic(
        category=DiagnosticCategory.LINT,
        severity=DiagnosticSeverity.WARNING,
        code="F401",
        message="`os` imported but unused",
        file_path="app/main.py",
        line=1,
        column=8,
        source="ruff",
        evidence="import os",
        metadata={"url": "https://docs.astral.sh/ruff/rules/unused-import"},
    )
    assert diag.code == "F401"
    assert diag.severity == DiagnosticSeverity.WARNING
    assert diag.category == DiagnosticCategory.LINT
    assert diag.line == 1


def test_static_diagnostic_invalid_severity():
    with pytest.raises(ValidationError):
        StaticDiagnostic(
            category=DiagnosticCategory.LINT,
            severity="FATAL",  # Invalid enum
            code="F401",
            message="Test",
            source="ruff",
        )


def test_static_diagnostic_invalid_category():
    with pytest.raises(ValidationError):
        StaticDiagnostic(
            category="COMPILER",  # Invalid enum
            severity=DiagnosticSeverity.ERROR,
            code="ERR01",
            message="Test",
            source="custom",
        )


def test_static_diagnostic_rejects_extra_fields():
    with pytest.raises(ValidationError):
        StaticDiagnostic(
            category=DiagnosticCategory.LINT,
            severity=DiagnosticSeverity.WARNING,
            code="F401",
            message="Test",
            source="ruff",
            unapproved_extra_field="malicious",  # Extra field forbidden
        )


# ==============================================================================
# 2. AST Analysis Tests
# ==============================================================================

def test_ast_analyzer_valid_python():
    analyzer = ASTAnalyzer()
    code = """
import os
from math import sqrt

class Calculator:
    def add(self, a: int, b: int) -> int:
        return a + b
"""
    data, diags = analyzer.analyze_file("app/calc.py", code)
    assert len(diags) == 0
    assert len(data.functions) == 1
    assert data.functions[0][0] == "add"
    assert len(data.classes) == 1
    assert data.classes[0][0] == "Calculator"
    assert len(data.imports) == 2


def test_ast_analyzer_syntax_error():
    analyzer = ASTAnalyzer()
    code = "def broken(:\n    pass\n"
    data, diags = analyzer.analyze_file("app/broken.py", code)
    assert len(diags) == 1
    assert diags[0].category == DiagnosticCategory.SYNTAX
    assert diags[0].severity == DiagnosticSeverity.ERROR
    assert diags[0].code == "SYNTAX_ERROR"
    assert diags[0].line == 1


def test_ast_analyzer_dangerous_eval():
    analyzer = ASTAnalyzer()
    code = "x = eval('2 + 2')\n"
    data, diags = analyzer.analyze_file("app/eval.py", code)
    assert len(diags) == 1
    assert diags[0].category == DiagnosticCategory.SECURITY
    assert diags[0].severity == DiagnosticSeverity.CRITICAL
    assert diags[0].code == "FORBIDDEN_CALL"
    assert diags[0].line == 1


def test_ast_analyzer_dangerous_exec():
    analyzer = ASTAnalyzer()
    code = "exec('import sys; sys.exit(0)')\n"
    data, diags = analyzer.analyze_file("app/exec.py", code)
    assert len(diags) == 1
    assert diags[0].category == DiagnosticCategory.SECURITY
    assert diags[0].severity == DiagnosticSeverity.CRITICAL
    assert diags[0].code == "FORBIDDEN_CALL"
    assert diags[0].line == 1


# ==============================================================================
# 3. Dependency Analysis Tests
# ==============================================================================

def test_dependency_analyzer_clean_stdlib_and_declared():
    ast_analyzer = ASTAnalyzer()
    dep_analyzer = DependencyAnalyzer()

    code = """
import os
import sys
from typing import List
import fastapi
from pydantic import BaseModel
from app.services import user_service
"""
    data, _ = ast_analyzer.analyze_file("app/main.py", code)
    reqs = "fastapi==0.115.0\npydantic>=2.0.0\n"

    diags = dep_analyzer.analyze(
        modules=[data],
        all_file_paths=["app/main.py", "app/services.py"],
        requirements_content=reqs,
    )
    # Zero missing dependency diagnostics
    assert len(diags) == 0


def test_dependency_analyzer_missing_third_party():
    ast_analyzer = ASTAnalyzer()
    dep_analyzer = DependencyAnalyzer()

    code = """
import httpx
import redis
"""
    data, _ = ast_analyzer.analyze_file("app/client.py", code)
    reqs = "fastapi==0.115.0\n"  # Missing httpx and redis

    diags = dep_analyzer.analyze(
        modules=[data],
        all_file_paths=["app/client.py"],
        requirements_content=reqs,
    )
    assert len(diags) == 2
    assert all(d.code == "DEP_MISSING" for d in diags)
    assert all(d.category == DiagnosticCategory.DEPENDENCY for d in diags)
    assert all(d.severity == DiagnosticSeverity.WARNING for d in diags)


def test_dependency_analyzer_missing_requirements_file():
    ast_analyzer = ASTAnalyzer()
    dep_analyzer = DependencyAnalyzer()

    data, _ = ast_analyzer.analyze_file("app/main.py", "import os\n")
    diags = dep_analyzer.analyze(
        modules=[data],
        all_file_paths=["app/main.py"],
        requirements_content=None,
    )
    assert len(diags) == 1
    assert diags[0].code == "STRUCT_MISSING_REQUIREMENTS"
    assert diags[0].severity == DiagnosticSeverity.WARNING


# ==============================================================================
# 4. Test Discovery Tests
# ==============================================================================

def test_test_discovery_identifies_test_functions():
    ast_analyzer = ASTAnalyzer()
    discovery = TestDiscovery()

    code_app = "def add(a, b): return a + b\n"
    code_test = """
def test_addition():
    assert 1 + 1 == 2

def test_subtraction():
    assert 2 - 1 == 1

class TestCalculator:
    def test_mult(self):
        assert 2 * 2 == 4
"""
    data_app, _ = ast_analyzer.analyze_file("app/main.py", code_app)
    data_test, _ = ast_analyzer.analyze_file("tests/test_main.py", code_test)

    test_files, total_tests, diags = discovery.discover([data_app, data_test])
    assert test_files == ["tests/test_main.py"]
    assert total_tests == 3
    assert len(diags) == 1
    assert diags[0].code == "TEST_DISCOVERED"
    assert diags[0].severity == DiagnosticSeverity.INFO


def test_test_discovery_warns_when_no_tests():
    ast_analyzer = ASTAnalyzer()
    discovery = TestDiscovery()

    data_app, _ = ast_analyzer.analyze_file("app/main.py", "x = 1\n")
    test_files, total_tests, diags = discovery.discover([data_app])
    assert test_files == []
    assert total_tests == 0
    assert len(diags) == 1
    assert diags[0].code == "TEST_NO_TESTS"
    assert diags[0].severity == DiagnosticSeverity.WARNING


# ==============================================================================
# 5. Ruff Analyzer (Mocked) Tests
# ==============================================================================

@pytest.mark.asyncio
async def test_ruff_analyzer_parses_json_output():
    mock_ruff_json = """[
        {
            "code": "F401",
            "message": "`os` imported but unused",
            "location": {"row": 2, "column": 8},
            "filename": "/workspace/app/main.py",
            "url": "https://docs.astral.sh/ruff/rules/unused-import"
        },
        {
            "code": "F821",
            "message": "Undefined name `undefined_variable`",
            "location": {"row": 5, "column": 12},
            "filename": "/workspace/app/main.py",
            "url": "https://docs.astral.sh/ruff/rules/undefined-name"
        }
    ]"""

    mock_exec = MockSandboxExecutor(mock_stdout=mock_ruff_json)
    analyzer = RuffAnalyzer(executor=mock_exec)

    artifact = make_valid_code_output()
    from app.sandbox.contracts import ExecutionRequest
    req = ExecutionRequest(project_id=uuid.uuid4())

    diags = await analyzer.analyze(req, artifact)
    assert len(diags) == 2

    # F401 -> Warning
    d0 = next(d for d in diags if d.code == "F401")
    assert d0.category == DiagnosticCategory.LINT
    assert d0.severity == DiagnosticSeverity.WARNING
    assert d0.file_path == "app/main.py"
    assert d0.line == 2

    # F821 -> Error (undefined name)
    d1 = next(d for d in diags if d.code == "F821")
    assert d1.category == DiagnosticCategory.LINT
    assert d1.severity == DiagnosticSeverity.ERROR
    assert d1.file_path == "app/main.py"
    assert d1.line == 5


# ==============================================================================
# 6. Deduplication and Aggregation Tests
# ==============================================================================

def test_deduplication():
    from app.sandbox.static_analysis.service import StaticAnalysisService
    service = StaticAnalysisService(session=None, workflow_service=None, executor=None)  # type: ignore

    d1 = StaticDiagnostic(
        category=DiagnosticCategory.LINT,
        severity=DiagnosticSeverity.WARNING,
        code="F401",
        message="unused import",
        file_path="app/main.py",
        line=1,
        column=8,
        source="ruff",
    )
    d2 = StaticDiagnostic(
        category=DiagnosticCategory.LINT,
        severity=DiagnosticSeverity.WARNING,
        code="F401",
        message="duplicate finding",
        file_path="app/main.py",
        line=1,
        column=8,
        source="ast",
    )
    d3 = StaticDiagnostic(
        category=DiagnosticCategory.LINT,
        severity=DiagnosticSeverity.WARNING,
        code="F401",
        message="different line",
        file_path="app/main.py",
        line=5,
        column=8,
        source="ruff",
    )

    deduped = service._deduplicate_diagnostics([d1, d2, d3])
    assert len(deduped) == 2


def test_build_result_aggregation():
    from app.sandbox.static_analysis.service import StaticAnalysisService
    service = StaticAnalysisService(session=None, workflow_service=None, executor=None)  # type: ignore

    diags = [
        StaticDiagnostic(
            category=DiagnosticCategory.SECURITY,
            severity=DiagnosticSeverity.CRITICAL,
            code="SEC_KEY",
            message="Secret found",
            source="secret_scanner",
        ),
        StaticDiagnostic(
            category=DiagnosticCategory.LINT,
            severity=DiagnosticSeverity.WARNING,
            code="F401",
            message="Unused import",
            source="ruff",
        ),
        StaticDiagnostic(
            category=DiagnosticCategory.TEST,
            severity=DiagnosticSeverity.INFO,
            code="TEST_DISCOVERED",
            message="Found tests",
            source="test_discovery",
        ),
    ]

    res = service._build_result(
        analysis_id=uuid.uuid4(),
        project_id=uuid.uuid4(),
        workflow_execution_id=None,
        status=StaticAnalysisStatus.VALIDATION_ERROR,
        duration_seconds=0.12,
        diagnostics=diags,
        files_analyzed=3,
        files_skipped=0,
        test_file_count=1,
        summary="Test summary",
    )

    assert res.error_count == 1
    assert res.warning_count == 1
    assert res.info_count == 1
    assert res.security_issue_count == 1
    assert res.lint_issue_count == 1
    assert res.status == StaticAnalysisStatus.VALIDATION_ERROR

