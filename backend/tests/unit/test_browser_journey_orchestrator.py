"""Unit Tests for Phase 11K — Stage 4: Intelligent Browser Journey Generation Orchestrator.

Tests end-to-end pipeline coordination:
Authoritative Context -> Generation -> Validation -> Adaptation -> BrowserTestingService -> FailureAnalysis.
"""

import uuid
from datetime import datetime, timezone
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.agents.contracts import AgentExecutionStatus, AgentResult
from app.agents.exceptions import ProviderError
from app.agents.execution import AgentExecutor
from app.agents.failure_analysis.agent import FailureAnalysisAgent
from app.agents.failure_analysis.contracts import (
    DiagnosticSeverity,
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
    BoundedRouteInfo,
    JourneyCategory,
    JourneyPriority,
)
from app.browser.contracts import (
    BrowserLimits,
    DeterministicBrowserTestDefinition,
)
from app.browser.browser_testing_service import BrowserTestingService
from app.browser.journey.contracts import (
    BrowserJourneyWorkflowResult,
    BrowserJourneyWorkflowStatus,
    ValidatedBrowserJourney,
    ValidatedBrowserJourneySuite,
    ValidationContext,
)
from app.browser.journey.errors import BrowserJourneyAdaptationError
from app.browser.journey.orchestrator import BrowserJourneyWorkflowOrchestrator
from app.schemas.browser_testing import (
    BrowserTestCaseResult,
    BrowserTestRun,
    BrowserTestStatus,
)
from app.schemas.context import ProjectContextResponse
from app.schemas.runtime import ApplicationRuntimeManifest
from app.workflows.contracts import WorkflowResult, WorkflowStatus
from app.workflows.coordinator import WorkflowCoordinator


# ==============================================================================
# Fixtures
# ==============================================================================

@pytest.fixture
def sample_project_id() -> uuid.UUID:
    return uuid.uuid4()


@pytest.fixture
def mock_project_context(sample_project_id: uuid.UUID) -> ProjectContextResponse:
    mock_proj = MagicMock()
    mock_proj.id = sample_project_id
    mock_proj.name = "Test Web Application"

    mock_req1 = MagicMock()
    mock_req1.id = "REQ-001"
    mock_req1.title = "User Login"
    mock_req1.description = "Users can log into the system with credentials."
    mock_req1.is_archived = False
    mock_req1.status = MagicMock()
    mock_req1.status.value = "APPROVED"
    mock_req1.category = MagicMock()
    mock_req1.category.value = "FUNCTIONAL"

    mock_req2 = MagicMock()
    mock_req2.id = "REQ-002"
    mock_req2.title = "Dashboard View"
    mock_req2.description = "Users can view the metrics dashboard."
    mock_req2.is_archived = False
    mock_req2.status = MagicMock()
    mock_req2.status.value = "IMPLEMENTED"
    mock_req2.category = MagicMock()
    mock_req2.category.value = "FUNCTIONAL"

    ctx = MagicMock(spec=ProjectContextResponse)
    ctx.project = mock_proj
    ctx.requirements = [mock_req1, mock_req2]
    ctx.architecture = None
    return ctx


@pytest.fixture
def sample_candidate_suite(sample_project_id: uuid.UUID) -> BrowserJourneySuiteCandidate:
    return BrowserJourneySuiteCandidate(
        project_id=sample_project_id,
        suite_name="Auth and Dashboard Journeys",
        summary="User authentication and dashboard verification flows",
        journeys=[
            BrowserJourney(
                journey_id="BJ-001",
                title="User Login Flow",
                description="Navigate to login and submit valid credentials",
                category=JourneyCategory.AUTHENTICATION,
                priority=JourneyPriority.HIGH,
                requirement_ids=["REQ-001"],
                target_routes=["/login"],
                steps=[
                    BrowserJourneyStep(
                        step_id="S01",
                        action=BrowserActionType.NAVIGATE,
                        route="/login",
                        description="Navigate to login page",
                    ),
                    BrowserJourneyStep(
                        step_id="S02",
                        action=BrowserActionType.FILL,
                        target=BrowserTarget(
                            target_type=BrowserTargetType.TEST_ID,
                            value="email-input",
                        ),
                        value="test@example.com",
                        description="Enter email",
                    ),
                    BrowserJourneyStep(
                        step_id="S03",
                        action=BrowserActionType.CLICK,
                        target=BrowserTarget(
                            target_type=BrowserTargetType.TEST_ID,
                            value="login-submit",
                        ),
                        description="Submit credentials",
                    ),
                    BrowserJourneyStep(
                        step_id="S04",
                        action=BrowserActionType.ASSERT_VISIBLE,
                        target=BrowserTarget(
                            target_type=BrowserTargetType.TEST_ID,
                            value="dashboard-header",
                        ),
                        description="Assert dashboard header is visible",
                    ),
                ],
                expected_outcomes=["User successfully authenticated"],
            )
        ],
    )


@pytest.fixture
def mock_registry() -> AgentRegistry:
    reg = AgentRegistry()
    register_browser_journey_agents(reg)
    return reg


@pytest.fixture
def successful_browser_test_run(sample_project_id: uuid.UUID) -> BrowserTestRun:
    return BrowserTestRun(
        run_id=uuid.uuid4(),
        project_id=sample_project_id,
        status=BrowserTestStatus.PASSED,
        summary="All browser test cases passed successfully.",
        test_cases=[
            BrowserTestCaseResult(
                test_id="journey_BJ-001",
                name="User Login Flow",
                status=BrowserTestStatus.PASSED,
                duration_seconds=1.2,
                metadata={
                    "journey_id": "BJ-001",
                    "requirement_ids": ["REQ-001"],
                },
            )
        ],
    )


# ==============================================================================
# A. End-to-End Orchestration Tests
# ==============================================================================

class TestEndToEndOrchestration:
    """Verifies complete workflow orchestration across generation, validation, adaptation, and execution."""

    @pytest.mark.asyncio
    async def test_successful_end_to_end_orchestration(
        self,
        mock_project_context: ProjectContextResponse,
        sample_candidate_suite: BrowserJourneySuiteCandidate,
        mock_registry: AgentRegistry,
        successful_browser_test_run: BrowserTestRun,
    ):
        mock_provider = MockLLMProvider()
        mock_provider.register_structured_response(sample_candidate_suite)
        executor = AgentExecutor(provider=mock_provider)
        coordinator = WorkflowCoordinator(executor=executor, registry=mock_registry)

        mock_browser_service = MagicMock(spec=BrowserTestingService)
        mock_browser_service.execute_validated_browser_journey_suite = AsyncMock(
            return_value=successful_browser_test_run
        )

        orchestrator = BrowserJourneyWorkflowOrchestrator(
            coordinator=coordinator,
            browser_service=mock_browser_service,
        )

        result = await orchestrator.execute_workflow(
            context=mock_project_context,
            authoritative_routes=["/login", "/dashboard"],
        )

        assert isinstance(result, BrowserJourneyWorkflowResult)
        assert result.status == BrowserJourneyWorkflowStatus.COMPLETED
        assert result.stage_reached == "completed"
        assert result.candidate_suite is not None
        assert result.validated_suite is not None
        assert result.validation_outcome is not None
        assert result.validation_outcome.is_valid is True
        assert result.coverage_report is not None
        assert result.test_definitions is not None
        assert len(result.test_definitions) == 1
        assert result.browser_test_run == successful_browser_test_run
        assert result.failure_diagnosis is None

        # Artifacts verification
        assert "browser_journey_input" in result.artifacts
        assert "browser_journey_generation" in result.artifacts
        assert "browser_journey_validation" in result.artifacts
        assert "browser_journey_suite" in result.artifacts
        assert "browser_test_run" in result.artifacts

        # Verification of BrowserTestingService delegation
        mock_browser_service.execute_validated_browser_journey_suite.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_generate_and_validate_only_mode(
        self,
        mock_project_context: ProjectContextResponse,
        sample_candidate_suite: BrowserJourneySuiteCandidate,
        mock_registry: AgentRegistry,
    ):
        mock_provider = MockLLMProvider()
        mock_provider.register_structured_response(sample_candidate_suite)
        executor = AgentExecutor(provider=mock_provider)
        coordinator = WorkflowCoordinator(executor=executor, registry=mock_registry)

        mock_browser_service = MagicMock(spec=BrowserTestingService)
        mock_browser_service.execute_validated_browser_journey_suite = AsyncMock()

        orchestrator = BrowserJourneyWorkflowOrchestrator(
            coordinator=coordinator,
            browser_service=mock_browser_service,
        )

        result = await orchestrator.execute_workflow(
            context=mock_project_context,
            authoritative_routes=["/login", "/dashboard"],
            execute_browser_tests=False,
        )

        assert result.status == BrowserJourneyWorkflowStatus.COMPLETED
        assert result.stage_reached == "adaptation"
        assert result.validated_suite is not None
        assert result.test_definitions is not None
        assert result.browser_test_run is None
        mock_browser_service.execute_validated_browser_journey_suite.assert_not_called()


# ==============================================================================
# B. Failure Boundaries Tests
# ==============================================================================

class TestFailureBoundaries:
    """Verifies that failures at each stage stop execution deterministically."""

    @pytest.mark.asyncio
    async def test_generation_failure_blocks_downstream_stages(
        self,
        mock_project_context: ProjectContextResponse,
        mock_registry: AgentRegistry,
    ):
        mock_provider = MockLLMProvider()
        mock_provider.permanent_error = ProviderError("Simulated LLM network failure")
        executor = AgentExecutor(provider=mock_provider)
        coordinator = WorkflowCoordinator(executor=executor, registry=mock_registry)

        mock_browser_service = MagicMock(spec=BrowserTestingService)
        mock_browser_service.execute_validated_browser_journey_suite = AsyncMock()

        orchestrator = BrowserJourneyWorkflowOrchestrator(
            coordinator=coordinator,
            browser_service=mock_browser_service,
        )

        result = await orchestrator.execute_workflow(
            context=mock_project_context,
            authoritative_routes=["/login"],
        )

        assert result.status == BrowserJourneyWorkflowStatus.GENERATION_FAILED
        assert result.stage_reached == "generation"
        assert result.candidate_suite is None
        assert result.validated_suite is None
        assert result.test_definitions is None
        assert result.browser_test_run is None
        mock_browser_service.execute_validated_browser_journey_suite.assert_not_called()

    @pytest.mark.asyncio
    async def test_validation_failure_blocks_adaptation_and_execution(
        self,
        mock_project_context: ProjectContextResponse,
        mock_registry: AgentRegistry,
        sample_project_id: uuid.UUID,
    ):
        # Candidate references unknown hallucinated route '/non-existent-admin'
        invalid_candidate = BrowserJourneySuiteCandidate(
            project_id=sample_project_id,
            suite_name="Invalid Candidate",
            summary="Candidate with invalid route",
            journeys=[
                BrowserJourney(
                    journey_id="BJ-INVALID",
                    title="Invalid Flow",
                    description="Accessing unapproved route",
                    category=JourneyCategory.NAVIGATION,
                    requirement_ids=["REQ-001"],
                    steps=[
                        BrowserJourneyStep(
                            step_id="S01",
                            action=BrowserActionType.NAVIGATE,
                            route="/non-existent-admin",
                            description="Navigating to unapproved route",
                        )
                    ],
                )
            ],
        )

        mock_provider = MockLLMProvider()
        mock_provider.register_structured_response(invalid_candidate)
        executor = AgentExecutor(provider=mock_provider)
        coordinator = WorkflowCoordinator(executor=executor, registry=mock_registry)

        mock_browser_service = MagicMock(spec=BrowserTestingService)
        mock_browser_service.execute_validated_browser_journey_suite = AsyncMock()

        orchestrator = BrowserJourneyWorkflowOrchestrator(
            coordinator=coordinator,
            browser_service=mock_browser_service,
        )

        result = await orchestrator.execute_workflow(
            context=mock_project_context,
            authoritative_routes=["/login", "/dashboard"],  # '/non-existent-admin' NOT allowed
        )

        assert result.status == BrowserJourneyWorkflowStatus.VALIDATION_FAILED
        assert result.stage_reached == "validation"
        assert result.candidate_suite is not None
        assert result.validated_suite is None
        assert result.test_definitions is None
        assert result.browser_test_run is None
        assert result.validation_outcome is not None
        assert result.validation_outcome.is_valid is False
        mock_browser_service.execute_validated_browser_journey_suite.assert_not_called()

    @pytest.mark.asyncio
    async def test_adaptation_failure_blocks_execution(
        self,
        mock_project_context: ProjectContextResponse,
        sample_candidate_suite: BrowserJourneySuiteCandidate,
        mock_registry: AgentRegistry,
    ):
        mock_provider = MockLLMProvider()
        mock_provider.register_structured_response(sample_candidate_suite)
        executor = AgentExecutor(provider=mock_provider)
        coordinator = WorkflowCoordinator(executor=executor, registry=mock_registry)

        mock_browser_service = MagicMock(spec=BrowserTestingService)
        mock_browser_service.execute_validated_browser_journey_suite = AsyncMock()

        orchestrator = BrowserJourneyWorkflowOrchestrator(
            coordinator=coordinator,
            browser_service=mock_browser_service,
        )

        with patch("app.browser.journey.adapter.BrowserJourneyAdapter.adapt", side_effect=BrowserJourneyAdaptationError("Mock adaptation error")):
            result = await orchestrator.execute_workflow(
                context=mock_project_context,
                authoritative_routes=["/login", "/dashboard"],
            )

        assert result.status == BrowserJourneyWorkflowStatus.ADAPTATION_FAILED
        assert result.stage_reached == "adaptation"
        assert result.validated_suite is not None
        assert result.test_definitions is None
        assert result.browser_test_run is None
        mock_browser_service.execute_validated_browser_journey_suite.assert_not_called()

    @pytest.mark.asyncio
    async def test_browser_execution_failure_triggers_failure_analysis(
        self,
        mock_project_context: ProjectContextResponse,
        sample_candidate_suite: BrowserJourneySuiteCandidate,
        mock_registry: AgentRegistry,
        sample_project_id: uuid.UUID,
    ):
        mock_provider = MockLLMProvider()
        mock_provider.register_structured_response(sample_candidate_suite)
        executor = AgentExecutor(provider=mock_provider)
        coordinator = WorkflowCoordinator(executor=executor, registry=mock_registry)

        failed_browser_run = BrowserTestRun(
            run_id=uuid.uuid4(),
            project_id=sample_project_id,
            status=BrowserTestStatus.FAILED,
            failure_reason="Element '[data-testid=\"dashboard-header\"]' timed out after 5.0s",
            summary="1 of 1 test cases failed.",
            tests_failed=1,
            test_cases=[
                BrowserTestCaseResult(
                    test_id="journey_BJ-001",
                    name="User Login Flow",
                    status=BrowserTestStatus.FAILED,
                    failed_step="ASSERT_VISIBLE on dashboard-header timed out",
                    metadata={"journey_id": "BJ-001", "requirement_ids": ["REQ-001"]},
                )
            ],
        )

        mock_browser_service = MagicMock(spec=BrowserTestingService)
        mock_browser_service.execute_validated_browser_journey_suite = AsyncMock(
            return_value=failed_browser_run
        )

        mock_fa_agent = MagicMock(spec=FailureAnalysisAgent)
        mock_fa_diagnosis = FailureDiagnosis(
            diagnosis_id=uuid.uuid4(),
            failure_source=FailureSource.BROWSER,
            failure_type=FailureType.ASSERTION_FAILURE,
            title="Dashboard Header Element Missing",
            summary="Browser assertion failed because header element was not rendered.",
            root_cause="Dashboard view rendered without data-testid='dashboard-header'",
            severity=DiagnosticSeverity.ERROR,
            suggested_remediation="Verify dashboard view template renders the required test ID.",
        )

        with patch.object(executor, "execute", wraps=executor.execute) as mock_exec:
            # When FA agent is called, return mock diagnosis
            async def patched_execute(*args, **kwargs):
                if kwargs.get("agent") == mock_fa_agent or (len(args) > 0 and args[0] == mock_fa_agent):
                    return AgentResult(
                        execution_id=uuid.uuid4(),
                        agent_id="failure-analysis",
                        agent_version="1.0.0",
                        status=AgentExecutionStatus.COMPLETED,
                        output=mock_fa_diagnosis,
                        started_at=datetime.now(timezone.utc),
                    )
                return await mock_exec(*args, **kwargs)

            executor.execute = AsyncMock(side_effect=patched_execute)

            orchestrator = BrowserJourneyWorkflowOrchestrator(
                coordinator=coordinator,
                browser_service=mock_browser_service,
                failure_analysis_agent=mock_fa_agent,
            )

            result = await orchestrator.execute_workflow(
                context=mock_project_context,
                authoritative_routes=["/login", "/dashboard"],
            )

        assert result.status == BrowserJourneyWorkflowStatus.BROWSER_EXECUTION_FAILED
        assert result.stage_reached == "browser_execution"
        assert result.candidate_suite is not None
        assert result.validated_suite is not None
        assert result.test_definitions is not None
        assert result.browser_test_run == failed_browser_run
        assert result.failure_diagnosis == mock_fa_diagnosis
        assert "failure_analysis" in result.artifacts


# ==============================================================================
# C. Traceability & Coverage Preservation Tests
# ==============================================================================

class TestTraceabilityAndCoverage:
    """Verifies end-to-end requirement traceability and Stage 2 coverage report preservation."""

    @pytest.mark.asyncio
    async def test_traceability_chain_preserved(
        self,
        mock_project_context: ProjectContextResponse,
        sample_candidate_suite: BrowserJourneySuiteCandidate,
        mock_registry: AgentRegistry,
        successful_browser_test_run: BrowserTestRun,
    ):
        mock_provider = MockLLMProvider()
        mock_provider.register_structured_response(sample_candidate_suite)
        executor = AgentExecutor(provider=mock_provider)
        coordinator = WorkflowCoordinator(executor=executor, registry=mock_registry)

        mock_browser_service = MagicMock(spec=BrowserTestingService)
        mock_browser_service.execute_validated_browser_journey_suite = AsyncMock(
            return_value=successful_browser_test_run
        )

        orchestrator = BrowserJourneyWorkflowOrchestrator(
            coordinator=coordinator,
            browser_service=mock_browser_service,
        )

        result = await orchestrator.execute_workflow(
            context=mock_project_context,
            authoritative_routes=["/login", "/dashboard"],
        )

        # 1. Requirement in generation input
        assert any(r.id == "REQ-001" for r in result.generation_input.requirements)

        # 2. Requirement in candidate journey
        assert result.candidate_suite.journeys[0].requirement_ids == ["REQ-001"]

        # 3. Requirement in validated journey
        assert result.validated_suite.journeys[0].validated_requirement_ids == ["REQ-001"]

        # 4. Requirement in deterministic test definition metadata
        assert result.test_definitions[0].metadata["requirement_ids"] == ["REQ-001"]
        assert result.test_definitions[0].metadata["journey_id"] == "BJ-001"

        # 5. Requirement and journey in browser test run result metadata
        assert result.browser_test_run.test_cases[0].metadata["journey_id"] == "BJ-001"
        assert result.browser_test_run.test_cases[0].metadata["requirement_ids"] == ["REQ-001"]

    @pytest.mark.asyncio
    async def test_coverage_report_preserved_without_recalculation(
        self,
        mock_project_context: ProjectContextResponse,
        sample_candidate_suite: BrowserJourneySuiteCandidate,
        mock_registry: AgentRegistry,
        successful_browser_test_run: BrowserTestRun,
    ):
        mock_provider = MockLLMProvider()
        mock_provider.register_structured_response(sample_candidate_suite)
        executor = AgentExecutor(provider=mock_provider)
        coordinator = WorkflowCoordinator(executor=executor, registry=mock_registry)

        mock_browser_service = MagicMock(spec=BrowserTestingService)
        mock_browser_service.execute_validated_browser_journey_suite = AsyncMock(
            return_value=successful_browser_test_run
        )

        orchestrator = BrowserJourneyWorkflowOrchestrator(
            coordinator=coordinator,
            browser_service=mock_browser_service,
        )

        result = await orchestrator.execute_workflow(
            context=mock_project_context,
            authoritative_routes=["/login", "/dashboard"],
        )

        # Stage 4 coverage report must be identical to validated suite's report
        assert result.coverage_report == result.validated_suite.coverage_report
        assert result.coverage_report.covered_requirement_ids == ["REQ-001"]


# ==============================================================================
# D. Authority Boundaries & Security Tests
# ==============================================================================

class TestAuthorityBoundariesAndSecurity:
    """Verifies that AgentExecutor and WorkflowCoordinator boundaries are strictly enforced."""

    @pytest.mark.asyncio
    async def test_agent_executor_and_workflow_coordinator_enforced(
        self,
        mock_project_context: ProjectContextResponse,
        sample_candidate_suite: BrowserJourneySuiteCandidate,
        mock_registry: AgentRegistry,
        successful_browser_test_run: BrowserTestRun,
    ):
        mock_provider = MockLLMProvider()
        mock_provider.register_structured_response(sample_candidate_suite)
        executor = AgentExecutor(provider=mock_provider)

        coordinator = WorkflowCoordinator(executor=executor, registry=mock_registry)

        with patch.object(coordinator, "execute", wraps=coordinator.execute) as mock_coord_exec, \
             patch.object(executor, "execute", wraps=executor.execute) as mock_agent_exec:

            mock_browser_service = MagicMock(spec=BrowserTestingService)
            mock_browser_service.execute_validated_browser_journey_suite = AsyncMock(
                return_value=successful_browser_test_run
            )

            orchestrator = BrowserJourneyWorkflowOrchestrator(
                coordinator=coordinator,
                browser_service=mock_browser_service,
            )

            result = await orchestrator.execute_workflow(
                context=mock_project_context,
                authoritative_routes=["/login", "/dashboard"],
            )

            # Proves multi-stage coordination executed through WorkflowCoordinator
            mock_coord_exec.assert_awaited_once()

            # Proves BrowserJourneyGenerationAgent executed through AgentExecutor
            mock_agent_exec.assert_awaited()
            executed_agent_ids = [
                call.kwargs["agent"].metadata.agent_id
                for call in mock_agent_exec.call_args_list
            ]
            assert "browser-journey-generation" in executed_agent_ids

    def test_build_generation_input_sanitizes_files_and_manifests(
        self,
        mock_project_context: ProjectContextResponse,
    ):
        raw_files = [
            "src/App.tsx",
            ".env",
            "config/secrets.json",
            "backend/passwords.txt",
            "../../etc/passwd",
            "dist/bundle.js",
            "image.png",
        ]

        inp = BrowserJourneyWorkflowOrchestrator.build_generation_input(
            context=mock_project_context,
            file_manifest=raw_files,
            authoritative_routes=["/home"],
        )

        # Sensitive files must be excluded
        assert "src/App.tsx" in inp.file_manifest
        assert "dist/bundle.js" in inp.file_manifest
        assert ".env" not in inp.file_manifest
        assert "config/secrets.json" not in inp.file_manifest
        assert "backend/passwords.txt" not in inp.file_manifest
        assert "../../etc/passwd" not in inp.file_manifest
        assert "image.png" not in inp.file_manifest

    @pytest.mark.asyncio
    async def test_project_isolation_enforced(
        self,
        mock_project_context: ProjectContextResponse,
        mock_registry: AgentRegistry,
        sample_project_id: uuid.UUID,
    ):
        # Candidate attempts to test requirement belonging to a foreign project
        foreign_candidate = BrowserJourneySuiteCandidate(
            project_id=sample_project_id,
            suite_name="Foreign Req Journey",
            summary="Candidate referencing foreign requirement",
            journeys=[
                BrowserJourney(
                    journey_id="BJ-FOREIGN",
                    title="Foreign Req Flow",
                    description="Testing foreign requirement",
                    category=JourneyCategory.NAVIGATION,
                    requirement_ids=["FOREIGN-REQ-999"],
                    steps=[
                        BrowserJourneyStep(
                            step_id="S01",
                            action=BrowserActionType.NAVIGATE,
                            route="/login",
                            description="Nav",
                        )
                    ],
                )
            ],
        )

        mock_provider = MockLLMProvider()
        mock_provider.register_structured_response(foreign_candidate)
        executor = AgentExecutor(provider=mock_provider)
        coordinator = WorkflowCoordinator(executor=executor, registry=mock_registry)

        mock_browser_service = MagicMock(spec=BrowserTestingService)
        mock_browser_service.execute_validated_browser_journey_suite = AsyncMock()

        orchestrator = BrowserJourneyWorkflowOrchestrator(
            coordinator=coordinator,
            browser_service=mock_browser_service,
        )

        result = await orchestrator.execute_workflow(
            context=mock_project_context,
            authoritative_routes=["/login"],
        )

        # Validation gate MUST block execution
        assert result.status == BrowserJourneyWorkflowStatus.VALIDATION_FAILED
        mock_browser_service.execute_validated_browser_journey_suite.assert_not_called()

    @pytest.mark.asyncio
    async def test_no_direct_llm_provider_calls(
        self,
        mock_project_context: ProjectContextResponse,
        sample_candidate_suite: BrowserJourneySuiteCandidate,
        mock_registry: AgentRegistry,
        successful_browser_test_run: BrowserTestRun,
    ):
        mock_provider = MockLLMProvider()
        mock_provider.register_structured_response(sample_candidate_suite)
        executor = AgentExecutor(provider=mock_provider)
        coordinator = WorkflowCoordinator(executor=executor, registry=mock_registry)

        mock_browser_service = MagicMock(spec=BrowserTestingService)
        mock_browser_service.execute_validated_browser_journey_suite = AsyncMock(
            return_value=successful_browser_test_run
        )

        orchestrator = BrowserJourneyWorkflowOrchestrator(
            coordinator=coordinator,
            browser_service=mock_browser_service,
        )

        with patch.object(mock_provider, "generate_structured", wraps=mock_provider.generate_structured) as mock_gen:
            await orchestrator.execute_workflow(
                context=mock_project_context,
                authoritative_routes=["/login", "/dashboard"],
            )
            # Provider.generate_structured is called via AgentExecutor during workflow execution,
            # never directly by the orchestrator module itself.
            mock_gen.assert_called_once()

    def test_no_direct_playwright_or_docker_in_orchestrator(self):
        import inspect
        import app.browser.journey.orchestrator as orch_mod

        src = inspect.getsource(orch_mod)
        # Verify no direct Playwright or Docker imports or invocations
        assert "import playwright" not in src.lower()
        assert "from playwright" not in src.lower()
        assert "import docker" not in src.lower()
        assert "from docker" not in src.lower()
        assert "subprocess" not in src
        assert "os.system" not in src
        assert "exec(" not in src
        assert "eval(" not in src

