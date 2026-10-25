"""Unit Tests for Browser Testing Subsystem (Phase 11J - Stage 3).

Validates:
- URL allowlisting and navigation security
- Deterministic test definition and interaction constraints
- Browser container argument construction and security hardening
- Concurrency limiting (semaphore max 2)
- Artifact path safety and bounds
- Status mapping and error handling
- Cleanup guarantees on failure and timeouts
"""

import asyncio
import json
import os
import shutil
import tempfile
import uuid
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch
import pytest

from app.browser.contracts import (
    DEFAULT_PLAYWRIGHT_IMAGE,
    BrowserInteractionType,
    BrowserLimits,
    DeterministicBrowserTestDefinition,
    DeterministicInteraction,
    create_default_smoke_suite,
)
from app.browser.errors import (
    BrowserNavigationError,
    BrowserStartupError,
    BrowserTimeoutError,
)
from app.browser.browser_executor import BrowserExecutor
from app.browser.browser_testing_service import BrowserTestingService
from app.core.exceptions import ValidationError
from app.runtime.contracts import RuntimeLimits, RuntimeSessionResult, RuntimeStatus
from app.schemas.browser_testing import (
    BrowserArtifactReference,
    BrowserArtifactType,
    BrowserConsoleError,
    BrowserNetworkRecord,
    BrowserTestCaseResult,
    BrowserTestRun,
    BrowserTestStatus,
)


# ==============================================================================
# 1. URL Allowlisting & Navigation Security Tests
# ==============================================================================

def test_url_allowlisting_valid():
    """Verify internal origin navigation passes allowlist check."""
    service = BrowserTestingService()
    allowed = "http://app-12345:8000"
    
    # Should not raise
    service.validate_navigation_target("http://app-12345:8000/", allowed)
    service.validate_navigation_target("http://app-12345:8000/docs", allowed)
    service.validate_navigation_target("http://app-12345:8000/api/v1/health", allowed)


def test_url_allowlisting_rejects_localhost_and_host_ip():
    """Verify localhost, 127.0.0.1, and 0.0.0.0 are strictly rejected."""
    service = BrowserTestingService()
    allowed = "http://app-12345:8000"

    with pytest.raises(BrowserNavigationError, match="host address prohibited"):
        service.validate_navigation_target("http://localhost:8000/docs", allowed)

    with pytest.raises(BrowserNavigationError, match="host address prohibited"):
        service.validate_navigation_target("http://127.0.0.1:8000/docs", allowed)

    with pytest.raises(BrowserNavigationError, match="host address prohibited"):
        service.validate_navigation_target("http://0.0.0.0:8000/docs", allowed)


def test_url_allowlisting_rejects_unsafe_schemes():
    """Verify file://, javascript:, data: schemes are strictly prohibited."""
    service = BrowserTestingService()
    allowed = "http://app-12345:8000"

    with pytest.raises(BrowserNavigationError, match="unsafe scheme prohibited"):
        service.validate_navigation_target("file:///etc/passwd", allowed)

    with pytest.raises(BrowserNavigationError, match="unsafe scheme prohibited"):
        service.validate_navigation_target("javascript:alert(1)", allowed)

    with pytest.raises(BrowserNavigationError, match="unsafe scheme prohibited"):
        service.validate_navigation_target("data:text/html,<h1>Hello</h1>", allowed)


def test_url_allowlisting_rejects_external_origin():
    """Verify external domains and URLs outside internal origin are rejected."""
    service = BrowserTestingService()
    allowed = "http://app-12345:8000"

    with pytest.raises(BrowserNavigationError, match="outside authorized internal origin"):
        service.validate_navigation_target("http://google.com", allowed)

    with pytest.raises(BrowserNavigationError, match="outside authorized internal origin"):
        service.validate_navigation_target("http://app-67890:8000/docs", allowed)


# ==============================================================================
# 2. Test Definitions & Interaction Safety Tests
# ==============================================================================

def test_deterministic_test_definition_validation():
    """Verify deterministic test definition fields and path sanitization."""
    test_def = DeterministicBrowserTestDefinition(
        test_id="smoke_01",
        name="Test root page",
        target_path="api/health",
        expected_status=200,
    )
    assert test_def.target_path == "/api/health"

    # Reject full URL in target path
    with pytest.raises(ValueError, match="relative path"):
        DeterministicBrowserTestDefinition(
            test_id="smoke_bad",
            name="Bad target",
            target_path="http://external.com/docs",
        )

    # Reject traversal
    with pytest.raises(ValueError, match="traversal"):
        DeterministicBrowserTestDefinition(
            test_id="smoke_bad_traversal",
            name="Bad target",
            target_path="/../../etc/passwd",
        )


def test_deterministic_interaction_rejects_script_injection():
    """Verify script injection in interaction selectors is blocked."""
    with pytest.raises(ValueError, match="Unsafe pattern"):
        DeterministicInteraction(
            action=BrowserInteractionType.CLICK,
            selector="<script>alert(1)</script>",
        )

    with pytest.raises(ValueError, match="Unsafe pattern"):
        DeterministicInteraction(
            action=BrowserInteractionType.FILL,
            selector="button[onclick='eval()']",
        )


def test_default_smoke_suite_generation():
    """Verify standard default smoke test suite creation."""
    suite = create_default_smoke_suite(health_path="/api/docs")
    assert len(suite) == 2
    assert suite[0].test_id == "smoke_01_root_page_load"
    assert suite[0].target_path == "/"
    assert suite[1].test_id == "smoke_02_health_or_docs_endpoint"
    assert suite[1].target_path == "/api/docs"


# ==============================================================================
# 3. Browser Executor & Container Hardening Tests
# ==============================================================================

def test_browser_container_args_security():
    """Verify security flags, resource quotas, and absence of host ports."""
    executor = BrowserExecutor()
    limits = BrowserLimits(
        container_memory="1024m",
        container_cpus="1.5",
        container_pids=128,
        container_shm_size="512m",
    )
    args = executor.build_container_args(
        container_name="browser-test-1",
        network_name="se_net_123",
        workspace_dir="C:/temp/browser",
        limits=limits,
    )

    # Must contain essential security and resource bounds
    assert "--name" in args and "browser-test-1" in args
    assert "--network" in args and "se_net_123" in args
    assert "--memory=1024m" in args
    assert "--cpus=1.5" in args
    assert "--pids-limit=128" in args
    assert "--shm-size=512m" in args
    assert "--security-opt=no-new-privileges:true" in args
    assert "--user" in args and "1000:1000" in args

    # MUST NOT contain host publishing or host network
    assert "-p" not in args
    assert "--publish" not in args
    assert "--network=host" not in args
    assert "host" not in [args[i+1] for i, x in enumerate(args) if x == "--network"]


# ==============================================================================
# 4. Concurrency Limit Tests
# ==============================================================================

@pytest.mark.asyncio
async def test_browser_concurrency_limit_enforced():
    """Verify maximum 2 concurrent browser sessions: 3rd returns RESOURCE_LIMIT."""
    service = BrowserTestingService(max_concurrent=2)
    semaphore = service.get_semaphore()

    # Artificially exhaust semaphore
    await semaphore.acquire()
    await semaphore.acquire()

    try:
        project_id = uuid.uuid4()
        version_id = uuid.uuid4()
        result = await service.execute_browser_tests(project_id, version_id)

        assert result.status == BrowserTestStatus.RESOURCE_LIMIT
        assert "exceeded" in result.failure_reason.lower()
        assert result.duration_seconds == 0.0
    finally:
        semaphore.release()
        semaphore.release()


# ==============================================================================
# 5. Status Mapping & Application Runtime Integration Tests
# ==============================================================================

@pytest.mark.asyncio
async def test_status_mapping_on_application_startup_failure():
    """Verify that an application runtime failure maps cleanly to STARTUP_FAILED."""
    mock_runtime_manager = MagicMock()
    mock_runtime_manager.resolve_version_files_and_manifest = AsyncMock(
        return_value=({"app/main.py": "print('hello')"}, MagicMock(health_check_path="/docs"))
    )

    # Mock managed_runtime_session to return STARTUP_FAILED
    failed_session = RuntimeSessionResult(
        project_id=uuid.uuid4(),
        status=RuntimeStatus.STARTUP_FAILED,
        internal_url="",
        container_name="",
        network_name="",
        failure_reason="Application process exited with code 1",
    )

    class MockAsyncContext:
        async def __aenter__(self):
            return failed_session
        async def __aexit__(self, exc_type, exc_val, exc_tb):
            pass

    mock_runtime_manager.managed_runtime_session.return_value = MockAsyncContext()

    service = BrowserTestingService(runtime_manager=mock_runtime_manager)
    project_id = uuid.uuid4()
    version_id = uuid.uuid4()

    run_result = await service.execute_browser_tests(project_id, version_id)
    assert run_result.status == BrowserTestStatus.STARTUP_FAILED
    assert "exited with code 1" in run_result.failure_reason


@pytest.mark.asyncio
async def test_cross_project_isolation():
    """Verify cross-project version access is rejected with VALIDATION_ERROR."""
    mock_runtime_manager = MagicMock()
    mock_runtime_manager.resolve_version_files_and_manifest = AsyncMock(
        side_effect=ValidationError("Version does not belong to project")
    )

    service = BrowserTestingService(runtime_manager=mock_runtime_manager)
    project_id = uuid.uuid4()
    version_id = uuid.uuid4()

    run_result = await service.execute_browser_tests(project_id, version_id)
    assert run_result.status == BrowserTestStatus.VALIDATION_ERROR
    assert "does not belong" in run_result.failure_reason


# ==============================================================================
# 6. Artifact & Evidence Bounds Tests
# ==============================================================================

def test_screenshot_path_safety_and_containment():
    """Verify artifact reference path validation against traversal and Windows drive letters."""
    valid_ref = BrowserArtifactReference(
        artifact_type=BrowserArtifactType.SCREENSHOT,
        file_path="artifacts/projects/1/versions/2/browser/run_1/test.png",
        size_bytes=1024,
    )
    assert valid_ref.file_path == "artifacts/projects/1/versions/2/browser/run_1/test.png"

    with pytest.raises(ValueError, match="path traversal"):
        BrowserArtifactReference(
            artifact_type=BrowserArtifactType.SCREENSHOT,
            file_path="artifacts/../../etc/passwd",
        )

    with pytest.raises(ValueError, match="relative, not absolute"):
        BrowserArtifactReference(
            artifact_type=BrowserArtifactType.SCREENSHOT,
            file_path="/var/log/secret.png",
        )


def test_console_and_network_bounds():
    """Verify console and network error limits on BrowserTestCaseResult."""
    errors = [
        BrowserConsoleError(level="error", message=f"Error {i}") for i in range(10)
    ]
    net_records = [
        BrowserNetworkRecord(method="GET", url=f"http://app/api/{i}", failed=True)
        for i in range(10)
    ]

    tc = BrowserTestCaseResult(
        test_id="test_bounded",
        name="Test Bounded Evidence",
        status=BrowserTestStatus.PASSED,
        console_errors=errors,
        network_errors=net_records,
    )
    assert len(tc.console_errors) == 10
    assert len(tc.network_errors) == 10

    # Exceeding 10 should fail Pydantic max_length validation
    with pytest.raises(ValueError):
        BrowserTestCaseResult(
            test_id="test_overflow",
            name="Test Overflow",
            status=BrowserTestStatus.PASSED,
            console_errors=errors + [BrowserConsoleError(level="error", message="overflow")],
        )


# ==============================================================================
# 7. Timeout & Cleanup Guarantees
# ==============================================================================

@pytest.mark.asyncio
async def test_browser_timeout_handling():
    """Verify BrowserTimeoutError yields BrowserTestStatus.TIMEOUT."""
    mock_runtime_manager = MagicMock()
    mock_runtime_manager.resolve_version_files_and_manifest = AsyncMock(
        return_value=({"app/main.py": "code"}, MagicMock(health_check_path="/docs"))
    )

    ready_session = RuntimeSessionResult(
        project_id=uuid.uuid4(),
        status=RuntimeStatus.READY,
        internal_url="http://app-123:8000",
        container_name="app-123",
        network_name="se_net_123",
    )

    class MockAsyncContext:
        async def __aenter__(self):
            return ready_session
        async def __aexit__(self, exc_type, exc_val, exc_tb):
            pass

    mock_runtime_manager.managed_runtime_session.return_value = MockAsyncContext()

    mock_executor = MagicMock()
    mock_executor.check_image_available = AsyncMock(return_value=True)
    mock_executor.run_browser_container = AsyncMock(
        side_effect=BrowserTimeoutError("Browser exceeded timeout of 60.0s")
    )
    mock_executor.stop_and_remove_container = AsyncMock()

    service = BrowserTestingService(
        runtime_manager=mock_runtime_manager,
        browser_executor=mock_executor,
    )

    run_result = await service.execute_browser_tests(uuid.uuid4(), uuid.uuid4())
    assert run_result.status == BrowserTestStatus.TIMEOUT
    assert "exceeded timeout" in run_result.failure_reason
    assert mock_executor.stop_and_remove_container.called


def test_browser_limits_defaults():
    """Verify default resource limits match approved architecture."""
    limits = BrowserLimits()
    assert limits.max_concurrent_sessions == 2
    assert limits.session_timeout_seconds == 60.0
    assert limits.container_memory == "1024m"
    assert limits.container_cpus == "1.5"
    assert limits.container_pids == 128
    assert limits.container_shm_size == "512m"


@pytest.mark.asyncio
async def test_successful_browser_test_flow(tmp_path):
    """Verify complete successful execution flow with mocked runner output and screenshot copying."""
    mock_runtime_manager = MagicMock()
    mock_runtime_manager.resolve_version_files_and_manifest = AsyncMock(
        return_value=({"app/main.py": "code"}, MagicMock(health_check_path="/docs"))
    )

    ready_session = RuntimeSessionResult(
        project_id=uuid.uuid4(),
        status=RuntimeStatus.READY,
        internal_url="http://app-live:8000",
        container_name="app-live",
        network_name="se_net_live",
    )

    class MockAsyncContext:
        async def __aenter__(self):
            return ready_session
        async def __aexit__(self, exc_type, exc_val, exc_tb):
            pass

    mock_runtime_manager.managed_runtime_session.return_value = MockAsyncContext()

    mock_executor = MagicMock()
    mock_executor.check_image_available = AsyncMock(return_value=True)

    async def fake_run_browser(container_name, network_name, workspace_dir, limits):
        # Simulate runner writing results.json and a screenshot
        os.makedirs(os.path.join(workspace_dir, "screenshots"), exist_ok=True)
        ss_path = os.path.join(workspace_dir, "screenshots", "smoke_01.png")
        with open(ss_path, "wb") as f:
            f.write(b"\x89PNG\r\n\x1a\nfake_image_bytes")

        results_data = {
            "test_cases": [
                {
                    "test_id": "smoke_01",
                    "name": "Verify Root",
                    "status": "PASSED",
                    "duration_seconds": 1.25,
                    "assertion_summary": "Page loaded successfully",
                    "screenshots": [
                        {
                            "artifact_type": "SCREENSHOT",
                            "file_path": "screenshots/smoke_01.png",
                            "size_bytes": 24,
                            "content_type": "image/png",
                            "caption": "Root page",
                        }
                    ],
                    "console_errors": [],
                    "network_errors": [],
                }
            ]
        }
        with open(os.path.join(workspace_dir, "results.json"), "w", encoding="utf-8") as rf:
            json.dump(results_data, rf)
        return 0, "All tests passed", ""

    mock_executor.run_browser_container = AsyncMock(side_effect=fake_run_browser)
    mock_executor.stop_and_remove_container = AsyncMock()

    service = BrowserTestingService(
        runtime_manager=mock_runtime_manager,
        browser_executor=mock_executor,
        artifacts_base_dir=tmp_path / "artifacts",
    )

    project_id = uuid.uuid4()
    version_id = uuid.uuid4()
    test_run = await service.execute_browser_tests(project_id, version_id)

    assert test_run.status == BrowserTestStatus.PASSED
    assert test_run.tests_total == 1
    assert test_run.tests_passed == 1
    assert test_run.tests_failed == 0
    assert len(test_run.artifacts) == 1
    assert test_run.artifacts[0].artifact_type == BrowserArtifactType.SCREENSHOT
    assert "artifacts/projects/" in test_run.artifacts[0].file_path
    assert mock_executor.stop_and_remove_container.called


@pytest.mark.asyncio
async def test_failed_assertion_browser_test_flow(tmp_path):
    """Verify failed assertion execution flow with diagnostic preservation."""
    mock_runtime_manager = MagicMock()
    mock_runtime_manager.resolve_version_files_and_manifest = AsyncMock(
        return_value=({"app/main.py": "code"}, MagicMock(health_check_path="/docs"))
    )

    ready_session = RuntimeSessionResult(
        project_id=uuid.uuid4(),
        status=RuntimeStatus.READY,
        internal_url="http://app-fail:8000",
        container_name="app-fail",
        network_name="se_net_fail",
    )

    class MockAsyncContext:
        async def __aenter__(self):
            return ready_session
        async def __aexit__(self, exc_type, exc_val, exc_tb):
            pass

    mock_runtime_manager.managed_runtime_session.return_value = MockAsyncContext()

    mock_executor = MagicMock()
    mock_executor.check_image_available = AsyncMock(return_value=True)

    async def fake_run_browser(container_name, network_name, workspace_dir, limits):
        results_data = {
            "test_cases": [
                {
                    "test_id": "smoke_fail",
                    "name": "Verify Missing Button",
                    "status": "FAILED",
                    "duration_seconds": 2.1,
                    "failed_step": "Element '#login-button' not found",
                    "assertion_summary": "Expected selector '#login-button' to be visible, timed out",
                    "screenshots": [],
                    "console_errors": [{"level": "error", "message": "ReferenceError: foo is not defined"}],
                    "network_errors": [{"method": "GET", "url": "http://app/missing", "status_code": 404, "failed": True}],
                }
            ]
        }
        with open(os.path.join(workspace_dir, "results.json"), "w", encoding="utf-8") as rf:
            json.dump(results_data, rf)
        return 1, "Tests failed", ""

    mock_executor.run_browser_container = AsyncMock(side_effect=fake_run_browser)
    mock_executor.stop_and_remove_container = AsyncMock()

    service = BrowserTestingService(
        runtime_manager=mock_runtime_manager,
        browser_executor=mock_executor,
        artifacts_base_dir=tmp_path / "artifacts",
    )

    test_run = await service.execute_browser_tests(uuid.uuid4(), uuid.uuid4())
    assert test_run.status == BrowserTestStatus.FAILED
    assert test_run.tests_failed == 1
    assert "login-button" in test_run.failure_reason
    assert len(test_run.test_cases[0].console_errors) == 1
    assert len(test_run.test_cases[0].network_errors) == 1


@pytest.mark.asyncio
async def test_image_unavailable_error_handling():
    """Verify BROWSER_ERROR when Playwright Docker image is not available."""
    mock_runtime_manager = MagicMock()
    mock_runtime_manager.resolve_version_files_and_manifest = AsyncMock(
        return_value=({"app/main.py": "code"}, MagicMock(health_check_path="/docs"))
    )

    ready_session = RuntimeSessionResult(
        project_id=uuid.uuid4(),
        status=RuntimeStatus.READY,
        internal_url="http://app-live:8000",
        container_name="app-live",
        network_name="se_net_live",
    )

    class MockAsyncContext:
        async def __aenter__(self):
            return ready_session
        async def __aexit__(self, exc_type, exc_val, exc_tb):
            pass

    mock_runtime_manager.managed_runtime_session.return_value = MockAsyncContext()

    mock_executor = MagicMock()
    mock_executor.check_image_available = AsyncMock(return_value=False)

    service = BrowserTestingService(
        runtime_manager=mock_runtime_manager,
        browser_executor=mock_executor,
    )

    test_run = await service.execute_browser_tests(uuid.uuid4(), uuid.uuid4())
    assert test_run.status == BrowserTestStatus.BROWSER_ERROR
    assert "unavailable" in test_run.failure_reason

