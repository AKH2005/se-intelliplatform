"""Integration Tests for Docker Sandbox Ruff Execution and Static Analysis."""

import uuid
import pytest

from app.sandbox.contracts import ExecutionRequest
from app.sandbox.docker_executor import DockerSandboxExecutor
from app.sandbox.static_analysis.contracts import (
    DiagnosticCategory,
    DiagnosticSeverity,
)
from app.sandbox.static_analysis.ruff_analyzer import RuffAnalyzer
from tests.integration.test_sandbox_docker import docker_available
from tests.unit.test_sandbox import make_valid_code_output


@pytest.fixture
def docker_executor():
    return DockerSandboxExecutor()


@pytest.mark.asyncio
@docker_available
async def test_docker_ruff_unused_import_fixture(docker_executor):
    """Verify that containerized Ruff detects unused import (F401)."""
    artifact = make_valid_code_output([
        ("app/main.py", "import os\n\ndef add(a: int, b: int) -> int:\n    return a + b\n"),
        ("tests/test_main.py", "def test_add(): assert 1 == 1\n"),
    ])
    analyzer = RuffAnalyzer(executor=docker_executor)
    req = ExecutionRequest(project_id=uuid.uuid4())

    diagnostics = await analyzer.analyze(req, artifact)
    f401_diags = [d for d in diagnostics if d.code == "F401"]
    assert len(f401_diags) == 1
    d = f401_diags[0]
    assert d.category == DiagnosticCategory.LINT
    assert d.severity == DiagnosticSeverity.WARNING
    assert d.file_path == "app/main.py"
    assert d.line == 1
    assert "os" in d.message


@pytest.mark.asyncio
@docker_available
async def test_docker_ruff_undefined_name_fixture(docker_executor):
    """Verify that containerized Ruff detects undefined names (F821) as ERROR severity."""
    artifact = make_valid_code_output([
        ("app/main.py", "def compute():\n    return undefined_variable * 2\n"),
        ("tests/test_main.py", "def test_ok(): assert 1 == 1\n"),
    ])
    analyzer = RuffAnalyzer(executor=docker_executor)
    req = ExecutionRequest(project_id=uuid.uuid4())

    diagnostics = await analyzer.analyze(req, artifact)
    f821_diags = [d for d in diagnostics if d.code == "F821"]
    assert len(f821_diags) == 1
    d = f821_diags[0]
    assert d.category == DiagnosticCategory.LINT
    assert d.severity == DiagnosticSeverity.ERROR
    assert d.file_path == "app/main.py"
    assert "undefined_variable" in d.message


@pytest.mark.asyncio
@docker_available
async def test_docker_ruff_clean_fixture(docker_executor):
    """Verify that clean Python code produces 0 Ruff diagnostics."""
    artifact = make_valid_code_output([
        ("app/main.py", "def multiply(x: int, y: int) -> int:\n    return x * y\n"),
        ("tests/test_main.py", "from app.main import multiply\n\ndef test_mult():\n    assert multiply(2, 3) == 6\n"),
    ])
    analyzer = RuffAnalyzer(executor=docker_executor)
    req = ExecutionRequest(project_id=uuid.uuid4())

    diagnostics = await analyzer.analyze(req, artifact)
    assert len(diagnostics) == 0
