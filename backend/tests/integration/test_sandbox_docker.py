"""Integration Tests for Docker Sandbox Runtime.

Verifies:
- PASS fixture execution
- FAIL fixture execution
- TIMEOUT enforcement
- Network isolation (--network=none)
- Filesystem read-only isolation (/workspace is ro)
- Environment variable isolation (host secrets absent)
- Container cleanup
"""

import shutil
import subprocess
import uuid
import pytest

from app.sandbox.contracts import (
    ExecutionRequest,
    ExecutionStatus,
    ExecutionType,
    ResourceLimits,
)
from app.sandbox.docker_executor import DockerSandboxExecutor
from tests.unit.test_sandbox import make_valid_code_output


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
    reason="Docker runtime is not available in environment",
)


@pytest.fixture
def docker_executor():
    return DockerSandboxExecutor()


@pytest.mark.asyncio
@docker_available
async def test_docker_sandbox_pass_fixture(docker_executor):
    """Verify clean execution of passing pytest test suite."""
    code_output = make_valid_code_output([
        ("app/math.py", "def multiply(x: int, y: int) -> int:\n    return x * y\n"),
        ("tests/test_math.py", "from app.math import multiply\n\ndef test_multiply():\n    assert multiply(3, 4) == 12\n"),
    ])
    req = ExecutionRequest(
        project_id=uuid.uuid4(),
        execution_type=ExecutionType.TEST,
        limits=ResourceLimits(timeout_seconds=20),
    )

    result = await docker_executor.execute(req, code_output)
    assert result.status == ExecutionStatus.PASSED
    assert result.exit_code == 0
    assert result.tests_passed == 1
    assert result.tests_failed == 0
    assert "1 passed" in result.stdout


@pytest.mark.asyncio
@docker_available
async def test_docker_sandbox_fail_fixture(docker_executor):
    """Verify clean handling of failing pytest test suite."""
    code_output = make_valid_code_output([
        ("app/math.py", "def multiply(x: int, y: int) -> int:\n    return x * y\n"),
        ("tests/test_math.py", "from app.math import multiply\n\ndef test_fail():\n    assert multiply(2, 2) == 5\n"),
    ])
    req = ExecutionRequest(
        project_id=uuid.uuid4(),
        execution_type=ExecutionType.TEST,
        limits=ResourceLimits(timeout_seconds=20),
    )

    result = await docker_executor.execute(req, code_output)
    assert result.status == ExecutionStatus.FAILED
    assert result.exit_code == 1
    assert result.tests_failed == 1
    assert "1 failed" in result.stdout


@pytest.mark.asyncio
@docker_available
async def test_docker_sandbox_timeout_fixture(docker_executor):
    """Verify that infinite loops or hanging tests are terminated within configured timeout."""
    code_output = make_valid_code_output([
        ("app/slow.py", "import time\ndef stall():\n    while True:\n        time.sleep(0.1)\n"),
        ("tests/test_slow.py", "from app.slow import stall\ndef test_stall():\n    stall()\n"),
    ])
    req = ExecutionRequest(
        project_id=uuid.uuid4(),
        execution_type=ExecutionType.TEST,
        limits=ResourceLimits(timeout_seconds=3),  # 3s limit
    )

    result = await docker_executor.execute(req, code_output)
    assert result.status == ExecutionStatus.TIMEOUT
    assert result.exit_code == -1
    assert "timeout" in result.stderr.lower()


@pytest.mark.asyncio
@docker_available
async def test_docker_sandbox_network_isolation(docker_executor):
    """Verify that network access inside container is completely disabled (--network=none)."""
    code_output = make_valid_code_output([
        ("app/net.py", "import urllib.request\ndef ping():\n    urllib.request.urlopen('http://1.1.1.1', timeout=1)\n"),
        ("tests/test_net.py", "from app.net import ping\nimport urllib.error, pytest\ndef test_net_blocked():\n    with pytest.raises(Exception):\n        ping()\n"),
    ])
    req = ExecutionRequest(
        project_id=uuid.uuid4(),
        execution_type=ExecutionType.TEST,
        limits=ResourceLimits(timeout_seconds=15),
    )

    result = await docker_executor.execute(req, code_output)
    assert result.status == ExecutionStatus.PASSED
    assert result.tests_passed == 1


@pytest.mark.asyncio
@docker_available
async def test_docker_sandbox_readonly_filesystem(docker_executor):
    """Verify that the generated workspace is mounted read-only and cannot be modified."""
    code_output = make_valid_code_output([
        ("app/ro.py", "def tamper():\n    with open('/workspace/tampered.txt', 'w') as f:\n        f.write('bad')\n"),
        ("tests/test_ro.py", "from app.ro import tamper\nimport pytest\ndef test_write_blocked():\n    with pytest.raises(OSError):\n        tamper()\n"),
    ])
    req = ExecutionRequest(
        project_id=uuid.uuid4(),
        execution_type=ExecutionType.TEST,
        limits=ResourceLimits(timeout_seconds=15),
    )

    result = await docker_executor.execute(req, code_output)
    assert result.status == ExecutionStatus.PASSED
    assert result.tests_passed == 1


@pytest.mark.asyncio
@docker_available
async def test_docker_sandbox_environment_isolation(docker_executor):
    """Verify that host environment variables and secrets are absent from the container."""
    code_output = make_valid_code_output([
        (
            "tests/test_env.py",
            "import os\ndef test_no_host_secrets():\n"
            "    forbidden = ['GROQ_API_KEY', 'GEMINI_API_KEY', 'DATABASE_URL', 'SECRET_KEY']\n"
            "    for key in forbidden:\n"
            "        assert key not in os.environ, f'{key} leaked into container'\n",
        ),
    ])
    req = ExecutionRequest(
        project_id=uuid.uuid4(),
        execution_type=ExecutionType.TEST,
        limits=ResourceLimits(timeout_seconds=15),
    )

    result = await docker_executor.execute(req, code_output)
    assert result.status == ExecutionStatus.PASSED
    assert result.tests_passed == 1
