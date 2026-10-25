"""Integration Tests for Docker Sandbox Execution of AI-Generated Tests (Phase 11F).

Verifies:
1. Valid generated test passes inside Docker container.
2. Valid generated test fails inside Docker container.
3. Dangerous test (forbidden call or import) is rejected before execution by validator.
4. Network-access test is rejected by validator or blocked by sandbox.
5. Timeout is handled safely without hanging.
6. Original artifact remains completely unchanged.
7. Generated tests cannot escape controlled paths.
"""

import shutil
import subprocess
import uuid
import pytest

from app.agents.code_generation.contracts import (
    CodeGenerationOutput,
    CodeGenerationPlan,
    GeneratedFile,
    PlannedFile,
)
from app.agents.test_generation.contracts import (
    AITestSuite,
    AITestSuiteCandidate,
    GeneratedTest,
    GeneratedTestCandidate,
    TestCategory,
    TestGenerationInput,
)
from app.agents.test_generation.validator import AITestValidator
from app.sandbox.contracts import (
    ExecutionRequest,
    ExecutionStatus,
    ExecutionType,
    ResourceLimits,
)
from app.sandbox.docker_executor import DockerSandboxExecutor


def is_docker_ready() -> bool:
    """Check if Docker is installed and running."""
    if not shutil.which("docker"):
        return False
    try:
        res = subprocess.run(
            ["docker", "info"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=5,
        )
        return res.returncode == 0
    except Exception:
        return False


docker_available = pytest.mark.skipif(
    not is_docker_ready(),
    reason="Docker daemon is not available in environment",
)


def _make_code_artifact() -> CodeGenerationOutput:
    """Helper to create a deterministic application artifact."""
    return CodeGenerationOutput(
        plan=CodeGenerationPlan(
            project_type="backend-service",
            language="python",
            framework="fastapi",
            database="sqlite",
            package_manager="pip",
            files=[
                PlannedFile(
                    path="app/calculator.py",
                    purpose="Arithmetic logic",
                    file_type="SOURCE",
                    requirement_ids=[],
                    dependencies=[],
                )
            ],
            rationale="Math calculation service",
        ),
        generated_files=[
            GeneratedFile(
                path="app/calculator.py",
                content=(
                    "def add(a, b):\n"
                    "    return a + b\n\n"
                    "def multiply(a, b):\n"
                    "    return a * b\n"
                ),
                language="python",
                size_bytes=60,
                requirement_ids=[],
            )
        ],
        total_files=1,
        total_size_bytes=60,
        summary="Verified calculator module",
    )


def _build_ephemeral_artifact(original: CodeGenerationOutput, suite: AITestSuite) -> CodeGenerationOutput:
    """Combine original files and generated tests into an ephemeral execution artifact."""
    combined = list(original.generated_files)
    for path, content in suite.test_files.items():
        combined.append(
            GeneratedFile(
                path=path,
                content=content,
                language="python",
                size_bytes=len(content.encode("utf-8")),
                requirement_ids=[],
            )
        )
    return CodeGenerationOutput(
        plan=original.plan,
        generated_files=combined,
        total_files=len(combined),
        total_size_bytes=sum(f.size_bytes for f in combined),
        summary="Ephemeral testing artifact",
    )


@pytest.fixture
def docker_executor():
    return DockerSandboxExecutor()


# ==============================================================================
# Docker Integration Tests
# ==============================================================================

@pytest.mark.asyncio
@docker_available
async def test_docker_ai_generated_test_passes(docker_executor):
    """1. Valid generated test passes inside Docker container."""
    original = _make_code_artifact()
    inp = TestGenerationInput(
        project_id=uuid.uuid4(),
        manifest=["app/calculator.py"],
        files={"app/calculator.py": original.generated_files[0].content},
        available_requirement_ids=[],
    )

    candidate = AITestSuiteCandidate(
        summary="Calculator unit test suite",
        tests=[
            GeneratedTestCandidate(
                test_id="TEST-001",
                name="test_calculator_add_success",
                description="Tests add function",
                category="HAPPY_PATH",
                target_file="app/calculator.py",
                code="def test_calculator_add_success():\n    from app.calculator import add\n    assert add(3, 4) == 7\n",
            )
        ],
    )

    val_res = AITestValidator.validate(candidate, inp)
    assert val_res.is_valid is True

    suite = AITestValidator.compile_candidate_to_suite(candidate, inp)
    ephemeral = _build_ephemeral_artifact(original, suite)

    req = ExecutionRequest(
        project_id=inp.project_id,
        execution_type=ExecutionType.TEST,
        test_target="tests/test_ai_generated.py",
        limits=ResourceLimits(timeout_seconds=20),
    )

    result = await docker_executor.execute(req, ephemeral)
    assert result.status == ExecutionStatus.PASSED
    assert result.exit_code == 0
    assert result.tests_passed == 1
    assert result.tests_failed == 0
    assert "1 passed" in result.stdout


@pytest.mark.asyncio
@docker_available
async def test_docker_ai_generated_test_fails(docker_executor):
    """2. Valid generated test fails inside Docker container when assertion fails."""
    original = _make_code_artifact()
    inp = TestGenerationInput(
        project_id=uuid.uuid4(),
        manifest=["app/calculator.py"],
        files={"app/calculator.py": original.generated_files[0].content},
        available_requirement_ids=[],
    )

    candidate = AITestSuiteCandidate(
        summary="Failing assertion test",
        tests=[
            GeneratedTestCandidate(
                test_id="TEST-002",
                name="test_calculator_failing_assertion",
                description="Intentionally failing assertion",
                category="HAPPY_PATH",
                target_file="app/calculator.py",
                code="def test_calculator_failing_assertion():\n    from app.calculator import add\n    assert add(3, 4) == 999\n",
            )
        ],
    )

    val_res = AITestValidator.validate(candidate, inp)
    assert val_res.is_valid is True

    suite = AITestValidator.compile_candidate_to_suite(candidate, inp)
    ephemeral = _build_ephemeral_artifact(original, suite)

    req = ExecutionRequest(
        project_id=inp.project_id,
        execution_type=ExecutionType.TEST,
        test_target="tests/test_ai_generated.py",
        limits=ResourceLimits(timeout_seconds=20),
    )

    result = await docker_executor.execute(req, ephemeral)
    assert result.status == ExecutionStatus.FAILED
    assert result.exit_code != 0
    assert result.tests_failed == 1
    assert "1 failed" in result.stdout


def test_dangerous_test_rejected_before_docker_execution():
    """3. Dangerous test (forbidden call or import) is rejected before Docker execution."""
    inp = TestGenerationInput(
        project_id=uuid.uuid4(),
        manifest=["app/calculator.py"],
        files={"app/calculator.py": "def add(a, b): return a + b\n"},
        available_requirement_ids=[],
    )

    dangerous_candidate = AITestSuiteCandidate(
        summary="Malicious test suite",
        tests=[
            GeneratedTestCandidate(
                test_id="MAL-001",
                name="test_subprocess_escape",
                category="HAPPY_PATH",
                target_file="app/calculator.py",
                code="def test_subprocess_escape():\n    import subprocess\n    subprocess.run(['rm', '-rf', '/'])\n    assert True\n",
            )
        ],
    )

    val_res = AITestValidator.validate(dangerous_candidate, inp)
    assert val_res.is_valid is False
    assert any("Forbidden import 'subprocess'" in e for e in val_res.errors)


def test_network_access_test_rejected_before_execution():
    """4. Network-access test is rejected by deterministic AST validator."""
    inp = TestGenerationInput(
        project_id=uuid.uuid4(),
        manifest=["app/calculator.py"],
        files={"app/calculator.py": "def add(a, b): return a + b\n"},
        available_requirement_ids=[],
    )

    network_candidate = AITestSuiteCandidate(
        summary="Network test suite",
        tests=[
            GeneratedTestCandidate(
                test_id="NET-001",
                name="test_outbound_http",
                category="API_BEHAVIOR",
                target_file="app/calculator.py",
                code="def test_outbound_http():\n    import requests\n    r = requests.get('https://google.com')\n    assert r.status_code == 200\n",
            )
        ],
    )

    val_res = AITestValidator.validate(network_candidate, inp)
    assert val_res.is_valid is False
    assert any("Forbidden import 'requests'" in e for e in val_res.errors)


@pytest.mark.asyncio
@docker_available
async def test_docker_timeout_handled(docker_executor):
    """5. Timeout is handled safely without hanging the process."""
    original = _make_code_artifact()
    inp = TestGenerationInput(
        project_id=uuid.uuid4(),
        manifest=["app/calculator.py"],
        files={"app/calculator.py": original.generated_files[0].content},
        available_requirement_ids=[],
    )

    candidate = AITestSuiteCandidate(
        summary="Infinite loop test",
        tests=[
            GeneratedTestCandidate(
                test_id="TEST-LOOP",
                name="test_infinite_loop",
                category="EDGE_CASE",
                target_file="app/calculator.py",
                code="def test_infinite_loop():\n    import time\n    time.sleep(10)\n    assert sum([1, 2]) == 3\n",
            )
        ],
    )

    val_res = AITestValidator.validate(candidate, inp)
    assert val_res.is_valid is True

    suite = AITestValidator.compile_candidate_to_suite(candidate, inp)
    ephemeral = _build_ephemeral_artifact(original, suite)

    req = ExecutionRequest(
        project_id=inp.project_id,
        execution_type=ExecutionType.TEST,
        test_target="tests/test_ai_generated.py",
        limits=ResourceLimits(timeout_seconds=2),  # Short 2 second timeout
    )

    result = await docker_executor.execute(req, ephemeral)
    assert result.status == ExecutionStatus.TIMEOUT
    assert "timed out" in result.stderr.lower() or result.duration_seconds >= 2.0


def test_original_artifact_immutability():
    """6. Original application artifact remains completely unchanged during ephemeral testing."""
    original = _make_code_artifact()
    original_files_before = [f.model_dump() for f in original.generated_files]

    inp = TestGenerationInput(
        project_id=uuid.uuid4(),
        manifest=["app/calculator.py"],
        files={"app/calculator.py": original.generated_files[0].content},
        available_requirement_ids=[],
    )

    candidate = AITestSuiteCandidate(
        tests=[
            GeneratedTestCandidate(
                test_id="TEST-001",
                name="test_immutability",
                category="HAPPY_PATH",
                target_file="app/calculator.py",
                code="def test_immutability():\n    assert 1 == 1\n",
            )
        ]
    )

    suite = AITestValidator.compile_candidate_to_suite(candidate, inp)
    ephemeral = _build_ephemeral_artifact(original, suite)

    # Ephemeral has the test file
    assert len(ephemeral.generated_files) == len(original.generated_files) + 1
    # Original remains untouched
    assert [f.model_dump() for f in original.generated_files] == original_files_before


def test_generated_test_path_traversal_blocked():
    """7. Generated tests cannot escape controlled paths."""
    inp = TestGenerationInput(
        project_id=uuid.uuid4(),
        manifest=["app/calculator.py"],
        files={"app/calculator.py": "def add(a, b): return a + b\n"},
        available_requirement_ids=[],
    )

    candidate = AITestSuiteCandidate(
        tests=[
            GeneratedTestCandidate(
                test_id="TEST-TRAV",
                name="test_path_traversal",
                category="HAPPY_PATH",
                target_file="../../etc/shadow",
                code="def test_path_traversal():\n    assert 1 == 1\n",
            )
        ]
    )

    val_res = AITestValidator.validate(candidate, inp)
    assert val_res.is_valid is False
    assert any("Directory traversal" in e or "not found in project manifest" in e for e in val_res.errors)
