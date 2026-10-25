"""Unit Tests for BrowserJourneyGenerationAgent & AgentExecutor Integration.

Phase 11K — Stage 1: BrowserJourneyGenerationAgent Tests
Verifies agent identity, lifecycle hooks, Mock provider integration, AgentExecutor governance,
deterministic candidate validation, registration, and candidate vs authoritative boundaries.
"""

import uuid
import pytest
from unittest.mock import MagicMock

from app.agents.contracts import AgentExecutionStatus, AgentType
from app.agents.execution import AgentExecutor
from app.agents.providers.mock import MockLLMProvider
from app.agents.registry import agent_registry, register_browser_journey_agents, register_default_agents
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
from app.schemas.context import ProjectContextResponse


# ==============================================================================
# Fixtures
# ==============================================================================

@pytest.fixture
def mock_project_context() -> ProjectContextResponse:
    project_id = uuid.uuid4()
    req1_id = uuid.uuid4()
    req2_id = uuid.uuid4()

    mock_proj = MagicMock()
    mock_proj.id = project_id
    mock_proj.name = "E-Commerce Web App"

    mock_req1 = MagicMock()
    mock_req1.id = req1_id
    mock_req1.title = "User Authentication"
    mock_req1.description = "Users can sign in with email and password"
    mock_req1.category = MagicMock()
    mock_req1.category.value = "FUNCTIONAL"

    mock_req2 = MagicMock()
    mock_req2.id = req2_id
    mock_req2.title = "Shopping Cart"
    mock_req2.description = "Users can add items to cart"
    mock_req2.category = MagicMock()
    mock_req2.category.value = "FUNCTIONAL"

    context = MagicMock(spec=ProjectContextResponse)
    context.project = mock_proj
    context.requirements = [mock_req1, mock_req2]
    context.architecture = None
    context.database = None
    return context


@pytest.fixture
def sample_candidate_suite() -> BrowserJourneySuiteCandidate:
    step1 = BrowserJourneyStep(
        step_id="step-1",
        action=BrowserActionType.NAVIGATE,
        route="/login",
        description="Navigate to the login page",
    )
    step2 = BrowserJourneyStep(
        step_id="step-2",
        action=BrowserActionType.FILL,
        target=BrowserTarget(target_type=BrowserTargetType.TEST_ID, value="email-field"),
        value="test@example.com",
        description="Fill email input",
    )
    step3 = BrowserJourneyStep(
        step_id="step-3",
        action=BrowserActionType.CLICK,
        target=BrowserTarget(target_type=BrowserTargetType.TEST_ID, value="submit-button"),
        description="Click login submit button",
    )
    step4 = BrowserJourneyStep(
        step_id="step-4",
        action=BrowserActionType.ASSERT_URL,
        route="/dashboard",
        description="Assert user is redirected to dashboard",
    )
    journey = BrowserJourney(
        journey_id="BJ-001",
        title="Sign In Journey",
        description="Validates that a registered user can sign in.",
        category=JourneyCategory.AUTHENTICATION,
        priority=JourneyPriority.HIGH,
        requirement_ids=["REQ-AUTH-01"],
        target_routes=["/login", "/dashboard"],
        steps=[step1, step2, step3, step4],
        expected_outcomes=["Dashboard is displayed"],
    )
    return BrowserJourneySuiteCandidate(
        suite_name="Auth and Checkout Suite",
        summary="User journeys covering sign in and cart interactions.",
        journeys=[journey],
    )


# ==============================================================================
# 1. Agent Identity & Registration Tests
# ==============================================================================

def test_browser_journey_agent_identity():
    agent = BrowserJourneyGenerationAgent()
    meta = agent.metadata

    assert meta.agent_id == "browser-journey-generation"
    assert meta.version == "1.0.0"
    assert meta.agent_type == AgentType.GENERATION
    assert "Browser Journey" in meta.name
    assert agent.output_schema == BrowserJourneySuiteCandidate


def test_agent_registration_idempotency():
    register_browser_journey_agents()
    assert agent_registry.has("browser-journey-generation")

    # Second registration should not raise ConflictError
    register_browser_journey_agents()
    assert agent_registry.has("browser-journey-generation")

    registered = agent_registry.get("browser-journey-generation")
    assert isinstance(registered, BrowserJourneyGenerationAgent)


def test_register_browser_journey_agents_isolated_registry():
    from app.agents.registry import AgentRegistry
    isolated_reg = AgentRegistry()
    register_browser_journey_agents(isolated_reg)
    assert isolated_reg.has("browser-journey-generation")
    assert isolated_reg.get("browser-journey-generation").metadata.agent_id == "browser-journey-generation"


# ==============================================================================
# 2. Lifecycle Hooks Tests
# ==============================================================================

@pytest.mark.asyncio
async def test_agent_analyze_hook_with_explicit_input(mock_project_context: ProjectContextResponse):
    agent = BrowserJourneyGenerationAgent()
    await agent.initialize()

    explicit_input = BrowserJourneyGenerationInput(
        project_id=mock_project_context.project.id,
        project_name="Explicit App",
        routes=[BoundedRouteInfo(path="/custom", method="GET")],
        max_journeys=2,
    )

    analysis = await agent.analyze(
        context=mock_project_context,
        browser_journey_input=explicit_input,
    )

    assert "journey_input" in analysis
    assert analysis["journey_input"] == explicit_input
    assert agent._current_input == explicit_input


@pytest.mark.asyncio
async def test_agent_analyze_hook_auto_extraction(mock_project_context: ProjectContextResponse):
    agent = BrowserJourneyGenerationAgent()
    await agent.initialize()

    analysis = await agent.analyze(
        context=mock_project_context,
        routes=["/home", "/cart"],
        architecture_components=["AuthModule", "CartModule"],
        file_manifest=["src/App.tsx", "src/Cart.tsx"],
        max_journeys=3,
    )

    journey_input: BrowserJourneyGenerationInput = analysis["journey_input"]
    assert journey_input.project_id == mock_project_context.project.id
    assert len(journey_input.requirements) == 2
    assert len(journey_input.routes) == 2
    assert journey_input.routes[0].path == "/home"
    assert journey_input.routes[1].path == "/cart"
    assert journey_input.architecture_components == ["AuthModule", "CartModule"]
    assert journey_input.max_journeys == 3


@pytest.mark.asyncio
async def test_agent_generate_hook_with_mock_provider(
    mock_project_context: ProjectContextResponse,
    sample_candidate_suite: BrowserJourneySuiteCandidate,
):
    agent = BrowserJourneyGenerationAgent()
    await agent.initialize()

    analysis = await agent.analyze(context=mock_project_context)

    mock_provider = MockLLMProvider()
    mock_provider.register_structured_response(sample_candidate_suite)

    candidate = await agent.generate(
        analysis_result=analysis,
        provider=mock_provider,
    )

    assert isinstance(candidate, BrowserJourneySuiteCandidate)
    assert len(candidate.journeys) == 1
    assert candidate.journeys[0].journey_id == "BJ-001"
    assert len(mock_provider.call_history) == 1
    # Verify untrusted content boundary was used in prompt
    user_prompt_content = mock_provider.call_history[0].messages[1].content
    assert "<untrusted_content>" in user_prompt_content
    assert "</untrusted_content>" in user_prompt_content


# ==============================================================================
# 3. AgentExecutor Governance & Execution Tests
# ==============================================================================

@pytest.mark.asyncio
async def test_agent_executor_successful_run(
    mock_project_context: ProjectContextResponse,
    sample_candidate_suite: BrowserJourneySuiteCandidate,
):
    agent = BrowserJourneyGenerationAgent()
    mock_provider = MockLLMProvider()
    mock_provider.register_structured_response(sample_candidate_suite)

    executor = AgentExecutor(provider=mock_provider)
    result = await executor.execute(
        agent=agent,
        context=mock_project_context,
    )

    assert result.status == AgentExecutionStatus.COMPLETED
    assert result.agent_id == "browser-journey-generation"
    assert result.agent_version == "1.0.0"
    assert result.output is not None
    assert isinstance(result.output, BrowserJourneySuiteCandidate)
    assert len(result.output.journeys) == 1
    assert result.validation.is_valid is True
    assert result.error is None


@pytest.mark.asyncio
async def test_agent_executor_handles_json_mock_response(
    mock_project_context: ProjectContextResponse,
    sample_candidate_suite: BrowserJourneySuiteCandidate,
):
    agent = BrowserJourneyGenerationAgent()
    mock_provider = MockLLMProvider()
    # Register serialized JSON
    mock_provider.register_response(sample_candidate_suite.model_dump_json())

    executor = AgentExecutor(provider=mock_provider)
    result = await executor.execute(
        agent=agent,
        context=mock_project_context,
    )

    assert result.status == AgentExecutionStatus.COMPLETED
    assert result.output is not None
    assert result.output.suite_name == sample_candidate_suite.suite_name


@pytest.mark.asyncio
async def test_agent_executor_malformed_provider_json_rejection(
    mock_project_context: ProjectContextResponse,
):
    agent = BrowserJourneyGenerationAgent()
    mock_provider = MockLLMProvider()

    # Provide malformed JSON missing required journey fields
    malformed_json = '{"suite_name": "Bad Suite", "journeys": [{"journey_id": "BJ-BAD"}]}'
    mock_provider.register_response(malformed_json)

    executor = AgentExecutor(provider=mock_provider)
    result = await executor.execute(
        agent=agent,
        context=mock_project_context,
    )

    assert result.status == AgentExecutionStatus.FAILED
    assert result.output is None
    assert result.error is not None
    assert result.error.error_code == "PROVIDER_ERROR"
    assert result.error.transient is False


@pytest.mark.asyncio
async def test_agent_executor_domain_validation_failure_no_retry(
    mock_project_context: ProjectContextResponse,
    sample_candidate_suite: BrowserJourneySuiteCandidate,
):
    agent = BrowserJourneyGenerationAgent()
    mock_provider = MockLLMProvider()
    mock_provider.register_structured_response(sample_candidate_suite)

    # Monkeypatch validate_output to simulate deterministic business rule rejection
    agent.validate_output = MagicMock(
        return_value=MagicMock(is_valid=False, errors=["Deterministic domain invariant failed: disallowed interaction."])
    )

    executor = AgentExecutor(provider=mock_provider)
    result = await executor.execute(
        agent=agent,
        context=mock_project_context,
    )

    assert result.status == AgentExecutionStatus.FAILED
    assert result.output is None
    assert result.error is not None
    assert result.error.error_code == "VALIDATION_FAILED"
    assert result.error.transient is False


# ==============================================================================
# 4. Candidate vs Authoritative Boundaries & Traceability Tests
# ==============================================================================

@pytest.mark.asyncio
async def test_hallucinated_requirement_ids_accepted_as_candidate_intent(
    mock_project_context: ProjectContextResponse,
):
    """Stage 1 accepts proposed requirement IDs without claiming they are authoritative.
    
    Deterministic matching and coverage calculation are strictly deferred to Stage 2.
    Stage 1 candidate output must NOT be marked as authoritative or validated.
    """
    hallucinated_req_id = "FABRICATED-REQ-999"
    hallucinated_route = "/unmapped-route"

    journey = BrowserJourney(
        journey_id="BJ-PROPOSED-01",
        title="Proposed Journey with Unverified Traceability",
        description="LLM proposed requirement ID that does not exist in canonical context.",
        category=JourneyCategory.BUSINESS_RULE,
        priority=JourneyPriority.LOW,
        requirement_ids=[hallucinated_req_id],
        target_routes=[hallucinated_route],
        steps=[
            BrowserJourneyStep(
                step_id="step-1",
                action=BrowserActionType.NAVIGATE,
                route=hallucinated_route,
                description="Navigate to unverified route",
            )
        ],
    )
    candidate_suite = BrowserJourneySuiteCandidate(
        suite_name="Candidate Proposal",
        journeys=[journey],
    )

    agent = BrowserJourneyGenerationAgent()
    mock_provider = MockLLMProvider()
    mock_provider.register_structured_response(candidate_suite)

    executor = AgentExecutor(provider=mock_provider)
    result = await executor.execute(
        agent=agent,
        context=mock_project_context,
    )

    # In Stage 1, the candidate is accepted structurally as a candidate proposal
    assert result.status == AgentExecutionStatus.COMPLETED
    assert result.output is not None
    assert isinstance(result.output, BrowserJourneySuiteCandidate)
    assert result.output.journeys[0].requirement_ids == [hallucinated_req_id]

    # Explicit boundary invariant: Candidate output is NOT a ValidatedBrowserJourneySuite
    assert not hasattr(result.output, "is_executable")
    assert not hasattr(result.output, "coverage_percentage")
    assert not hasattr(result.output, "validated_requirement_ids")


def test_candidate_output_cannot_be_executed_directly():
    """Verify BrowserJourneySuiteCandidate has no execution, browser, or Docker hooks."""
    candidate = BrowserJourneySuiteCandidate(
        suite_name="Intent Suite",
        journeys=[],
    )
    assert not hasattr(candidate, "execute")
    assert not hasattr(candidate, "run")
    assert not hasattr(candidate, "to_playwright_script")
    assert not hasattr(candidate, "launch_browser")
