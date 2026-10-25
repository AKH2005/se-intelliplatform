"""Unit tests for Phase 11F: AI Test Generation, AST Safety Validation, Contracts, and Execution Parsing."""

import uuid
import pytest
from app.agents.contracts import ValidationResult
from app.agents.providers.mock import MockLLMProvider
from app.agents.test_generation.agent import TestGenerationAgent
from app.agents.test_generation.contracts import (
    AITestCaseResult,
    AITestExecutionRequest,
    AITestExecutionResult,
    AITestSuite,
    AITestSuiteCandidate,
    GeneratedTest,
    GeneratedTestCandidate,
    TestCategory,
    TestGenerationInput,
)
from app.agents.test_generation.service import AITestService
from app.agents.test_generation.validator import AITestValidator
from app.sandbox.contracts import ExecutionStatus
from app.schemas.context import ProjectContextResponse


def _sample_input(manifest: list[str] | None = None, req_ids: list[str] | None = None) -> TestGenerationInput:
    """Helper to build sample TestGenerationInput."""
    files = {
        "app/calculator.py": "def add(a, b):\n    return a + b\n\ndef divide(a, b):\n    if b == 0:\n        raise ValueError('Cannot divide by zero')\n    return a / b\n",
    }
    return TestGenerationInput(
        project_id=uuid.uuid4(),
        workflow_execution_id=uuid.uuid4(),
        manifest=manifest or ["app/calculator.py"],
        files=files,
        available_requirement_ids=req_ids or ["REQ-001", "REQ-002"],
        available_architecture_components=["CalculatorComponent"],
        available_database_entities=[],
        static_analysis_result=None,
        failure_diagnosis=None,
        allowed_categories=list(TestCategory),
    )


# ==============================================================================
# 1. Contract & Schema Tests
# ==============================================================================

def test_test_category_enums():
    """Verify all required test category classifications exist."""
    categories = {c.value for c in TestCategory}
    expected = {"HAPPY_PATH", "EDGE_CASE", "VALIDATION", "ERROR_HANDLING", "BUSINESS_LOGIC", "API_BEHAVIOR"}
    assert expected.issubset(categories)


def test_generated_test_validation():
    """Test GeneratedTest model validation rules."""
    test = GeneratedTest(
        test_id="TEST-001",
        name="test_add_positive",
        description="Verifies adding two positive integers",
        category=TestCategory.HAPPY_PATH,
        target_file="app/calculator.py",
        target_symbol="add",
        requirement_ids=["REQ-001"],
        architecture_component="CalculatorComponent",
        rationale="Tests standard addition",
        code="def test_add_positive():\n    from app.calculator import add\n    assert add(2, 3) == 5\n",
        expected_behavior="Returns 5",
    )
    assert test.name == "test_add_positive"
    assert test.category == TestCategory.HAPPY_PATH


def test_generated_test_invalid_name():
    """Reject function names that do not start with test_."""
    with pytest.raises(Exception):
        GeneratedTest(
            test_id="TEST-001",
            name="invalid_function_name",
            description="Missing test_ prefix",
            category=TestCategory.HAPPY_PATH,
            target_file="app/calculator.py",
            rationale="Invalid",
            code="def invalid(): pass",
            expected_behavior="Fail",
        )


# ==============================================================================
# 2. Deterministic AST & Safety Validator Tests
# ==============================================================================

def test_validator_valid_suite():
    """Validator accepts clean, structured pytest tests."""
    inp = _sample_input()
    candidate = AITestSuiteCandidate(
        summary="Unit test suite for calculator",
        tests=[
            GeneratedTestCandidate(
                test_id="TEST-001",
                name="test_add_valid",
                description="Tests standard addition",
                category="HAPPY_PATH",
                target_file="app/calculator.py",
                target_symbol="add",
                requirement_ids=["REQ-001"],
                architecture_component="CalculatorComponent",
                rationale="Verifies happy path",
                code="def test_add_valid():\n    from app.calculator import add\n    assert add(2, 3) == 5\n",
                expected_behavior="Result is 5",
            ),
            GeneratedTestCandidate(
                test_id="TEST-002",
                name="test_divide_zero_raises",
                description="Tests division by zero raises ValueError",
                category="ERROR_HANDLING",
                target_file="app/calculator.py",
                target_symbol="divide",
                requirement_ids=["REQ-002"],
                architecture_component="CalculatorComponent",
                rationale="Verifies error handling",
                code="def test_divide_zero_raises():\n    import pytest\n    from app.calculator import divide\n    with pytest.raises(ValueError):\n        divide(10, 0)\n",
                expected_behavior="Raises ValueError",
            ),
        ],
    )
    val_res = AITestValidator.validate(candidate, inp)
    assert val_res.is_valid is True
    assert len(val_res.errors) == 0


def test_validator_rejects_empty_suite():
    """Validator rejects suites with no tests."""
    inp = _sample_input()
    candidate = AITestSuiteCandidate(summary="Empty suite", tests=[])
    val_res = AITestValidator.validate(candidate, inp)
    assert val_res.is_valid is False
    assert "contains no test cases" in val_res.errors[0]


def test_validator_rejects_oversized_suite():
    """Validator rejects suites exceeding MAX_TESTS."""
    inp = _sample_input()
    many_tests = [
        GeneratedTestCandidate(
            test_id=f"TEST-{i}",
            name=f"test_num_{i}",
            target_file="app/calculator.py",
            code=f"def test_num_{i}():\n    assert {i} == {i}\n",
        )
        for i in range(12)
    ]
    candidate = AITestSuiteCandidate(summary="Too many tests", tests=many_tests)
    val_res = AITestValidator.validate(candidate, inp)
    assert val_res.is_valid is False
    assert any("exceeds maximum allowed tests" in e for e in val_res.errors)


def test_validator_rejects_duplicate_ids_and_names():
    """Validator detects and rejects duplicate test IDs and duplicate test names."""
    inp = _sample_input()
    candidate = AITestSuiteCandidate(
        tests=[
            GeneratedTestCandidate(
                test_id="TEST-001",
                name="test_duplicate_name",
                target_file="app/calculator.py",
                code="def test_duplicate_name():\n    assert 1 == 1\n",
            ),
            GeneratedTestCandidate(
                test_id="TEST-001",
                name="test_duplicate_name",
                target_file="app/calculator.py",
                code="def test_duplicate_name():\n    assert 2 == 2\n",
            ),
        ]
    )
    val_res = AITestValidator.validate(candidate, inp)
    assert val_res.is_valid is False
    assert any("Duplicate test_id" in e for e in val_res.errors)
    assert any("Duplicate test name" in e for e in val_res.errors)


def test_validator_rejects_hallucinated_file():
    """Validator rejects tests targeting files not present in the project manifest."""
    inp = _sample_input(manifest=["app/calculator.py"])
    candidate = AITestSuiteCandidate(
        tests=[
            GeneratedTestCandidate(
                test_id="TEST-001",
                name="test_unknown_module",
                target_file="app/nonexistent_service.py",
                code="def test_unknown_module():\n    assert 1 == 1\n",
            )
        ]
    )
    val_res = AITestValidator.validate(candidate, inp)
    assert val_res.is_valid is False
    assert any("not found in project manifest" in e for e in val_res.errors)


def test_validator_rejects_hallucinated_requirement_id():
    """Validator rejects tests referencing requirement IDs outside available requirements."""
    inp = _sample_input(req_ids=["REQ-001"])
    candidate = AITestSuiteCandidate(
        tests=[
            GeneratedTestCandidate(
                test_id="TEST-001",
                name="test_hallucinated_req",
                target_file="app/calculator.py",
                requirement_ids=["REQ-999-FAKE"],
                code="def test_hallucinated_req():\n    assert 1 == 1\n",
            )
        ]
    )
    val_res = AITestValidator.validate(candidate, inp)
    assert val_res.is_valid is False
    assert any("Hallucinated requirement_id 'REQ-999-FAKE'" in e for e in val_res.errors)


def test_validator_rejects_path_traversal():
    """Validator blocks directory traversal and absolute paths."""
    inp = _sample_input()
    for bad_path in ["../app/calculator.py", "/app/calculator.py", "C:\\app\\calculator.py", "app/../calculator.py"]:
        candidate = AITestSuiteCandidate(
            tests=[
                GeneratedTestCandidate(
                    test_id="TEST-001",
                    name="test_traversal",
                    target_file=bad_path,
                    code="def test_traversal():\n    assert 1 == 1\n",
                )
            ]
        )
        val_res = AITestValidator.validate(candidate, inp)
        assert val_res.is_valid is False


def test_validator_rejects_forbidden_imports():
    """Validator uses AST to detect forbidden imports (os, subprocess, socket, requests, urllib, etc.)."""
    inp = _sample_input()
    dangerous_snippets = [
        "def test_os_import():\n    import os\n    assert os.name == 'posix'\n",
        "def test_subprocess_import():\n    import subprocess\n    assert subprocess.run(['ls']).returncode == 0\n",
        "def test_socket_import():\n    from socket import socket\n    assert socket is not None\n",
        "def test_requests_import():\n    import requests\n    assert requests.get('http://evil.com')\n",
        "def test_shutil_import():\n    from shutil import rmtree\n    rmtree('/tmp')\n",
    ]

    for snippet in dangerous_snippets:
        candidate = AITestSuiteCandidate(
            tests=[
                GeneratedTestCandidate(
                    test_id="TEST-001",
                    name="test_danger",
                    target_file="app/calculator.py",
                    code=snippet,
                )
            ]
        )
        val_res = AITestValidator.validate(candidate, inp)
        assert val_res.is_valid is False
        assert any("Forbidden import" in e for e in val_res.errors)


def test_validator_rejects_forbidden_calls():
    """Validator rejects eval(), exec(), open(), and dangerous builtins."""
    inp = _sample_input()
    forbidden_calls = [
        "def test_eval():\n    eval('2 + 2')\n    assert True\n",
        "def test_exec():\n    exec('x = 1')\n    assert True\n",
        "def test_open():\n    with open('/etc/passwd') as f: pass\n    assert True\n",
        "def test_globals():\n    g = globals()\n    assert g\n",
    ]

    for snippet in forbidden_calls:
        candidate = AITestSuiteCandidate(
            tests=[
                GeneratedTestCandidate(
                    test_id="TEST-001",
                    name="test_forbidden_call",
                    target_file="app/calculator.py",
                    code=snippet,
                )
            ]
        )
        val_res = AITestValidator.validate(candidate, inp)
        assert val_res.is_valid is False
        assert any("Forbidden function call" in e for e in val_res.errors)


def test_validator_rejects_missing_assertions():
    """Validator rejects test code that contains no assertions."""
    inp = _sample_input()
    candidate = AITestSuiteCandidate(
        tests=[
            GeneratedTestCandidate(
                test_id="TEST-001",
                name="test_no_assertions",
                target_file="app/calculator.py",
                code="def test_no_assertions():\n    x = 1 + 1\n",
            )
        ]
    )
    val_res = AITestValidator.validate(candidate, inp)
    assert val_res.is_valid is False
    assert any("must contain at least one meaningful assertion" in e for e in val_res.errors)


def test_validator_rejects_trivial_assertions():
    """Validator rejects trivial 'assert True'."""
    inp = _sample_input()
    candidate = AITestSuiteCandidate(
        tests=[
            GeneratedTestCandidate(
                test_id="TEST-001",
                name="test_trivial",
                target_file="app/calculator.py",
                code="def test_trivial():\n    assert True\n",
            )
        ]
    )
    val_res = AITestValidator.validate(candidate, inp)
    assert val_res.is_valid is False
    assert any("Trivial assertion 'assert True'" in e for e in val_res.errors)


def test_validator_rejects_secrets():
    """Validator scans test code for credentials, private keys, and API tokens."""
    inp = _sample_input()
    candidate = AITestSuiteCandidate(
        tests=[
            GeneratedTestCandidate(
                test_id="TEST-001",
                name="test_with_secret",
                target_file="app/calculator.py",
                code="def test_with_secret():\n    api_key = 'AKIA1234567890ABCDEF'\n    assert api_key\n",
            )
        ]
    )
    val_res = AITestValidator.validate(candidate, inp)
    assert val_res.is_valid is False
    assert any("Detected potential secret" in e for e in val_res.errors)


def test_validator_compiles_suite_correctly():
    """AITestValidator.compile_candidate_to_suite correctly generates a runnable pytest module."""
    inp = _sample_input()
    candidate = AITestSuiteCandidate(
        summary="Calculations test suite",
        tests=[
            GeneratedTestCandidate(
                test_id="TEST-001",
                name="test_add",
                description="Tests add function",
                category="HAPPY_PATH",
                target_file="app/calculator.py",
                requirement_ids=["REQ-001"],
                code="def test_add():\n    from app.calculator import add\n    assert add(1, 2) == 3\n",
            )
        ],
    )
    suite = AITestValidator.compile_candidate_to_suite(candidate, inp)
    assert isinstance(suite, AITestSuite)
    assert suite.test_count == 1
    assert "tests/test_ai_generated.py" in suite.test_files
    test_content = suite.test_files["tests/test_ai_generated.py"]
    assert "import pytest" in test_content
    assert "def test_add():" in test_content
    assert suite.requirement_traceability == {"REQ-001": ["TEST-001"]}


# ==============================================================================
# 3. Agent Integration Tests
# ==============================================================================

@pytest.mark.asyncio
async def test_test_generation_agent_lifecycle():
    """Verify TestGenerationAgent metadata, initialization, and structured generation."""
    agent = TestGenerationAgent()
    assert agent.metadata.agent_id == "test-generation"
    assert agent.metadata.version == "1.0.0"

    await agent.initialize()

    provider = MockLLMProvider()
    canned_candidate = AITestSuiteCandidate(
        summary="Canned mock test suite",
        tests=[
            GeneratedTestCandidate(
                test_id="TEST-001",
                name="test_calc_add",
                description="Tests addition",
                category="HAPPY_PATH",
                target_file="app/calculator.py",
                requirement_ids=["REQ-001"],
                code="def test_calc_add():\n    assert 2 + 2 == 4\n",
            )
        ],
    )
    provider.register_structured_response(canned_candidate)

    inp = _sample_input()
    analysis_res = {"test_input": inp}
    candidate = await agent.generate(analysis_res, provider)

    assert candidate.summary == "Canned mock test suite"
    assert len(candidate.tests) == 1
    assert candidate.tests[0].name == "test_calc_add"


# ==============================================================================
# 4. Service Detailed Result Parsing Tests
# ==============================================================================

def test_parse_detailed_test_results():
    """Test pytest stdout parser maps verbose test lines into individual structured test results."""
    service = AITestService.__new__(AITestService)

    sample_stdout = """
============================= test session starts ==============================
rootdir: /workspace
collected 2 items

tests/test_ai_generated.py::test_calc_add PASSED                         [ 50%]
tests/test_ai_generated.py::test_calc_div FAILED                         [100%]

=================================== FAILURES ===================================
________________________________ test_calc_div _________________________________
    def test_calc_div():
>       assert divide(1, 0) == 0
E       ValueError: Cannot divide by zero
=========================== short test summary info ============================
FAILED tests/test_ai_generated.py::test_calc_div - ValueError: Cannot divide by zero
========================= 1 failed, 1 passed in 0.05s ==========================
"""

    mock_tests = [
        GeneratedTest(
            test_id="TEST-001",
            name="test_calc_add",
            description="add test",
            category=TestCategory.HAPPY_PATH,
            target_file="app/calculator.py",
            rationale="rationale",
            code="def test_calc_add(): pass",
            expected_behavior="passes",
        ),
        GeneratedTest(
            test_id="TEST-002",
            name="test_calc_div",
            description="div test",
            category=TestCategory.ERROR_HANDLING,
            target_file="app/calculator.py",
            rationale="rationale",
            code="def test_calc_div(): pass",
            expected_behavior="passes",
        ),
    ]

    results, failures = service._parse_detailed_test_results(sample_stdout, "", mock_tests)

    assert len(results) == 2
    assert results[0].name == "test_calc_add"
    assert results[0].status == "PASSED"
    assert results[1].name == "test_calc_div"
    assert results[1].status == "FAILED"
    assert len(failures) >= 1
    assert "ValueError: Cannot divide by zero" in failures[0]
