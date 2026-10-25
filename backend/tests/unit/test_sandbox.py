"""Unit Tests for Sandbox Architecture, Pre-Execution Validation, Resource Limits, and Service."""

import uuid
import pytest
from app.agents.code_generation.contracts import (
    CodeGenerationOutput,
    CodeGenerationPlan,
    GeneratedFile,
    PlannedFile,
)
from app.sandbox.contracts import (
    DEFAULT_MAX_OUTPUT_BYTES,
    DEFAULT_MEMORY_LIMIT,
    DEFAULT_TIMEOUT_SECONDS,
    ExecutionRequest,
    ExecutionResult,
    ExecutionStatus,
    ExecutionType,
    ResourceLimits,
)
from app.sandbox.docker_executor import DockerSandboxExecutor
from app.sandbox.mock_executor import MockSandboxExecutor
from app.sandbox.service import SandboxService
from app.sandbox.validation import validate_artifact_for_execution


def make_valid_code_output(
    files: list[tuple[str, str]] | None = None,
) -> CodeGenerationOutput:
    """Helper to produce a valid CodeGenerationOutput for testing."""
    if files is None:
        files = [
            ("app/main.py", "def add(a: int, b: int) -> int:\n    return a + b\n"),
            ("tests/test_main.py", "from app.main import add\n\ndef test_add():\n    assert add(1, 2) == 3\n"),
        ]

    plan_files = [
        PlannedFile(
            path=p,
            purpose=f"Purpose for {p}",
            file_type="SOURCE",
            requirement_ids=[],
            dependencies=[],
        )
        for p, _ in files
    ]

    plan = CodeGenerationPlan(
        project_type="backend-service",
        language="python",
        framework="fastapi",
        database="postgresql",
        package_manager="pip",
        files=plan_files,
        rationale="Valid test plan.",
    )

    gen_files = [
        GeneratedFile(
            path=p,
            content=c,
            language="python",
            size_bytes=len(c.encode("utf-8")),
            requirement_ids=[],
        )
        for p, c in files
    ]

    total_size = sum(f.size_bytes for f in gen_files)
    return CodeGenerationOutput(
        plan=plan,
        generated_files=gen_files,
        total_files=len(gen_files),
        total_size_bytes=total_size,
        summary="Test scaffold.",
    )


# ==============================================================================
# 1. Pre-Execution Validation Tests
# ==============================================================================

def test_pre_execution_validation_valid():
    artifact = make_valid_code_output()
    errors = validate_artifact_for_execution(artifact)
    assert errors == []


def test_pre_execution_validation_rejects_path_traversal():
    artifact = make_valid_code_output([("app/../../evil.py", "print(1)")])
    errors = validate_artifact_for_execution(artifact)
    assert any("path safety" in err.lower() for err in errors)


def test_pre_execution_validation_rejects_absolute_path():
    artifact = make_valid_code_output([("/etc/passwd", "root:x:0:0")])
    errors = validate_artifact_for_execution(artifact)
    assert any("path safety" in err.lower() or "absolute" in err.lower() for err in errors)


def test_pre_execution_validation_rejects_null_byte():
    artifact = make_valid_code_output([("app/main.py", "x = 1\0")])
    errors = validate_artifact_for_execution(artifact)
    assert any("null byte" in err.lower() for err in errors)


def test_pre_execution_validation_rejects_secrets():
    content = "API_KEY = 'gsk_123456789012345678901234567890123456'\n"
    artifact = make_valid_code_output([("app/config.py", content)])
    errors = validate_artifact_for_execution(artifact)
    assert any("secret detected" in err.lower() for err in errors)


def test_pre_execution_validation_rejects_private_keys():
    content = "-----BEGIN RSA PRIVATE KEY-----\nMIIEowIBAAKCAQEA0...\n-----END RSA PRIVATE KEY-----\n"
    artifact = make_valid_code_output([("app/key.pem", content)])
    errors = validate_artifact_for_execution(artifact)
    assert any("secret detected" in err.lower() for err in errors)


def test_pre_execution_validation_rejects_syntax_errors():
    artifact = make_valid_code_output([("app/main.py", "def broken_syntax(:\n    pass")])
    errors = validate_artifact_for_execution(artifact)
    assert any("syntax error" in err.lower() for err in errors)


def test_pre_execution_validation_rejects_dynamic_eval():
    artifact = make_valid_code_output([("app/main.py", "eval('1 + 1')\n")])
    errors = validate_artifact_for_execution(artifact)
    assert any("forbidden dynamic execution" in err.lower() for err in errors)


def test_pre_execution_validation_rejects_dynamic_exec():
    artifact = make_valid_code_output([("app/main.py", "exec('import os')\n")])
    errors = validate_artifact_for_execution(artifact)
    assert any("forbidden dynamic execution" in err.lower() for err in errors)


def test_pre_execution_validation_rejects_oversized_file():
    huge_content = "x = 1\n" * 20000  # > 50 KB
    # Test with dict representation which would fail Pydantic model validation
    raw_dict = {
        "plan": {
            "project_type": "backend-service",
            "language": "python",
            "framework": "fastapi",
            "database": "postgresql",
            "package_manager": "pip",
            "files": [{"path": "app/huge.py", "purpose": "Test huge file", "file_type": "SOURCE"}],
            "rationale": "Valid test plan.",
        },
        "generated_files": [
            {
                "path": "app/huge.py",
                "content": huge_content,
                "language": "python",
                "size_bytes": len(huge_content.encode("utf-8")),
                "requirement_ids": [],
            }
        ],
        "total_files": 1,
        "total_size_bytes": len(huge_content.encode("utf-8")),
        "summary": "Oversized artifact.",
    }
    errors = validate_artifact_for_execution(raw_dict)
    assert len(errors) > 0
    assert any("size_bytes" in err.lower() or "exceed" in err.lower() or "malformed" in err.lower() for err in errors)



def test_pre_execution_validation_validates_test_target_safety():
    artifact = make_valid_code_output()
    # Bad test target path
    errors = validate_artifact_for_execution(artifact, test_target="../../tests/evil.py")
    assert any("invalid test target" in err.lower() or "traversal" in err.lower() for err in errors)

    # Valid test target path
    valid_errors = validate_artifact_for_execution(artifact, test_target="tests/test_main.py")
    assert valid_errors == []


# ==============================================================================
# 2. Contract & Extra Field Rejection Tests
# ==============================================================================

def test_execution_request_rejects_extra_fields():
    with pytest.raises(Exception):
        ExecutionRequest(
            project_id=uuid.uuid4(),
            arbitrary_command="rm -rf /",  # type: ignore
        )


def test_execution_request_rejects_arbitrary_docker_flags():
    with pytest.raises(Exception):
        ExecutionRequest(
            project_id=uuid.uuid4(),
            privileged=True,  # type: ignore
        )


def test_resource_limits_bounds():
    # Valid limits
    limits = ResourceLimits(
        timeout_seconds=45,
        memory_limit="256m",
        cpus=1.5,
        max_pids=32,
        max_output_bytes=10000,
    )
    assert limits.timeout_seconds == 45

    # Negative timeout rejected
    with pytest.raises(Exception):
        ResourceLimits(timeout_seconds=-5)

    # Timeout > MAX rejected
    with pytest.raises(Exception):
        ResourceLimits(timeout_seconds=120)

    # Invalid memory format rejected
    with pytest.raises(Exception):
        ResourceLimits(memory_limit="unlimited")


# ==============================================================================
# 3. Output Truncation & Pytest Output Parsing Tests
# ==============================================================================

def test_docker_executor_output_parsing():
    executor = DockerSandboxExecutor()
    stdout_pass = "..\n2 passed in 0.12s\n"
    p, f, total = executor._parse_pytest_output(stdout_pass)
    assert p == 2
    assert f == 0
    assert total == 2

    stdout_fail = ".F\n1 failed, 1 passed in 0.15s\n"
    p, f, total = executor._parse_pytest_output(stdout_fail)
    assert p == 1
    assert f == 1
    assert total == 2

    stdout_error = "ERROR tests/test_main.py\n1 error in 0.05s\n"
    p, f, total = executor._parse_pytest_output(stdout_error)
    assert p == 0
    assert f == 1
    assert total == 1


def test_docker_executor_output_truncation():
    executor = DockerSandboxExecutor()
    short_text = "Standard test output."
    res, is_trunc = executor._truncate_output(short_text, max_bytes=100)
    assert res == short_text
    assert is_trunc is False

    long_text = "A" * 500
    res, is_trunc = executor._truncate_output(long_text, max_bytes=100)
    assert is_trunc is True
    assert "[TRUNCATED:" in res
    assert len(res) > 100  # Truncated marker is appended


# ==============================================================================
# 4. Mock Executor Execution Tests
# ==============================================================================

@pytest.mark.asyncio
async def test_mock_executor_passed():
    executor = MockSandboxExecutor(default_status=ExecutionStatus.PASSED)
    req = ExecutionRequest(project_id=uuid.uuid4(), execution_type=ExecutionType.TEST)
    artifact = make_valid_code_output()

    result = await executor.execute(req, artifact)
    assert result.status == ExecutionStatus.PASSED
    assert result.exit_code == 0
    assert result.tests_passed == 1
    assert result.tests_failed == 0


@pytest.mark.asyncio
async def test_mock_executor_failed():
    executor = MockSandboxExecutor(
        default_status=ExecutionStatus.FAILED,
        mock_tests_passed=1,
        mock_tests_failed=1,
        mock_exit_code=1,
        mock_stdout="1 failed, 1 passed",
    )
    req = ExecutionRequest(project_id=uuid.uuid4(), execution_type=ExecutionType.TEST)
    artifact = make_valid_code_output()

    result = await executor.execute(req, artifact)
    assert result.status == ExecutionStatus.FAILED
    assert result.exit_code == 1
    assert result.tests_passed == 1
    assert result.tests_failed == 1


@pytest.mark.asyncio
async def test_mock_executor_timeout():
    executor = MockSandboxExecutor(default_status=ExecutionStatus.TIMEOUT)
    req = ExecutionRequest(project_id=uuid.uuid4(), execution_type=ExecutionType.TEST)
    artifact = make_valid_code_output()

    result = await executor.execute(req, artifact)
    assert result.status == ExecutionStatus.TIMEOUT
    assert result.exit_code == -1


@pytest.mark.asyncio
async def test_mock_executor_resource_limit():
    executor = MockSandboxExecutor(default_status=ExecutionStatus.RESOURCE_LIMIT)
    req = ExecutionRequest(project_id=uuid.uuid4(), execution_type=ExecutionType.TEST)
    artifact = make_valid_code_output()

    result = await executor.execute(req, artifact)
    assert result.status == ExecutionStatus.RESOURCE_LIMIT
    assert result.exit_code == 137


@pytest.mark.asyncio
async def test_mock_executor_unavailable():
    executor = MockSandboxExecutor(is_available_flag=False)
    req = ExecutionRequest(project_id=uuid.uuid4(), execution_type=ExecutionType.TEST)
    artifact = make_valid_code_output()

    result = await executor.execute(req, artifact)
    assert result.status == ExecutionStatus.SANDBOX_UNAVAILABLE


@pytest.mark.asyncio
async def test_mock_executor_static_validate():
    executor = MockSandboxExecutor()
    req = ExecutionRequest(project_id=uuid.uuid4(), execution_type=ExecutionType.STATIC_VALIDATE)
    artifact = make_valid_code_output()

    result = await executor.execute(req, artifact)
    assert result.status == ExecutionStatus.PASSED
    assert result.exit_code == 0
    assert result.tests_passed == 1


@pytest.mark.asyncio
async def test_mock_executor_validation_error():
    executor = MockSandboxExecutor()
    req = ExecutionRequest(project_id=uuid.uuid4(), execution_type=ExecutionType.TEST)
    bad_artifact = make_valid_code_output([("app/bad.py", "eval('2')\n")])

    result = await executor.execute(req, bad_artifact)
    assert result.status == ExecutionStatus.VALIDATION_ERROR
    assert len(result.validation_errors) > 0


# ==============================================================================
# 5. Malicious Code Block Fixture Tests
# ==============================================================================

def test_malicious_fixture_path_traversal():
    """Verify that path traversal attempts are deterministically blocked."""
    artifact = make_valid_code_output([
        ("app/main.py", "x = 1"),
        ("../../../../../windows/system32/cmd.exe", "fake binary"),
    ])
    errors = validate_artifact_for_execution(artifact)
    assert len(errors) > 0
    assert any("path safety" in e.lower() for e in errors)


def test_malicious_fixture_embedded_secret():
    """Verify that hardcoded credentials/secrets are caught before entering sandbox."""
    artifact = make_valid_code_output([
        ("app/main.py", "SECRET = 'AIzaSyABC123456789012345678901234567890'\n"),
    ])
    errors = validate_artifact_for_execution(artifact)
    assert len(errors) > 0
    assert any("secret detected" in e.lower() for e in errors)


def test_malicious_fixture_dynamic_code_exec():
    """Verify that eval and exec calls are rejected."""
    artifact = make_valid_code_output([
        ("app/main.py", "import sys\nexec('sys.exit(1)')\n"),
    ])
    errors = validate_artifact_for_execution(artifact)
    assert len(errors) > 0
    assert any("forbidden dynamic execution" in e.lower() for e in errors)
