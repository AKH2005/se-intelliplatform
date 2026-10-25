"""Integration Tests for Docker Runtime Subsystem (Phase 11J - Stage 2).

Executes against the real local Docker daemon using isolated, ephemeral fixtures.
Validates internal bridge networking, non-root execution, zero host ports,
and guaranteed cleanup.
"""

import asyncio
import os
import shutil
import tempfile
import uuid
from pathlib import Path
import pytest

from app.runtime.contracts import RuntimeLimits, RuntimeStatus
from app.runtime.docker_runtime_executor import DockerRuntimeExecutor
from app.schemas.runtime import ApplicationRuntimeManifest, RuntimeFramework, RuntimeLanguage


@pytest.fixture
def docker_executor():
    return DockerRuntimeExecutor(image="se-intelliplatform-sandbox:latest")


@pytest.mark.asyncio
async def test_live_docker_availability(docker_executor):
    """Confirm Docker daemon is accessible."""
    is_available = await docker_executor.check_docker_available()
    if not is_available:
        pytest.skip("Docker daemon is not available in current environment.")
    assert is_available is True


@pytest.mark.asyncio
async def test_live_isolated_application_runtime_lifecycle(docker_executor):
    """Full lifecycle integration test:

    1. Create internal network
    2. Start Python HTTP application container
    3. Verify non-root user (UID 2000)
    4. Verify zero host ports published
    5. Poll health check (200 OK)
    6. Verify Docker socket is inaccessible
    7. Clean teardown of container and network
    """
    if not await docker_executor.check_docker_available():
        pytest.skip("Docker daemon is not available.")

    run_id = uuid.uuid4()
    container_name = f"app-live-{run_id}"
    network_name = f"se_net_live_{run_id}"
    port = 8000
    temp_dir = tempfile.mkdtemp(prefix="se_live_test_")

    try:
        # Create minimal index.html to serve on /docs
        docs_dir = os.path.join(temp_dir, "docs")
        os.makedirs(docs_dir, exist_ok=True)
        with open(os.path.join(docs_dir, "index.html"), "w", encoding="utf-8") as f:
            f.write("<html><body><h1>FastAPI - Swagger UI Mock</h1></body></html>")

        # Manifest using Python standard library HTTP server
        manifest = ApplicationRuntimeManifest(
            runtime_type="docker",
            language=RuntimeLanguage.PYTHON,
            framework=RuntimeFramework.FASTAPI,
            entrypoint="app.main:app",
            startup_command=["python", "-m", "http.server", str(port)],
            application_port=port,
            health_check_path="/docs/",
            health_check_method="GET",
            health_check_timeout_seconds=10.0,
        )

        limits = RuntimeLimits(
            memory_limit="512m",
            cpus=1.0,
            max_pids=64,
            startup_timeout_seconds=10.0,
        )

        # 1. Create internal network
        await docker_executor.create_internal_network(network_name)

        # 2. Launch container
        await docker_executor.start_application_container(
            container_name=container_name,
            network_name=network_name,
            workspace_dir=temp_dir,
            manifest=manifest,
            limits=limits,
        )

        # 3. Verify container is running as non-root (UID 2000)
        proc_user = await asyncio.create_subprocess_exec(
            "docker", "exec", container_name, "id", "-u",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout_user, _ = await proc_user.communicate()
        assert stdout_user.decode("utf-8").strip() == "2000"

        # 4. Verify ZERO host ports are published
        proc_port = await asyncio.create_subprocess_exec(
            "docker", "port", container_name,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout_port, _ = await proc_port.communicate()
        # docker port must return completely empty output (no published mappings)
        assert stdout_port.decode("utf-8").strip() == ""

        # 5. Verify Docker socket is inaccessible
        proc_sock = await asyncio.create_subprocess_exec(
            "docker", "exec", container_name, "test", "-e", "/var/run/docker.sock",
            stdout=asyncio.subprocess.DEVNULL,
            stderr=asyncio.subprocess.DEVNULL,
        )
        assert await proc_sock.wait() != 0  # Socket must not exist

        # 6. Verify health check succeeds internally
        healthy, health_msg = await docker_executor.poll_health(
            container_name=container_name,
            port=port,
            path="/docs/",
            method="GET",
            timeout_seconds=10.0,
        )
        assert healthy is True
        assert "readiness confirmed" in health_msg

        # 7. Collect logs
        stdout, stderr, is_truncated = await docker_executor.get_container_logs(container_name)
        assert is_truncated is False

    finally:
        # Teardown
        await docker_executor.stop_and_remove_container(container_name)
        await docker_executor.remove_network(network_name)
        shutil.rmtree(temp_dir, ignore_errors=True)

    # Confirm container is gone
    is_running, _ = await docker_executor.get_container_status(container_name)
    assert is_running is False


@pytest.mark.asyncio
async def test_live_invalid_application_fails_safely(docker_executor):
    """Verify that a failing application container exits cleanly and is torn down."""
    if not await docker_executor.check_docker_available():
        pytest.skip("Docker daemon is not available.")

    run_id = uuid.uuid4()
    container_name = f"app-fail-{run_id}"
    network_name = f"se_net_fail_{run_id}"
    temp_dir = tempfile.mkdtemp(prefix="se_live_fail_")

    try:
        (Path(temp_dir) / "fail.py").write_text("import sys\nsys.exit(42)\n")

        manifest = ApplicationRuntimeManifest(
            runtime_type="docker",
            language=RuntimeLanguage.PYTHON,
            framework=RuntimeFramework.FASTAPI,
            entrypoint="app.main:app",
            startup_command=["python", "fail.py"],
            application_port=8000,
            health_check_path="/docs",
            health_check_method="GET",
            health_check_timeout_seconds=3.0,
        )

        limits = RuntimeLimits(startup_timeout_seconds=3.0)

        await docker_executor.create_internal_network(network_name)
        await docker_executor.start_application_container(
            container_name=container_name,
            network_name=network_name,
            workspace_dir=temp_dir,
            manifest=manifest,
            limits=limits,
        )

        # Give it a brief moment to exit
        await asyncio.sleep(0.5)

        # Health polling should report container exited prematurely
        healthy, health_msg = await docker_executor.poll_health(
            container_name=container_name,
            port=8000,
            path="/docs",
            timeout_seconds=3.0,
        )
        assert healthy is False
        assert "exited prematurely" in health_msg.lower() or "exit code" in health_msg.lower()

    finally:
        await docker_executor.stop_and_remove_container(container_name)
        await docker_executor.remove_network(network_name)
        shutil.rmtree(temp_dir, ignore_errors=True)

    is_running, _ = await docker_executor.get_container_status(container_name)
    assert is_running is False


@pytest.mark.asyncio
async def test_live_health_check_timeout_handles_safely(docker_executor):
    """Verify that an unresponsive endpoint times out without hanging or resource leaks."""
    if not await docker_executor.check_docker_available():
        pytest.skip("Docker daemon is not available.")

    run_id = uuid.uuid4()
    container_name = f"app-timeout-{run_id}"
    network_name = f"se_net_timeout_{run_id}"
    temp_dir = tempfile.mkdtemp(prefix="se_live_timeout_")

    try:
        # Runs server on 8001, but manifest probes /nonexistent on port 8001 with short timeout
        manifest = ApplicationRuntimeManifest(
            runtime_type="docker",
            language=RuntimeLanguage.PYTHON,
            framework=RuntimeFramework.FASTAPI,
            entrypoint="app.main:app",
            startup_command=["python", "-m", "http.server", "8001"],
            application_port=8001,
            health_check_path="/nonexistent_path_404",
            health_check_method="GET",
            health_check_timeout_seconds=2.0,
        )

        limits = RuntimeLimits(startup_timeout_seconds=2.0)

        await docker_executor.create_internal_network(network_name)
        await docker_executor.start_application_container(
            container_name=container_name,
            network_name=network_name,
            workspace_dir=temp_dir,
            manifest=manifest,
            limits=limits,
        )

        healthy, health_msg = await docker_executor.poll_health(
            container_name=container_name,
            port=8001,
            path="/nonexistent_path_404",
            timeout_seconds=2.0,
            interval_seconds=0.3,
        )
        assert healthy is False
        assert "timed out" in health_msg.lower()

    finally:
        await docker_executor.stop_and_remove_container(container_name)
        await docker_executor.remove_network(network_name)
        shutil.rmtree(temp_dir, ignore_errors=True)

    is_running, _ = await docker_executor.get_container_status(container_name)
    assert is_running is False
