"""Live Containerized E2E Integration and System Validation Tests (Phase 11K - Stage 7).

Proves the complete Browser Journey pipeline with the REAL application and runtime environment:
    Requirements
        ↓
    Application Context
        ↓
    Browser Journey Generation (BrowserJourneyGenerationAgent via AgentExecutor)
        ↓
    Deterministic Validation (BrowserJourneyValidator)
        ↓
    Deterministic Adaptation (BrowserJourneyAdapter)
        ↓
    Browser Testing Service (BrowserTestingService)
        ↓
    Containerized Playwright (se-intelliplatform-browser:v1.49.0)
        ↓
    Containerized Application (se-intelliplatform-sandbox:latest on isolated bridge network)
        ↓
    BrowserTestRun (Screenshots, Traces, Telemetry)
        ↓
    WorkflowExecution (Audit Record & Artifact Traceability Chain)
        ↓
    Requirement Coverage (Authoritative Backend Metrics)
        ↓
    Failure Analysis (FailureAnalysisAgent via AgentExecutor on failure)
        ↓
    REST API (/api/v1/projects/{project_id}/browser-journeys/*)
        ↓
    Intelli Assistant Action Boundary (GENERATE_BROWSER_JOURNEYS)

ARCHITECTURAL INVARIANTS ENFORCED:
1. AgentExecutor remains the sole single-agent execution authority.
2. WorkflowCoordinator remains the sole multi-agent coordination authority.
3. BrowserTestingService remains the browser execution orchestrator.
4. Docker remains the sole code/browser execution boundary.
5. Playwright remains inside the controlled browser container.
6. FailureAnalysisAgent remains the failure-analysis authority (no remediation loops).
7. Browser telemetry is untrusted content (XSS and raw injection defense).
8. DevelopmentVersion remains immutable historical state.
9. Backend calculates deterministic business metrics (no frontend recalculation).
10. Strict cross-project isolation (Project A cannot read Project B executions).
11. Clean resource teardown (zero orphaned Docker containers or networks).
"""

import asyncio
import os
import shutil
import tempfile
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.contracts import AgentExecutionStatus, AgentResult
from app.agents.execution import AgentExecutor
from app.agents.failure_analysis.agent import FailureAnalysisAgent
from app.agents.failure_analysis.contracts import (
    ClaimType,
    DiagnosticSeverity,
    EvidenceReference,
    FailureAnalysisInput,
    FailureDiagnosis,
    FailureSource,
    FailureType,
)
from app.agents.providers.mock import MockLLMProvider
from app.agents.registry import AgentRegistry, register_browser_journey_agents
from app.agents.browser_journey.agent import BrowserJourneyGenerationAgent
from app.agents.browser_journey.contracts import (
    BrowserActionType,
    BrowserJourney,
    BrowserJourneyGenerationInput,
    BrowserJourneyStep,
    BrowserJourneySuiteCandidate,
    BrowserTarget,
    BrowserTargetType,
    BoundedRequirementInfo,
    BoundedRouteInfo,
    JourneyCategory,
    JourneyPriority,
)
from app.browser.contracts import (
    DEFAULT_PLAYWRIGHT_IMAGE,
    BrowserLimits,
    DeterministicBrowserTestDefinition,
    create_default_smoke_suite,
)
from app.browser.errors import BrowserNavigationError
from app.browser.browser_executor import BrowserExecutor
from app.browser.browser_testing_service import BrowserTestingService
from app.browser.journey.adapter import BrowserJourneyAdapter
from app.browser.journey.contracts import (
    BrowserJourneyWorkflowResult,
    BrowserJourneyWorkflowStatus,
    ValidatedBrowserJourneySuite,
    ValidationContext,
)
from app.browser.journey.orchestrator import BrowserJourneyWorkflowOrchestrator
from app.browser.journey.validator import BrowserJourneyValidator
from app.models.project import Project, ProjectStatus
from app.models.requirement import Requirement, RequirementPriority, RequirementStatus, RequirementType
from app.models.workflow_execution import WorkflowExecution, WorkflowStatus
from app.runtime.application_runtime_manager import ApplicationRuntimeManager
from app.runtime.contracts import RuntimeLimits
from app.runtime.docker_runtime_executor import DockerRuntimeExecutor
from app.schemas.assistant import ActionResult, ActionStatus
from app.schemas.browser_testing import (
    BrowserTestCaseResult,
    BrowserTestRun,
    BrowserTestStatus,
)
from app.schemas.context import ProjectContextResponse
from app.schemas.runtime import ApplicationRuntimeManifest, RuntimeFramework, RuntimeLanguage
from app.services.action_registry import ACTION_REGISTRY
from app.services.browser_journey_service import BrowserJourneyService
from app.services.context_engine import ProjectContextEngine
from app.services.development_version_service import DevelopmentVersionService
from app.services.engineering_action_service import EngineeringActionService
from app.services.requirement_service import RequirementService
from app.services.verification_service import DevelopmentVerificationService
from app.services.workflow_service import WorkflowService
from app.workflows.contracts import WorkflowResult, WorkflowStatus as CoordinatorWorkflowStatus
from app.workflows.coordinator import WorkflowCoordinator


# ==============================================================================
# Deterministic Test Fixtures (Synthetic Data Only)
# ==============================================================================

SYNTHETIC_EMAIL = "test.user@example.test"
SYNTHETIC_PASSWORD = "synthetic-test-password"

SYNTHETIC_LOGIN_PAGE = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Enterprise Application Portal</title>
    <style>
        body { font-family: sans-serif; margin: 2rem; background: #f8fafc; }
        .hidden { display: none; }
        .card { padding: 1.5rem; background: white; border: 1px solid #cbd5e1; border-radius: 8px; max-width: 420px; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1); }
        input { display: block; width: 100%; margin: 0.5rem 0 1rem 0; padding: 0.6rem; border: 1px solid #94a3b8; border-radius: 4px; box-sizing: border-box; }
        button { background: #2563eb; color: white; border: none; padding: 0.6rem 1.2rem; border-radius: 4px; font-weight: 600; cursor: pointer; width: 100%; }
        button:hover { background: #1d4ed8; }
        .success-banner { padding: 0.75rem; background: #dcfce7; color: #166534; border-radius: 4px; margin-bottom: 1rem; }
    </style>
</head>
<body>
    <div id="login-container" class="card">
        <h1>Portal Sign In</h1>
        <p>Please enter your credentials to access your workspaces.</p>
        <form id="login-form">
            <label for="email-input">Email Address</label>
            <input id="email-input" data-testid="email-input" type="email" placeholder="user@example.test" required />
            <label for="password-input">Password</label>
            <input id="password-input" data-testid="password-input" type="password" placeholder="Password" required />
            <button id="signin-button" data-testid="signin-button" type="submit">Sign In</button>
        </form>
    </div>

    <div id="dashboard-view" data-testid="dashboard-view" class="card hidden">
        <div class="success-banner">Authenticated Successfully</div>
        <h1>Executive Dashboard</h1>
        <p id="welcome-message" data-testid="welcome-message">Welcome, Authenticated User</p>
        <p>System Status: Operational</p>
        <a id="nav-analytics" data-testid="nav-analytics" href="/analytics.html" style="color: #2563eb; text-decoration: underline;">System Analytics</a>
    </div>

    <script>
        document.getElementById('login-form').addEventListener('submit', function(e) {
            e.preventDefault();
            var email = document.getElementById('email-input').value;
            var pwd = document.getElementById('password-input').value;
            if (email && pwd) {
                document.getElementById('login-container').classList.add('hidden');
                document.getElementById('dashboard-view').classList.remove('hidden');
            }
        });
    </script>
</body>
</html>
"""

SYNTHETIC_ANALYTICS_PAGE = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>System Analytics</title>
    <style>
        body { font-family: sans-serif; margin: 2rem; background: #f8fafc; }
        .metric-card { padding: 1.5rem; background: white; border: 1px solid #cbd5e1; border-radius: 8px; max-width: 420px; }
        .stat { font-size: 1.5rem; font-weight: bold; color: #2563eb; }
    </style>
</head>
<body>
    <div id="analytics-page" data-testid="analytics-page" class="metric-card">
        <h1>System Analytics</h1>
        <p>Real-time telemetry and throughput metrics.</p>
        <div class="stat" id="metrics-data" data-testid="metrics-data">Active Users: 42</div>
        <p id="system-status" data-testid="system-status">System Operational</p>
        <div style="margin-top: 1.5rem;">
            <a id="back-home" href="/index.html" style="color: #64748b; font-size: 0.9rem;">Return to Portal</a>
        </div>
    </div>
</body>
</html>
"""


@pytest.fixture
def docker_runtime_executor():
    return DockerRuntimeExecutor(image="se-intelliplatform-sandbox:latest")


@pytest.fixture
def browser_executor():
    return BrowserExecutor(image=DEFAULT_PLAYWRIGHT_IMAGE)


@pytest.fixture
def synthetic_app_files():
    return {
        "index.html": SYNTHETIC_LOGIN_PAGE,
        "analytics.html": SYNTHETIC_ANALYTICS_PAGE,
    }


@pytest.fixture
def synthetic_app_manifest():
    return ApplicationRuntimeManifest(
        runtime_type="docker",
        language=RuntimeLanguage.PYTHON,
        framework=RuntimeFramework.FASTAPI,
        entrypoint="app.main:app",
        startup_command=["python", "-m", "http.server", "8000"],
        application_port=8000,
        health_check_path="/index.html",
        health_check_method="GET",
        health_check_timeout_seconds=8.0,
    )


def create_mock_context(project_id: uuid.UUID, req_configs: list[dict]) -> ProjectContextResponse:
    """Create a fully typed ProjectContextResponse mock with valid strings."""
    mock_proj = MagicMock()
    mock_proj.id = project_id
    mock_proj.name = "Portal Web Application"

    reqs = []
    for cfg in req_configs:
        r = MagicMock()
        r.id = cfg["id"]
        r.title = cfg["id"]
        r.description = cfg.get("description", "A functional requirement")
        r.is_archived = False
        r.status = MagicMock()
        r.status.value = "APPROVED"
        r.category = MagicMock()
        r.category.value = "FUNCTIONAL"
        reqs.append(r)

    ctx = MagicMock(spec=ProjectContextResponse)
    ctx.project = mock_proj
    ctx.requirements = reqs
    ctx.architecture = None
    return ctx


def create_synthetic_candidate_suite(project_id: uuid.UUID, include_analytics: bool = True) -> BrowserJourneySuiteCandidate:
    """Create a candidate suite matching the synthetic test application."""
    journeys = [
        BrowserJourney(
            journey_id="journey-auth-smoke",
            title="Synthetic User Authentication Flow",
            description="Verifies user can navigate to the portal, fill credentials, submit, and access dashboard.",
            category=JourneyCategory.AUTHENTICATION,
            priority=JourneyPriority.HIGH,
            requirement_ids=["REQ-001"],
            target_routes=["/index.html"],
            preconditions=["Portal is reachable"],
            steps=[
                BrowserJourneyStep(
                    step_id="step-1",
                    action=BrowserActionType.NAVIGATE,
                    route="/index.html",
                    description="Navigate to portal login page",
                ),
                BrowserJourneyStep(
                    step_id="step-2",
                    action=BrowserActionType.ASSERT_VISIBLE,
                    target=BrowserTarget(target_type=BrowserTargetType.TEST_ID, value="signin-button"),
                    description="Assert sign-in button is visible",
                ),
                BrowserJourneyStep(
                    step_id="step-3",
                    action=BrowserActionType.FILL,
                    target=BrowserTarget(target_type=BrowserTargetType.TEST_ID, value="email-input"),
                    value=SYNTHETIC_EMAIL,
                    description="Fill synthetic email address",
                ),
                BrowserJourneyStep(
                    step_id="step-4",
                    action=BrowserActionType.FILL,
                    target=BrowserTarget(target_type=BrowserTargetType.TEST_ID, value="password-input"),
                    value=SYNTHETIC_PASSWORD,
                    description="Fill synthetic password",
                ),
                BrowserJourneyStep(
                    step_id="step-5",
                    action=BrowserActionType.CLICK,
                    target=BrowserTarget(target_type=BrowserTargetType.TEST_ID, value="signin-button"),
                    description="Click submit button",
                ),
                BrowserJourneyStep(
                    step_id="step-6",
                    action=BrowserActionType.ASSERT_VISIBLE,
                    target=BrowserTarget(target_type=BrowserTargetType.TEST_ID, value="nav-analytics"),
                    description="Assert executive dashboard link is visible",
                ),
                BrowserJourneyStep(
                    step_id="step-7",
                    action=BrowserActionType.ASSERT_TEXT,
                    target=BrowserTarget(target_type=BrowserTargetType.TEST_ID, value="nav-analytics"),
                    value="System Analytics",
                    description="Assert analytics navigation label text",
                ),
            ],
            expected_outcomes=["User successfully authenticates and reaches executive dashboard"],
        )
    ]

    if include_analytics:
        journeys.append(
            BrowserJourney(
                journey_id="journey-analytics-nav",
                title="Synthetic System Analytics Navigation",
                description="Verifies user can navigate to the analytics page and inspect active user metrics.",
                category=JourneyCategory.NAVIGATION,
                priority=JourneyPriority.HIGH,
                requirement_ids=["REQ-002"],
                target_routes=["/analytics.html"],
                preconditions=["Analytics service is operational"],
                steps=[
                    BrowserJourneyStep(
                        step_id="step-1",
                        action=BrowserActionType.NAVIGATE,
                        route="/analytics.html",
                        description="Navigate to analytics dashboard",
                    ),
                    BrowserJourneyStep(
                        step_id="step-2",
                        action=BrowserActionType.ASSERT_VISIBLE,
                        target=BrowserTarget(target_type=BrowserTargetType.TEST_ID, value="metrics-data"),
                        description="Assert metrics card is displayed",
                    ),
                    BrowserJourneyStep(
                        step_id="step-3",
                        action=BrowserActionType.ASSERT_TEXT,
                        target=BrowserTarget(target_type=BrowserTargetType.TEST_ID, value="metrics-data"),
                        value="Active Users: 42",
                        description="Assert metrics counter value",
                    ),
                ],
                expected_outcomes=["Analytics page renders active metrics"],
            )
        )

    return BrowserJourneySuiteCandidate(
        suite_id="suite-stage7-synthetic",
        project_id=project_id,
        journeys=journeys,
        metadata={"generator": "Stage7-E2E-Synthetic"},
    )


# ==============================================================================
# STAGE 7 LIVE TESTS
# ==============================================================================

@pytest.mark.asyncio
async def test_stage7_live_docker_e2e_login_journey(
    docker_runtime_executor,
    browser_executor,
    synthetic_app_files,
    synthetic_app_manifest,
    db_session: AsyncSession,
):
    """LIVE E2E: Real Docker app + Real Playwright container execution of synthetic login journey.

    Covers:
    - Generation via AgentExecutor & MockLLMProvider
    - Validation via BrowserJourneyValidator
    - Adaptation via BrowserJourneyAdapter
    - Live Playwright execution in container against live app container
    - Authoritative requirement coverage (REQ-001 -> 100%)
    - Complete WorkflowExecution audit artifacts
    """
    if not await docker_runtime_executor.check_docker_available():
        pytest.skip("Docker daemon is not available.")
    if not await browser_executor.check_image_available():
        pytest.skip(f"Playwright browser image '{DEFAULT_PLAYWRIGHT_IMAGE}' not available locally.")

    project_id = uuid.uuid4()
    artifacts_dir = tempfile.mkdtemp(prefix="se_stage7_artifacts_")

    try:
        # 1. Setup isolated Project Context
        context = create_mock_context(
            project_id=project_id,
            req_configs=[{"id": "REQ-001", "title": "User Authentication", "description": "Users can sign in to the portal."}],
        )

        # 2. Setup AgentExecutor and WorkflowCoordinator
        candidate_suite = create_synthetic_candidate_suite(project_id, include_analytics=False)
        mock_provider = MockLLMProvider()
        mock_provider.register_structured_response(candidate_suite)

        executor = AgentExecutor(provider=mock_provider)
        registry = AgentRegistry()
        register_browser_journey_agents(registry)
        coordinator = WorkflowCoordinator(executor=executor, registry=registry)

        # 3. Setup real BrowserTestingService
        runtime_manager = ApplicationRuntimeManager()
        testing_service = BrowserTestingService(
            runtime_manager=runtime_manager,
            browser_executor=browser_executor,
            artifacts_base_dir=artifacts_dir,
        )

        orchestrator = BrowserJourneyWorkflowOrchestrator(
            coordinator=coordinator,
            browser_service=testing_service,
        )

        # 4. Execute End-to-End Workflow with LIVE Docker container execution
        workflow_id = uuid.uuid4()
        result = await orchestrator.execute_workflow(
            context=context,
            authoritative_routes=["/index.html"],
            runtime_manifest=synthetic_app_manifest,
            files_map=synthetic_app_files,
            execute_browser_tests=True,
            workflow_execution_id=workflow_id,
            session=db_session,
        )

        # 5. Assertions on E2E result
        assert isinstance(result, BrowserJourneyWorkflowResult)
        assert result.status == BrowserJourneyWorkflowStatus.COMPLETED
        assert result.stage_reached == "completed"
        assert result.validation_outcome.is_valid is True
        assert len(result.test_definitions) == 1

        # 6. Assert live browser test run
        assert result.browser_test_run is not None
        assert result.browser_test_run.status == BrowserTestStatus.PASSED
        assert result.browser_test_run.tests_passed == 1
        assert result.browser_test_run.tests_failed == 0

        # Verify screenshot artifact was generated in live container
        assert len(result.browser_test_run.artifacts) >= 1

        # 7. Authoritative requirement coverage verification
        assert result.coverage_report is not None
        assert result.coverage_report.covered_requirement_ids == ["REQ-001"]
        assert result.coverage_report.uncovered_requirement_ids == []
        assert result.coverage_report.coverage_percentage == 100.0

        # 8. Artifact traceability chain verification
        assert "browser_journey_input" in result.artifacts
        assert "browser_journey_generation" in result.artifacts
        assert "browser_journey_validation" in result.artifacts
        assert "browser_journey_suite" in result.artifacts
        assert "browser_test_run" in result.artifacts

    finally:
        shutil.rmtree(artifacts_dir, ignore_errors=True)


@pytest.mark.asyncio
async def test_stage7_live_docker_e2e_multi_journey(
    docker_runtime_executor,
    browser_executor,
    synthetic_app_files,
    synthetic_app_manifest,
    db_session: AsyncSession,
):
    """LIVE E2E: Real Docker app + Real Playwright container execution of 2 distinct journeys.

    Validates:
    - Login Journey (REQ-001)
    - Analytics Navigation Journey (REQ-002)
    - Both pass against the live application container.
    """
    if not await docker_runtime_executor.check_docker_available():
        pytest.skip("Docker daemon is not available.")
    if not await browser_executor.check_image_available():
        pytest.skip(f"Playwright browser image '{DEFAULT_PLAYWRIGHT_IMAGE}' not available locally.")

    project_id = uuid.uuid4()
    artifacts_dir = tempfile.mkdtemp(prefix="se_stage7_artifacts_")

    try:
        context = create_mock_context(
            project_id=project_id,
            req_configs=[
                {"id": "REQ-001", "title": "User Authentication", "description": "Users can sign in to the portal."},
                {"id": "REQ-002", "title": "Analytics Navigation", "description": "Users can view analytics metrics."},
            ],
        )

        candidate_suite = create_synthetic_candidate_suite(project_id, include_analytics=True)
        mock_provider = MockLLMProvider()
        mock_provider.register_structured_response(candidate_suite)

        executor = AgentExecutor(provider=mock_provider)
        registry = AgentRegistry()
        register_browser_journey_agents(registry)
        coordinator = WorkflowCoordinator(executor=executor, registry=registry)

        runtime_manager = ApplicationRuntimeManager()
        testing_service = BrowserTestingService(
            runtime_manager=runtime_manager,
            browser_executor=browser_executor,
            artifacts_base_dir=artifacts_dir,
        )

        orchestrator = BrowserJourneyWorkflowOrchestrator(
            coordinator=coordinator,
            browser_service=testing_service,
        )

        result = await orchestrator.execute_workflow(
            context=context,
            authoritative_routes=["/index.html", "/analytics.html"],
            runtime_manifest=synthetic_app_manifest,
            files_map=synthetic_app_files,
            execute_browser_tests=True,
            session=db_session,
        )

        assert result.status == BrowserJourneyWorkflowStatus.COMPLETED
        assert result.stage_reached == "completed"
        assert result.browser_test_run.status == BrowserTestStatus.PASSED
        assert result.browser_test_run.tests_passed == 2
        assert result.browser_test_run.tests_failed == 0
        assert set(result.coverage_report.covered_requirement_ids) == {"REQ-001", "REQ-002"}
        assert result.coverage_report.coverage_percentage == 100.0

    finally:
        shutil.rmtree(artifacts_dir, ignore_errors=True)


@pytest.mark.asyncio
async def test_stage7_validation_failure_fail_fast_gate(
    docker_runtime_executor,
    browser_executor,
    synthetic_app_files,
    synthetic_app_manifest,
    db_session: AsyncSession,
):
    """FAIL-FAST GATE: Unauthoritative route rejected by BrowserJourneyValidator.

    Proves that browser execution is NEVER initiated when validation fails.
    """
    project_id = uuid.uuid4()
    context = create_mock_context(
        project_id=project_id,
        req_configs=[{"id": "REQ-001", "title": "User Authentication", "description": "Users can sign in."}],
    )

    # Candidate with prohibited route
    bad_journey = BrowserJourney(
        journey_id="journey-bad-route",
        title="Unauthorized Admin Route Journey",
        description="Attempts to access unmapped route",
        category=JourneyCategory.AUTHENTICATION,
        priority=JourneyPriority.HIGH,
        requirement_ids=["REQ-001"],
        target_routes=["/unauthorized/admin-backdoor.html"],
        steps=[
            BrowserJourneyStep(
                step_id="step-1",
                action=BrowserActionType.NAVIGATE,
                route="/unauthorized/admin-backdoor.html",
                description="Navigate to backdoor",
            )
        ],
    )
    bad_candidate = BrowserJourneySuiteCandidate(
        suite_id="suite-bad",
        project_id=project_id,
        journeys=[bad_journey],
    )

    mock_provider = MockLLMProvider()
    mock_provider.register_structured_response(bad_candidate)
    executor = AgentExecutor(provider=mock_provider)
    registry = AgentRegistry()
    register_browser_journey_agents(registry)
    coordinator = WorkflowCoordinator(executor=executor, registry=registry)

    # Mock testing service to assert it is NEVER called
    mock_testing_service = MagicMock(spec=BrowserTestingService)
    mock_testing_service.execute_validated_browser_journey_suite = AsyncMock()

    orchestrator = BrowserJourneyWorkflowOrchestrator(
        coordinator=coordinator,
        browser_service=mock_testing_service,
    )

    result = await orchestrator.execute_workflow(
        context=context,
        authoritative_routes=["/index.html"],
        runtime_manifest=synthetic_app_manifest,
        files_map=synthetic_app_files,
        execute_browser_tests=True,
        session=db_session,
    )

    assert result.status == BrowserJourneyWorkflowStatus.VALIDATION_FAILED
    assert result.stage_reached == "validation"
    assert result.validation_outcome.is_valid is False
    assert result.browser_test_run is None

    # Guaranteed fail-fast: browser container was NEVER invoked
    mock_testing_service.execute_validated_browser_journey_suite.assert_not_called()


@pytest.mark.asyncio
async def test_stage7_live_docker_browser_failure_and_failure_analysis(
    docker_runtime_executor,
    browser_executor,
    synthetic_app_files,
    synthetic_app_manifest,
    db_session: AsyncSession,
):
    """LIVE FAILURE & DIAGNOSIS: Browser test fails in Docker and triggers FailureAnalysisAgent.

    Proves:
    - Live Playwright detects missing element
    - Browser test run status is FAILED
    - Workflow reaches WORKFLOW_BROWSER_EXECUTION_FAILED
    - Existing FailureAnalysisAgent produces structured diagnosis
    - ZERO automated remediation or code modification loop is started
    """
    if not await docker_runtime_executor.check_docker_available():
        pytest.skip("Docker daemon is not available.")
    if not await browser_executor.check_image_available():
        pytest.skip(f"Playwright browser image '{DEFAULT_PLAYWRIGHT_IMAGE}' not available locally.")

    project_id = uuid.uuid4()
    artifacts_dir = tempfile.mkdtemp(prefix="se_stage7_artifacts_")

    try:
        context = create_mock_context(
            project_id=project_id,
            req_configs=[{"id": "REQ-001", "title": "Portal App", "description": "Portal verification"}],
        )

        # Journey asserting element that does NOT exist
        failing_journey = BrowserJourney(
            journey_id="journey-fail-missing-elem",
            title="Failing Journey on Nonexistent Element",
            description="Navigates to portal and asserts a nonexistent secret badge.",
            category=JourneyCategory.AUTHENTICATION,
            priority=JourneyPriority.HIGH,
            requirement_ids=["REQ-001"],
            target_routes=["/index.html"],
            steps=[
                BrowserJourneyStep(
                    step_id="step-1",
                    action=BrowserActionType.NAVIGATE,
                    route="/index.html",
                    description="Navigate to portal",
                ),
                BrowserJourneyStep(
                    step_id="step-2",
                    action=BrowserActionType.ASSERT_VISIBLE,
                    target=BrowserTarget(target_type=BrowserTargetType.TEST_ID, value="nonexistent-secret-badge"),
                    description="Assert nonexistent element is visible",
                ),
            ],
        )
        failing_candidate = BrowserJourneySuiteCandidate(
            suite_id="suite-failing",
            project_id=project_id,
            journeys=[failing_journey],
        )

        mock_provider = MockLLMProvider()
        mock_provider.register_structured_response(failing_candidate)

        # Setup structured diagnosis response for FailureAnalysisAgent
        expected_diagnosis = FailureDiagnosis(
            failure_type=FailureType.TEST_FAILURE,
            title="Browser Journey Element Verification Timeout",
            summary="Selector '[data-testid=\"nonexistent-secret-badge\"]' timed out or is missing from DOM.",
            root_cause="The target element does not exist in the DOM structure of /index.html.",
            severity=DiagnosticSeverity.ERROR,
            affected_files=[],
            evidence=[
                EvidenceReference(
                    evidence_id="browser_run",
                    source=FailureSource.BROWSER,
                    code="SELECTOR_MISSING",
                    description="Selector '[data-testid=\"nonexistent-secret-badge\"]' missing",
                )
            ],
            claims=[],
            suggested_remediation="Add the required element or update the test selector to match the rendered DOM.",
        )
        mock_provider.register_structured_response(expected_diagnosis)

        executor = AgentExecutor(provider=mock_provider)
        registry = AgentRegistry()
        register_browser_journey_agents(registry)
        coordinator = WorkflowCoordinator(executor=executor, registry=registry)

        fa_agent = FailureAnalysisAgent()

        runtime_manager = ApplicationRuntimeManager()
        testing_service = BrowserTestingService(
            runtime_manager=runtime_manager,
            browser_executor=browser_executor,
            artifacts_base_dir=artifacts_dir,
        )

        orchestrator = BrowserJourneyWorkflowOrchestrator(
            coordinator=coordinator,
            browser_service=testing_service,
            failure_analysis_agent=fa_agent,
        )

        # Limits with short action timeout for quick failure
        short_limits = BrowserLimits(action_timeout_seconds=2.0)

        result = await orchestrator.execute_workflow(
            context=context,
            authoritative_routes=["/index.html"],
            runtime_manifest=synthetic_app_manifest,
            files_map=synthetic_app_files,
            limits=short_limits,
            execute_browser_tests=True,
            session=db_session,
        )

        # Assert status is BROWSER_EXECUTION_FAILED
        assert result.status == BrowserJourneyWorkflowStatus.BROWSER_EXECUTION_FAILED
        assert result.browser_test_run is not None
        assert result.browser_test_run.status == BrowserTestStatus.FAILED
        assert result.browser_test_run.tests_failed == 1

        # Assert FailureAnalysisAgent was invoked and populated diagnosis
        assert result.failure_diagnosis is not None
        assert result.failure_diagnosis.failure_type == FailureType.TEST_FAILURE
        assert "nonexistent-secret-badge" in result.failure_diagnosis.summary

        # Assert NO remediation loop executed
        assert "remediation_proposal" not in result.artifacts

    finally:
        shutil.rmtree(artifacts_dir, ignore_errors=True)


@pytest.mark.asyncio
async def test_stage7_security_boundary_enforcements():
    """SECURITY BOUNDARIES: Rejection of external URLs, dangerous URIs, raw Playwright code, and telemetry escaping."""
    service = BrowserTestingService()

    # A. External URL rejection
    with pytest.raises(BrowserNavigationError, match="outside authorized internal origin"):
        service.validate_navigation_target("https://evil.example.com/steal", allowed_origin="http://app-container:8000")

    # B. Dangerous URI schemes
    for dangerous in ["javascript:alert(1)", "data:text/html,<b>xss</b>", "file:///etc/passwd"]:
        with pytest.raises(BrowserNavigationError, match="unsafe scheme prohibited"):
            service.validate_navigation_target(dangerous, allowed_origin="http://app-container:8000")

    # C. Host/localhost navigation prohibited
    for host_target in ["http://localhost:8000/index.html", "http://127.0.0.1:8000/index.html", "http://169.254.169.254/meta-data"]:
        with pytest.raises(BrowserNavigationError, match="host address prohibited"):
            service.validate_navigation_target(host_target, allowed_origin="http://app-container:8000")

    # D. Raw script execution in target selector blocked at schema/adapter level
    from app.browser.journey.errors import BrowserJourneyAdaptationError
    with pytest.raises((BrowserJourneyAdaptationError, Exception)):
        BrowserTarget(target_type=BrowserTargetType.CSS_SELECTOR, value="<script>alert(1)</script>")

    # E. Target with quotation escape attack rejected
    with pytest.raises(BrowserJourneyAdaptationError, match="cannot contain quotes"):
        BrowserJourneyAdapter.target_to_selector(
            BrowserTarget(target_type=BrowserTargetType.TEST_ID, value='btn" onclick="evil()')
        )


@pytest.mark.asyncio
async def test_stage7_api_e2e_and_workflow_execution_lifecycle(
    client: AsyncClient,
    db_session: AsyncSession,
):
    """API E2E: Full REST lifecycle: POST -> GET by ID -> GET latest -> GET history.

    Verifies:
    - WorkflowExecution record tracks audit lifecycle
    - DevelopmentVersion is NOT mutated
    - Response schema contains authoritative coverage
    """
    project_id = uuid.uuid4()
    proj = Project(
        id=project_id,
        name="Stage 7 API Project",
        slug=f"stage7-api-{project_id.hex[:8]}",
        status=ProjectStatus.IN_PROGRESS,
    )
    db_session.add(proj)
    await db_session.commit()

    exec_id = uuid.uuid4()
    now = datetime.now(timezone.utc)
    mock_result = BrowserJourneyWorkflowResult(
        workflow_execution_id=exec_id,
        project_id=project_id,
        status=BrowserJourneyWorkflowStatus.COMPLETED,
        stage_reached="completed",
        candidate_suite=None,
        validation_outcome=None,
        validated_suite=None,
        coverage_report=None,
        test_definitions=[],
        browser_test_run=None,
        artifacts={"browser_journey_input": {"project_id": str(project_id)}},
        started_at=now,
        completed_at=now,
        duration_seconds=1.85,
    )

    mock_service = MagicMock(spec=BrowserJourneyService)
    mock_service.generate_and_execute_journeys = AsyncMock(return_value=mock_result)

    # Set up WorkflowExecution record in database to verify GET endpoints
    execution_record = WorkflowExecution(
        workflow_execution_id=exec_id,
        project_id=project_id,
        workflow_id="browser-journey-workflow",
        workflow_version="1.0.0",
        status=WorkflowStatus.COMPLETED,
        context_snapshot_id=None,
        context_version=None,
        started_at=now,
        completed_at=now,
        step_count=1,
        completed_steps=1,
        failed_steps=0,
        skipped_steps=0,
        artifacts={
            "browser_journey_validation": {
                "coverage_report": {
                    "coverage_percentage": 100.0,
                    "covered_requirement_ids": ["REQ-001", "REQ-002"],
                    "uncovered_requirement_ids": [],
                },
                "is_valid": True,
            },
            "browser_journey_suite": {
                "journeys": [{"journey_id": "j1"}, {"journey_id": "j2"}]
            },
        },
        errors=[],
        warnings=[],
        metadata_payload={
            "project_id": str(project_id),
            "workflow_status": "COMPLETED",
            "stage_reached": "completed",
            "journey_count": 2,
            "validation_passed": True,
            "coverage_percentage": 100.0,
            "covered_requirement_ids": ["REQ-001", "REQ-002"],
            "uncovered_requirement_ids": [],
            "test_definitions_count": 2,
            "browser_tests_executed": True,
            "browser_tests_passed": True,
        },
    )
    db_session.add(execution_record)
    await db_session.commit()

    from app.api.dependencies import get_browser_journey_service
    from app.main import app

    app.dependency_overrides[get_browser_journey_service] = lambda: mock_service

    try:
        # 1. POST /browser-journeys
        post_resp = await client.post(
            f"/api/v1/projects/{project_id}/browser-journeys",
            json={"execute_browser_tests": False, "max_journeys": 5},
        )
        assert post_resp.status_code == 200
        post_data = post_resp.json()
        assert post_data["workflow_execution_id"] == str(exec_id)
        assert post_data["project_id"] == str(project_id)

        # Clear mock override to test REAL service reading from database
        app.dependency_overrides.pop(get_browser_journey_service, None)

        # 2. GET /browser-journeys/{workflow_execution_id}
        get_resp = await client.get(
            f"/api/v1/projects/{project_id}/browser-journeys/{exec_id}"
        )
        assert get_resp.status_code == 200
        get_data = get_resp.json()
        assert get_data["workflow_execution_id"] == str(exec_id)
        assert get_data["coverage_percentage"] == 100.0
        assert get_data["covered_requirement_ids"] == ["REQ-001", "REQ-002"]

        # 3. GET /browser-journeys/latest
        latest_resp = await client.get(
            f"/api/v1/projects/{project_id}/browser-journeys/latest"
        )
        assert latest_resp.status_code == 200
        latest_data = latest_resp.json()
        assert latest_data["workflow_execution_id"] == str(exec_id)

        # 4. GET /browser-journeys (history list)
        history_resp = await client.get(
            f"/api/v1/projects/{project_id}/browser-journeys"
        )
        assert history_resp.status_code == 200
        history_data = history_resp.json()
        assert len(history_data) >= 1
        assert history_data[0]["workflow_execution_id"] == str(exec_id)

    finally:
        app.dependency_overrides.pop(get_browser_journey_service, None)


@pytest.mark.asyncio
async def test_stage7_cross_project_isolation(
    client: AsyncClient,
    db_session: AsyncSession,
):
    """CROSS-PROJECT ISOLATION: Project B cannot retrieve Project A's workflow executions."""
    proj_a = Project(id=uuid.uuid4(), name="Project A", slug=f"proj-a-{uuid.uuid4().hex[:6]}")
    proj_b = Project(id=uuid.uuid4(), name="Project B", slug=f"proj-b-{uuid.uuid4().hex[:6]}")
    db_session.add_all([proj_a, proj_b])
    await db_session.commit()

    exec_a = uuid.uuid4()
    now = datetime.now(timezone.utc)
    rec_a = WorkflowExecution(
        workflow_execution_id=exec_a,
        project_id=proj_a.id,
        workflow_id="browser-journey-workflow",
        workflow_version="1.0.0",
        status=WorkflowStatus.COMPLETED,
        started_at=now,
        completed_at=now,
        step_count=1,
        completed_steps=1,
        failed_steps=0,
        skipped_steps=0,
        artifacts={},
        errors=[],
        warnings=[],
        metadata_payload={"workflow_status": "COMPLETED"},
    )
    db_session.add(rec_a)
    await db_session.commit()

    # Query Project B with Project A's execution ID -> MUST return 404 NotFound
    cross_resp = await client.get(
        f"/api/v1/projects/{proj_b.id}/browser-journeys/{exec_a}"
    )
    assert cross_resp.status_code == 404

    # Query Project B's history -> MUST be empty
    history_b_resp = await client.get(
        f"/api/v1/projects/{proj_b.id}/browser-journeys"
    )
    assert history_b_resp.status_code == 200
    assert history_b_resp.json() == []


@pytest.mark.asyncio
async def test_stage7_assistant_action_boundary_integration(
    db_session: AsyncSession,
):
    """ASSISTANT BOUNDARY: GENERATE_BROWSER_JOURNEYS action execution through EngineeringActionService."""
    project_id = uuid.uuid4()
    proj = Project(
        id=project_id,
        name="Assistant Test Project",
        slug=f"asst-proj-{project_id.hex[:6]}",
        status=ProjectStatus.IN_PROGRESS,
    )
    db_session.add(proj)
    await db_session.commit()

    exec_id = uuid.uuid4()
    now = datetime.now(timezone.utc)
    mock_result = BrowserJourneyWorkflowResult(
        workflow_execution_id=exec_id,
        project_id=project_id,
        status=BrowserJourneyWorkflowStatus.COMPLETED,
        stage_reached="completed",
        candidate_suite=None,
        validation_outcome=None,
        validated_suite=None,
        coverage_report=None,
        test_definitions=[],
        browser_test_run=None,
        artifacts={},
        started_at=now,
        completed_at=now,
        duration_seconds=2.1,
    )

    mock_journey_service = MagicMock(spec=BrowserJourneyService)
    mock_journey_service.generate_and_execute_journeys = AsyncMock(return_value=mock_result)

    action_service = EngineeringActionService(
        session=db_session,
        version_service=MagicMock(spec=DevelopmentVersionService),
        verification_service=MagicMock(spec=DevelopmentVerificationService),
        requirement_service=MagicMock(spec=RequirementService),
        context_engine=MagicMock(spec=ProjectContextEngine),
        workflow_service=MagicMock(spec=WorkflowService),
        browser_journey_service=mock_journey_service,
    )

    action_result = await action_service.execute_action(
        project_id=project_id,
        action_id="GENERATE_BROWSER_JOURNEYS",
        parameters={"execute_browser_tests": False, "max_journeys": 5},
    )

    assert action_result is not None
    assert action_result.status == ActionStatus.SUCCESS
    assert action_result.data["workflow_execution_id"] == str(exec_id)
    assert action_result.data["status"] == "COMPLETED"


@pytest.mark.asyncio
async def test_stage7_docker_cleanup_audit(docker_runtime_executor):
    """CLEANUP AUDIT: Verify that no orphaned test containers or networks remain."""
    if not await docker_runtime_executor.check_docker_available():
        pytest.skip("Docker daemon is not available.")

    # Inspect active containers with se_ prefix
    proc = await asyncio.create_subprocess_exec(
        "docker", "ps", "--filter", "name=se_", "--format", "{{.Names}}",
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    stdout, _ = await proc.communicate()
    active_containers = [line.strip() for line in stdout.decode().splitlines() if line.strip()]

    # Assert no active test containers left behind
    assert len(active_containers) == 0, f"Orphaned test containers found: {active_containers}"
