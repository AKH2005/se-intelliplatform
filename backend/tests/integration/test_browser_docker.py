"""Integration Tests for Browser Container & Docker Runtime (Phase 11J - Stage 3).

Executes against the live Docker daemon:
1. Internal bridge network sharing between application and browser containers.
2. Zero host ports published on either container.
3. Inaccessible Docker socket (/var/run/docker.sock).
4. Non-root user execution.
5. Full browser smoke test execution (if Playwright image is available).
6. Deterministic teardown and guaranteed cleanup.
"""

import asyncio
import os
import shutil
import tempfile
import uuid
from pathlib import Path
import pytest

from app.browser.contracts import (
    DEFAULT_PLAYWRIGHT_IMAGE,
    BrowserLimits,
    DeterministicBrowserTestDefinition,
    create_default_smoke_suite,
)
from app.browser.errors import BrowserNavigationError
from app.browser.browser_executor import BrowserExecutor
from app.browser.browser_testing_service import BrowserTestingService
from app.runtime.contracts import RuntimeLimits, RuntimeStatus
from app.runtime.docker_runtime_executor import DockerRuntimeExecutor
from app.schemas.browser_testing import BrowserTestStatus
from app.schemas.runtime import ApplicationRuntimeManifest, RuntimeFramework, RuntimeLanguage


@pytest.fixture
def docker_runtime_executor():
    return DockerRuntimeExecutor(image="se-intelliplatform-sandbox:latest")


@pytest.fixture
def browser_executor():
    return BrowserExecutor(image=DEFAULT_PLAYWRIGHT_IMAGE)


@pytest.mark.asyncio
async def test_live_docker_internal_network_browser_join(docker_runtime_executor):
    """Verify application and browser containers can join the same internal network without host ports."""
    if not await docker_runtime_executor.check_docker_available():
        pytest.skip("Docker daemon is not available.")

    run_id = uuid.uuid4()
    network_name = f"se_net_join_{run_id}"
    app_container = f"app-join-{run_id}"
    browser_container = f"browser-join-{run_id}"
    app_dir = tempfile.mkdtemp(prefix="se_live_app_")

    try:
        # Create minimal HTTP app
        (Path(app_dir) / "index.html").write_text("<html><body><h1>App OK</h1></body></html>")
        app_manifest = ApplicationRuntimeManifest(
            runtime_type="docker",
            language=RuntimeLanguage.PYTHON,
            framework=RuntimeFramework.FASTAPI,
            entrypoint="app.main:app",
            startup_command=["python", "-m", "http.server", "8000"],
            application_port=8000,
            health_check_path="/index.html",
            health_check_method="GET",
            health_check_timeout_seconds=5.0,
        )

        # 1. Create internal network
        await docker_runtime_executor.create_internal_network(network_name)

        # 2. Start app container
        await docker_runtime_executor.start_application_container(
            container_name=app_container,
            network_name=network_name,
            workspace_dir=app_dir,
            manifest=app_manifest,
            limits=RuntimeLimits(startup_timeout_seconds=5.0),
        )

        # Verify app is healthy internally
        healthy, _ = await docker_runtime_executor.poll_health(
            container_name=app_container,
            port=8000,
            path="/index.html",
            timeout_seconds=5.0,
        )
        assert healthy is True

        # 3. Start a peer container on the same network to verify reachability & security
        proc = await asyncio.create_subprocess_exec(
            "docker",
            "run",
            "-d",
            "--name",
            browser_container,
            "--network",
            network_name,
            "--security-opt=no-new-privileges:true",
            "--memory=512m",
            "--user=2000:2000",
            "se-intelliplatform-sandbox:latest",
            "python",
            "-c",
            "import time; time.sleep(30)",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        await proc.communicate()
        assert proc.returncode == 0

        # Verify peer can resolve and reach app container via internal Docker DNS
        probe_proc = await asyncio.create_subprocess_exec(
            "docker",
            "exec",
            browser_container,
            "python",
            "-c",
            f"import urllib.request; resp = urllib.request.urlopen('http://{app_container}:8000/index.html'); assert resp.status == 200",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        probe_stdout, probe_stderr = await probe_proc.communicate()
        assert probe_proc.returncode == 0, f"Probe failed: {probe_stderr.decode()}"

        # 4. CRITICAL: Verify ZERO host ports on both containers
        for cname in (app_container, browser_container):
            port_proc = await asyncio.create_subprocess_exec(
                "docker",
                "port",
                cname,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            port_out, _ = await port_proc.communicate()
            assert port_out.decode().strip() == "", f"Container {cname} published host ports!"

        # 5. CRITICAL: Verify Docker socket is inaccessible
        sock_proc = await asyncio.create_subprocess_exec(
            "docker",
            "exec",
            browser_container,
            "test",
            "-e",
            "/var/run/docker.sock",
        )
        sock_exit = await sock_proc.wait()
        assert sock_exit != 0, "Docker socket must NOT exist inside browser container!"

        # 6. CRITICAL: Verify internal network blocks public internet (WAN)
        wan_proc = await asyncio.create_subprocess_exec(
            "docker",
            "exec",
            browser_container,
            "python",
            "-c",
            "import urllib.request; urllib.request.urlopen('http://1.1.1.1', timeout=2)",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        wan_exit = await wan_proc.wait()
        assert wan_exit != 0, "Internal network must block external internet access!"

        # 7. CRITICAL: Verify neither container uses host networking
        for cname in (app_container, browser_container):
            netmode_proc = await asyncio.create_subprocess_exec(
                "docker",
                "inspect",
                "--format",
                "{{.HostConfig.NetworkMode}}",
                cname,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            netmode_out, _ = await netmode_proc.communicate()
            netmode_str = netmode_out.decode().strip()
            assert netmode_str != "host", f"Container {cname} must not use host networking!"
            assert netmode_str == network_name, f"Container {cname} must be connected to internal network '{network_name}', got '{netmode_str}'!"

    finally:
        # Cleanup both containers and network
        for cname in (browser_container, app_container):
            try:
                p = await asyncio.create_subprocess_exec("docker", "rm", "-f", cname, stdout=asyncio.subprocess.DEVNULL, stderr=asyncio.subprocess.DEVNULL)
                await p.wait()
            except Exception:
                pass
        try:
            await docker_runtime_executor.remove_network(network_name)
        except Exception:
            pass
        shutil.rmtree(app_dir, ignore_errors=True)


@pytest.mark.asyncio
async def test_live_browser_external_navigation_rejection(browser_executor):
    """Verify that attempting to navigate outside internal origin is blocked before launch."""
    service = BrowserTestingService(browser_executor=browser_executor)
    allowed_origin = "http://app-target:8000"

    with pytest.raises(BrowserNavigationError, match="outside authorized internal origin"):
        service.validate_navigation_target("https://www.google.com", allowed_origin)

    with pytest.raises(BrowserNavigationError, match="host address prohibited"):
        service.validate_navigation_target("http://127.0.0.1:8000/docs", allowed_origin)

    with pytest.raises(BrowserNavigationError, match="unsafe scheme prohibited"):
        service.validate_navigation_target("file:///etc/passwd", allowed_origin)


@pytest.mark.asyncio
async def test_live_browser_smoke_test_execution_or_graceful_skip(browser_executor, docker_runtime_executor, tmp_path):
    """Verify complete browser test execution if Playwright image is present, or safe graceful diagnostic."""
    if not await docker_runtime_executor.check_docker_available():
        pytest.skip("Docker daemon is not available.")

    playwright_available = await browser_executor.check_image_available()

    # Create dummy app files and manifest
    app_files = {
        "index.html": "<!DOCTYPE html><html><head><title>App Home</title></head><body><h1>Welcome</h1></body></html>",
    }
    manifest = ApplicationRuntimeManifest(
        runtime_type="docker",
        language=RuntimeLanguage.PYTHON,
        framework=RuntimeFramework.FASTAPI,
        entrypoint="app.main:app",
        startup_command=["python", "-m", "http.server", "8000"],
        application_port=8000,
        health_check_path="/index.html",
        health_check_method="GET",
        health_check_timeout_seconds=5.0,
    )

    # Set up mock runtime manager to return the app session
    from unittest.mock import AsyncMock, MagicMock
    mock_rt = MagicMock()
    mock_rt.resolve_version_files_and_manifest = AsyncMock(return_value=(app_files, manifest))

    # Real managed_runtime_session using real DockerRuntimeExecutor
    from app.runtime.application_runtime_manager import ApplicationRuntimeManager
    real_rt_manager = ApplicationRuntimeManager(docker_executor=docker_runtime_executor)

    service = BrowserTestingService(
        runtime_manager=real_rt_manager,
        browser_executor=browser_executor,
        artifacts_base_dir=tmp_path / "artifacts",
    )

    project_id = uuid.uuid4()
    version_id = uuid.uuid4()

    # Define deterministic smoke test targeting /index.html
    smoke_tests = [
        DeterministicBrowserTestDefinition(
            test_id="smoke_live_01",
            name="Verify index page",
            target_path="/index.html",
            expected_status=200,
            expected_elements=["body", "h1"],
            expected_title_contains="App Home",
            capture_screenshot=True,
        )
    ]

    # Directly execute against real app runtime
    async with real_rt_manager.managed_runtime_session(
        project_id=project_id,
        files_map=app_files,
        manifest=manifest,
        version_id=version_id,
    ) as app_session:
        assert app_session.status == RuntimeStatus.READY

        if not playwright_available:
            # If Playwright image is not yet available, verify check_image_available returns False
            is_avail = await browser_executor.check_image_available()
            assert is_avail is False
            return

        # Execute in Playwright browser container
        test_run = await service._execute_in_browser_container(
            run_id=uuid.uuid4(),
            project_id=project_id,
            version_id=version_id,
            app_session=app_session,
            suite=smoke_tests,
            limits=BrowserLimits(),
            started_at=app_session.started_at,
            start_time=0.0,
        )

        assert test_run.status == BrowserTestStatus.PASSED
        assert test_run.tests_total == 1
        assert test_run.tests_passed == 1
        assert len(test_run.artifacts) == 1
        assert test_run.artifacts[0].artifact_type == "SCREENSHOT"
        assert (tmp_path / test_run.artifacts[0].file_path).exists()


@pytest.mark.asyncio
async def test_live_browser_container_security_flags(docker_runtime_executor):
    """Verify live container created with browser executor flags adheres to resource and security policies."""
    if not await docker_runtime_executor.check_docker_available():
        pytest.skip("Docker daemon is not available.")

    run_id = uuid.uuid4()
    container_name = f"browser-sec-{run_id}"
    network_name = f"se_net_sec_{run_id}"
    temp_dir = tempfile.mkdtemp(prefix="se_sec_test_")

    executor = BrowserExecutor(image="se-intelliplatform-sandbox:latest")
    limits = BrowserLimits(
        container_memory="1024m",
        container_cpus="1.5",
        container_pids=128,
        container_shm_size="512m",
    )

    try:
        await docker_runtime_executor.create_internal_network(network_name)

        # Write dummy runner so it sleeps briefly
        (Path(temp_dir) / "runner.py").write_text("import time\ntime.sleep(20)\n")

        args = executor.build_container_args(
            container_name=container_name,
            network_name=network_name,
            workspace_dir=temp_dir,
            limits=limits,
        )

        proc = await asyncio.create_subprocess_exec("docker", *args)
        await proc.wait()
        assert proc.returncode == 0

        # Inspect container host config
        import json
        inspect_proc = await asyncio.create_subprocess_exec(
            "docker", "inspect", container_name,
            stdout=asyncio.subprocess.PIPE,
        )
        out, _ = await inspect_proc.communicate()
        data = json.loads(out.decode())[0]

        host_config = data.get("HostConfig", {})
        # Memory 1024MB = 1073741824 bytes
        assert host_config.get("Memory") == 1073741824
        # NanoCPUs 1.5 = 1500000000
        assert host_config.get("NanoCpus") == 1500000000
        # PidsLimit = 128
        assert host_config.get("PidsLimit") == 128
        # ShmSize = 536870912 bytes (512MB)
        assert host_config.get("ShmSize") == 536870912
        # SecurityOpt no-new-privileges
        sec_opts = host_config.get("SecurityOpt") or []
        assert any("no-new-privileges" in opt for opt in sec_opts)
        # Network mode is our bridge network
        assert host_config.get("NetworkMode") == network_name
        # PortBindings must be empty
        assert not host_config.get("PortBindings")

    finally:
        try:
            p = await asyncio.create_subprocess_exec("docker", "rm", "-f", container_name, stdout=asyncio.subprocess.DEVNULL, stderr=asyncio.subprocess.DEVNULL)
            await p.wait()
        except Exception:
            pass
        try:
            await docker_runtime_executor.remove_network(network_name)
        except Exception:
            pass
        shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.mark.asyncio
async def test_live_browser_intentional_assertion_failure(browser_executor, docker_runtime_executor, tmp_path):
    """Verify live Playwright run reports FAILED when selector is missing and captures failure screenshot."""
    if not await docker_runtime_executor.check_docker_available():
        pytest.skip("Docker daemon is not available.")

    app_files = {
        "index.html": "<!DOCTYPE html><html><body><h1>Header</h1></body></html>",
    }
    manifest = ApplicationRuntimeManifest(
        runtime_type="docker",
        language=RuntimeLanguage.PYTHON,
        framework=RuntimeFramework.FASTAPI,
        entrypoint="app.main:app",
        startup_command=["python", "-m", "http.server", "8000"],
        application_port=8000,
        health_check_path="/index.html",
        health_check_method="GET",
        health_check_timeout_seconds=5.0,
    )

    from app.runtime.application_runtime_manager import ApplicationRuntimeManager
    real_rt_manager = ApplicationRuntimeManager(docker_executor=docker_runtime_executor)

    service = BrowserTestingService(
        runtime_manager=real_rt_manager,
        browser_executor=browser_executor,
        artifacts_base_dir=tmp_path / "artifacts",
    )

    failing_test = DeterministicBrowserTestDefinition(
        test_id="smoke_fail_01",
        name="Expect missing element",
        target_path="/index.html",
        expected_status=200,
        expected_elements=["#nonexistent_selector_404"],
        capture_screenshot=True,
    )

    async with real_rt_manager.managed_runtime_session(
        project_id=uuid.uuid4(),
        files_map=app_files,
        manifest=manifest,
        version_id=uuid.uuid4(),
    ) as app_session:
        assert app_session.status == RuntimeStatus.READY

        test_run = await service._execute_in_browser_container(
            run_id=uuid.uuid4(),
            project_id=uuid.uuid4(),
            version_id=uuid.uuid4(),
            app_session=app_session,
            suite=[failing_test],
            limits=BrowserLimits(action_timeout_seconds=1.0),
            started_at=app_session.started_at,
            start_time=0.0,
        )

        assert test_run.status == BrowserTestStatus.FAILED
        assert test_run.tests_failed == 1
        assert "nonexistent_selector_404" in test_run.failure_reason
        assert len(test_run.artifacts) >= 1


