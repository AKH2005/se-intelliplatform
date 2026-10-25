"""Unit Tests for Phase 11K — Stage 3: Browser Journey Adapter.

Tests deterministic transformation of ValidatedBrowserJourneySuite into
Phase 11J DeterministicBrowserTestDefinition instances.
"""

import uuid
import pytest
from unittest.mock import AsyncMock, patch

from app.agents.browser_journey.contracts import (
    BrowserActionType,
    BrowserJourney,
    BrowserJourneyStep,
    BrowserJourneySuiteCandidate,
    BrowserTarget,
    BrowserTargetType,
    JourneyCategory,
    JourneyPriority,
)
from app.browser.contracts import (
    BrowserInteractionType,
    DeterministicBrowserTestDefinition,
    DeterministicInteraction,
)
from app.browser.browser_testing_service import BrowserTestingService
from app.browser.journey.adapter import BrowserJourneyAdapter
from app.browser.journey.contracts import (
    RequirementCoverageReport,
    ValidatedBrowserJourney,
    ValidatedBrowserJourneySuite,
)
from app.browser.journey.errors import BrowserJourneyAdaptationError
from app.schemas.browser_testing import BrowserTestRun, BrowserTestStatus


# ==============================================================================
# Test Fixtures
# ==============================================================================

@pytest.fixture
def sample_project_id() -> uuid.UUID:
    return uuid.uuid4()


@pytest.fixture
def sample_coverage_report() -> RequirementCoverageReport:
    return RequirementCoverageReport(
        total_active_requirements=2,
        covered_requirement_count=2,
        uncovered_requirement_count=0,
        coverage_percentage=100.0,
        journey_count=1,
        covered_requirement_ids=["REQ-01", "REQ-02"],
        uncovered_requirement_ids=[],
        requirement_to_journeys_map={"REQ-01": ["BJ-001"], "REQ-02": ["BJ-001"]},
        journey_to_requirements_map={"BJ-001": ["REQ-01", "REQ-02"]},
    )


@pytest.fixture
def sample_validated_journey() -> ValidatedBrowserJourney:
    return ValidatedBrowserJourney(
        journey_id="BJ-001",
        title="User Login Flow",
        description="Verify user can navigate to login and authenticate.",
        category=JourneyCategory.AUTHENTICATION,
        priority=JourneyPriority.HIGH,
        validated_requirement_ids=["REQ-01", "REQ-02"],
        preconditions=["User is registered"],
        validated_target_routes=["/login", "/dashboard"],
        steps=[
            BrowserJourneyStep(
                step_id="S01",
                action=BrowserActionType.NAVIGATE,
                route="/login",
                description="Navigate to login page",
                timeout_seconds=5.0,
            ),
            BrowserJourneyStep(
                step_id="S02",
                action=BrowserActionType.FILL,
                target=BrowserTarget(
                    target_type=BrowserTargetType.TEST_ID,
                    value="email-input",
                ),
                value="test@example.com",
                description="Fill in email address",
                timeout_seconds=5.0,
            ),
            BrowserJourneyStep(
                step_id="S03",
                action=BrowserActionType.CLICK,
                target=BrowserTarget(
                    target_type=BrowserTargetType.TEST_ID,
                    value="login-submit",
                ),
                description="Click submit button",
                timeout_seconds=5.0,
            ),
            BrowserJourneyStep(
                step_id="S04",
                action=BrowserActionType.ASSERT_TEXT,
                target=BrowserTarget(
                    target_type=BrowserTargetType.TEST_ID,
                    value="welcome-message",
                ),
                value="Welcome back",
                description="Assert welcome message is displayed",
                timeout_seconds=5.0,
            ),
        ],
        expected_outcomes=["User arrives at dashboard"],
    )


@pytest.fixture
def sample_validated_suite(
    sample_project_id: uuid.UUID,
    sample_validated_journey: ValidatedBrowserJourney,
    sample_coverage_report: RequirementCoverageReport,
) -> ValidatedBrowserJourneySuite:
    return ValidatedBrowserJourneySuite(
        suite_id="suite-123",
        project_id=sample_project_id,
        suite_name="Auth Smoke Suite",
        summary="Automated browser journeys covering core auth requirements",
        journeys=[sample_validated_journey],
        coverage_report=sample_coverage_report,
    )


# ==============================================================================
# A. Basic Adaptation Tests
# ==============================================================================

class TestBasicAdaptation:
    """Verifies basic suite and journey adaptation to DeterministicBrowserTestDefinition."""

    def test_adapt_single_journey(self, sample_validated_suite: ValidatedBrowserJourneySuite):
        test_defs = BrowserJourneyAdapter.adapt(sample_validated_suite)
        assert len(test_defs) == 1
        td = test_defs[0]
        assert isinstance(td, DeterministicBrowserTestDefinition)
        assert td.test_id == "journey_BJ-001"
        assert td.name == "User Login Flow"
        assert td.target_path == "/login"
        assert td.expected_status == 200
        assert td.expected_elements == ["body"]
        assert len(td.interactions) == 4
        assert td.capture_screenshot is True

    def test_adapt_multiple_journeys(
        self,
        sample_project_id: uuid.UUID,
        sample_coverage_report: RequirementCoverageReport,
    ):
        j1 = ValidatedBrowserJourney(
            journey_id="BJ-001",
            title="Journey One",
            description="First journey",
            category=JourneyCategory.NAVIGATION,
            validated_requirement_ids=["REQ-01"],
            validated_target_routes=["/home"],
            steps=[
                BrowserJourneyStep(
                    step_id="S01",
                    action=BrowserActionType.NAVIGATE,
                    route="/home",
                    description="Go home",
                )
            ],
        )
        j2 = ValidatedBrowserJourney(
            journey_id="BJ-002",
            title="Journey Two",
            description="Second journey",
            category=JourneyCategory.CRUD,
            validated_requirement_ids=["REQ-02"],
            validated_target_routes=["/settings"],
            steps=[
                BrowserJourneyStep(
                    step_id="S01",
                    action=BrowserActionType.NAVIGATE,
                    route="/settings",
                    description="Go to settings",
                )
            ],
        )
        suite = ValidatedBrowserJourneySuite(
            project_id=sample_project_id,
            suite_name="Multi Suite",
            summary="Two journeys",
            journeys=[j1, j2],
            coverage_report=sample_coverage_report,
        )

        test_defs = BrowserJourneyAdapter.adapt(suite)
        assert len(test_defs) == 2
        assert test_defs[0].test_id == "journey_BJ-001"
        assert test_defs[0].target_path == "/home"
        assert test_defs[1].test_id == "journey_BJ-002"
        assert test_defs[1].target_path == "/settings"


# ==============================================================================
# B. Action Mapping Tests (All 12 Actions)
# ==============================================================================

class TestActionMapping:
    """Verifies that all 12 BrowserActionTypes deterministically map to runner operations."""

    def test_map_navigate(self):
        step = BrowserJourneyStep(
            step_id="S01",
            action=BrowserActionType.NAVIGATE,
            route="/dashboard",
            description="Navigate to dashboard",
            timeout_seconds=8.0,
        )
        interaction = BrowserJourneyAdapter.step_to_interaction(step)
        assert interaction.action == BrowserInteractionType.NAVIGATE
        assert interaction.selector == "body"
        assert interaction.value == "/dashboard"
        assert interaction.timeout_seconds == 8.0

    def test_map_click(self):
        step = BrowserJourneyStep(
            step_id="S02",
            action=BrowserActionType.CLICK,
            target=BrowserTarget(target_type=BrowserTargetType.TEST_ID, value="save-btn"),
            description="Click save",
        )
        interaction = BrowserJourneyAdapter.step_to_interaction(step)
        assert interaction.action == BrowserInteractionType.CLICK
        assert interaction.selector == '[data-testid="save-btn"]'

    def test_map_fill(self):
        step = BrowserJourneyStep(
            step_id="S03",
            action=BrowserActionType.FILL,
            target=BrowserTarget(target_type=BrowserTargetType.NAME, value="username"),
            value="alice",
            description="Enter username",
        )
        interaction = BrowserJourneyAdapter.step_to_interaction(step)
        assert interaction.action == BrowserInteractionType.FILL
        assert interaction.selector == '[name="username"]'
        assert interaction.value == "alice"

    def test_map_select(self):
        step = BrowserJourneyStep(
            step_id="S04",
            action=BrowserActionType.SELECT,
            target=BrowserTarget(target_type=BrowserTargetType.TEST_ID, value="country-select"),
            value="US",
            description="Select country",
        )
        interaction = BrowserJourneyAdapter.step_to_interaction(step)
        assert interaction.action == BrowserInteractionType.SELECT
        assert interaction.selector == '[data-testid="country-select"]'
        assert interaction.value == "US"

    def test_map_check(self):
        step = BrowserJourneyStep(
            step_id="S05",
            action=BrowserActionType.CHECK,
            target=BrowserTarget(target_type=BrowserTargetType.TEST_ID, value="agree-terms"),
            description="Check terms agreement",
        )
        interaction = BrowserJourneyAdapter.step_to_interaction(step)
        assert interaction.action == BrowserInteractionType.CLICK
        assert interaction.selector == '[data-testid="agree-terms"]'

    def test_map_uncheck(self):
        step = BrowserJourneyStep(
            step_id="S06",
            action=BrowserActionType.UNCHECK,
            target=BrowserTarget(target_type=BrowserTargetType.TEST_ID, value="newsletter-opt-in"),
            description="Uncheck newsletter",
        )
        interaction = BrowserJourneyAdapter.step_to_interaction(step)
        assert interaction.action == BrowserInteractionType.CLICK
        assert interaction.selector == '[data-testid="newsletter-opt-in"]'

    def test_map_submit_with_target(self):
        step = BrowserJourneyStep(
            step_id="S07",
            action=BrowserActionType.SUBMIT,
            target=BrowserTarget(target_type=BrowserTargetType.TEST_ID, value="form-submit"),
            description="Submit the form",
        )
        interaction = BrowserJourneyAdapter.step_to_interaction(step)
        assert interaction.action == BrowserInteractionType.CLICK
        assert interaction.selector == '[data-testid="form-submit"]'

    def test_map_submit_without_target(self):
        step = BrowserJourneyStep(
            step_id="S08",
            action=BrowserActionType.SUBMIT,
            target=BrowserTarget(target_type=BrowserTargetType.TEST_ID, value="btn"),
            description="Submit default form",
        )
        object.__setattr__(step, "target", None)
        interaction = BrowserJourneyAdapter.step_to_interaction(step)
        assert interaction.action == BrowserInteractionType.CLICK
        assert interaction.selector == 'button[type="submit"], input[type="submit"]'

    def test_map_assert_text(self):
        step = BrowserJourneyStep(
            step_id="S09",
            action=BrowserActionType.ASSERT_TEXT,
            target=BrowserTarget(target_type=BrowserTargetType.TEST_ID, value="alert-box"),
            value="Success!",
            description="Assert success alert text",
        )
        interaction = BrowserJourneyAdapter.step_to_interaction(step)
        assert interaction.action == BrowserInteractionType.ASSERT_TEXT
        assert interaction.selector == '[data-testid="alert-box"]'
        assert interaction.expected_text == "Success!"

    def test_map_assert_visible(self):
        step = BrowserJourneyStep(
            step_id="S10",
            action=BrowserActionType.ASSERT_VISIBLE,
            target=BrowserTarget(target_type=BrowserTargetType.ROLE, value="dialog"),
            description="Assert dialog modal is visible",
        )
        interaction = BrowserJourneyAdapter.step_to_interaction(step)
        assert interaction.action == BrowserInteractionType.ASSERT_VISIBLE
        assert interaction.selector == '[role="dialog"]'

    def test_map_assert_element(self):
        step = BrowserJourneyStep(
            step_id="S11",
            action=BrowserActionType.ASSERT_ELEMENT,
            target=BrowserTarget(target_type=BrowserTargetType.TEST_ID, value="footer"),
            description="Assert footer element exists and is visible",
        )
        interaction = BrowserJourneyAdapter.step_to_interaction(step)
        assert interaction.action == BrowserInteractionType.ASSERT_VISIBLE
        assert interaction.selector == '[data-testid="footer"]'

    def test_map_assert_url(self):
        step = BrowserJourneyStep(
            step_id="S12",
            action=BrowserActionType.ASSERT_URL,
            route="/checkout/confirmation",
            description="Assert URL is checkout confirmation",
        )
        interaction = BrowserJourneyAdapter.step_to_interaction(step)
        assert interaction.action == BrowserInteractionType.ASSERT_URL
        assert interaction.selector == "body"
        assert interaction.value == "/checkout/confirmation"

    def test_map_wait(self):
        step = BrowserJourneyStep(
            step_id="S13",
            action=BrowserActionType.WAIT,
            value="2.5",
            description="Wait 2.5 seconds for animation",
            timeout_seconds=3.0,
        )
        interaction = BrowserJourneyAdapter.step_to_interaction(step)
        assert interaction.action == BrowserInteractionType.WAIT
        assert interaction.selector == "body"
        assert interaction.value == "2.5"


# ==============================================================================
# C. Target Mapping Tests (All 6 Target Types)
# ==============================================================================

class TestTargetMapping:
    """Verifies that all 6 BrowserTargetTypes translate into safe, deterministic selectors."""

    def test_target_test_id(self):
        t = BrowserTarget(target_type=BrowserTargetType.TEST_ID, value="submit-button")
        assert BrowserJourneyAdapter.target_to_selector(t) == '[data-testid="submit-button"]'

    def test_target_role(self):
        t = BrowserTarget(target_type=BrowserTargetType.ROLE, value="navigation")
        assert BrowserJourneyAdapter.target_to_selector(t) == '[role="navigation"]'

    def test_target_label(self):
        t = BrowserTarget(target_type=BrowserTargetType.LABEL, value="Email Address")
        assert BrowserJourneyAdapter.target_to_selector(t) == '[aria-label="Email Address"], label:has-text("Email Address")'

    def test_target_name(self):
        t = BrowserTarget(target_type=BrowserTargetType.NAME, value="password")
        assert BrowserJourneyAdapter.target_to_selector(t) == '[name="password"]'

    def test_target_text(self):
        t = BrowserTarget(target_type=BrowserTargetType.TEXT, value="Click Here")
        assert BrowserJourneyAdapter.target_to_selector(t) == 'text="Click Here"'

    def test_target_css_selector(self):
        t = BrowserTarget(target_type=BrowserTargetType.CSS_SELECTOR, value="div.container > button.primary")
        assert BrowserJourneyAdapter.target_to_selector(t) == "div.container > button.primary"


# ==============================================================================
# D. Determinism & Traceability Tests
# ==============================================================================

class TestDeterminismAndTraceability:
    """Verifies test ID stability, repeated adaptation equivalence, and metadata preservation."""

    def test_determinism_twice_run(self, sample_validated_suite: ValidatedBrowserJourneySuite):
        run_1 = BrowserJourneyAdapter.adapt(sample_validated_suite)
        run_2 = BrowserJourneyAdapter.adapt(sample_validated_suite)

        assert len(run_1) == len(run_2)
        for d1, d2 in zip(run_1, run_2):
            assert d1.test_id == d2.test_id
            assert d1.name == d2.name
            assert d1.target_path == d2.target_path
            assert d1.expected_status == d2.expected_status
            assert d1.expected_elements == d2.expected_elements
            assert d1.metadata == d2.metadata
            assert len(d1.interactions) == len(d2.interactions)
            for i1, i2 in zip(d1.interactions, d2.interactions):
                assert i1.action == i2.action
                assert i1.selector == i2.selector
                assert i1.value == i2.value
                assert i1.expected_text == i2.expected_text
                assert i1.timeout_seconds == i2.timeout_seconds

    def test_test_id_conforms_to_schema_regex(self):
        journey = ValidatedBrowserJourney(
            journey_id="BJ:001!special*chars",
            title="Complex ID Journey",
            description="Testing character cleaning in ID",
            category=JourneyCategory.NAVIGATION,
            validated_requirement_ids=["REQ-01"],
            steps=[
                BrowserJourneyStep(
                    step_id="S1",
                    action=BrowserActionType.NAVIGATE,
                    route="/",
                    description="Nav",
                )
            ],
        )
        td = BrowserJourneyAdapter.adapt_journey(journey)
        # Must match pattern ^[a-zA-Z0-9_\-]+$
        import re
        assert re.match(r"^[a-zA-Z0-9_\-]+$", td.test_id)
        assert td.test_id == "journey_BJ_001_special_chars"

    def test_metadata_traceability(self, sample_validated_suite: ValidatedBrowserJourneySuite):
        test_defs = BrowserJourneyAdapter.adapt(sample_validated_suite)
        meta = test_defs[0].metadata

        assert meta["journey_id"] == "BJ-001"
        assert meta["title"] == "User Login Flow"
        assert meta["category"] == "AUTHENTICATION"
        assert meta["priority"] == "HIGH"
        assert meta["requirement_ids"] == ["REQ-01", "REQ-02"]
        assert meta["preconditions"] == ["User is registered"]
        assert meta["expected_outcomes"] == ["User arrives at dashboard"]


# ==============================================================================
# E. Security & Defensive Boundary Tests
# ==============================================================================

class TestSecurityAndDefensiveBoundaries:
    """Verifies rejection of dangerous protocols, external hosts, and injection attempts."""

    def test_reject_external_url_in_navigate(self):
        step = BrowserJourneyStep(
            step_id="S01",
            action=BrowserActionType.NAVIGATE,
            route="/valid",
            description="External navigation attempt",
        )
        object.__setattr__(step, "route", "https://evil.com/phish")
        with pytest.raises(BrowserJourneyAdaptationError, match="Unsafe or external"):
            BrowserJourneyAdapter.step_to_interaction(step)

    def test_reject_javascript_scheme_in_navigate(self):
        step = BrowserJourneyStep(
            step_id="S01",
            action=BrowserActionType.NAVIGATE,
            route="/valid",
            description="JS navigation attempt",
        )
        object.__setattr__(step, "route", "javascript:alert(1)")
        with pytest.raises(BrowserJourneyAdaptationError, match="Unsafe or external"):
            BrowserJourneyAdapter.step_to_interaction(step)

    def test_reject_data_scheme_in_navigate(self):
        step = BrowserJourneyStep(
            step_id="S01",
            action=BrowserActionType.NAVIGATE,
            route="/valid",
            description="Data scheme navigation attempt",
        )
        object.__setattr__(step, "route", "data:text/html,<h1>XSS</h1>")
        with pytest.raises(BrowserJourneyAdaptationError, match="Unsafe or external"):
            BrowserJourneyAdapter.step_to_interaction(step)

    def test_reject_path_traversal_in_navigate(self):
        step = BrowserJourneyStep(
            step_id="S01",
            action=BrowserActionType.NAVIGATE,
            route="/valid",
            description="Traversal attempt",
        )
        object.__setattr__(step, "route", "/app/../../etc/passwd")
        with pytest.raises(BrowserJourneyAdaptationError, match="Path traversal"):
            BrowserJourneyAdapter.step_to_interaction(step)

    def test_reject_unsafe_injection_in_target_value(self):
        target = BrowserTarget(
            target_type=BrowserTargetType.TEST_ID,
            value="valid-btn",
        )
        object.__setattr__(target, "value", "btn<script>alert(1)</script>")
        with pytest.raises(BrowserJourneyAdaptationError, match="prohibited injection"):
            BrowserJourneyAdapter.target_to_selector(target)

    def test_reject_quotes_in_attribute_targets(self):
        target = BrowserTarget(
            target_type=BrowserTargetType.TEST_ID,
            value="valid-btn",
        )
        object.__setattr__(target, "value", 'btn" or "1"="1')
        with pytest.raises(BrowserJourneyAdaptationError, match="quotes"):
            BrowserJourneyAdapter.target_to_selector(target)

    def test_reject_unsafe_css_selector(self):
        target = BrowserTarget(
            target_type=BrowserTargetType.CSS_SELECTOR,
            value="div.valid",
        )
        object.__setattr__(target, "value", "div[onload=alert(1)]")
        with pytest.raises(BrowserJourneyAdaptationError, match="prohibited injection"):
            BrowserJourneyAdapter.target_to_selector(target)

    def test_wait_bounds_enforced(self):
        # Even if step claims 100 seconds, adapter bounds it to <= 15.0
        step = BrowserJourneyStep(
            step_id="S01",
            action=BrowserActionType.WAIT,
            value="100.0",
            description="Large wait attempt",
        )
        interaction = BrowserJourneyAdapter.step_to_interaction(step)
        assert float(interaction.value) == 15.0
        assert interaction.timeout_seconds <= 15.0


# ==============================================================================
# F. Input Boundary & Failure Handling Tests
# ==============================================================================

class TestInputBoundary:
    """Verifies that only ValidatedBrowserJourneySuite is accepted and malformed inputs fail."""

    def test_reject_candidate_suite(self, sample_project_id: uuid.UUID):
        candidate = BrowserJourneySuiteCandidate(
            project_id=sample_project_id,
            suite_name="Candidate Suite",
            summary="Unvalidated raw candidate from LLM",
            journeys=[
                BrowserJourney(
                    journey_id="BJ-001",
                    title="Candidate",
                    description="Raw candidate",
                    category=JourneyCategory.AUTHENTICATION,
                    steps=[
                        BrowserJourneyStep(
                            step_id="S1",
                            action=BrowserActionType.NAVIGATE,
                            route="/",
                            description="Nav",
                        )
                    ],
                )
            ],
        )
        with pytest.raises(TypeError, match="BrowserJourneyAdapter requires ValidatedBrowserJourneySuite"):
            BrowserJourneyAdapter.adapt(candidate)

    def test_reject_arbitrary_dict(self):
        with pytest.raises(TypeError, match="BrowserJourneyAdapter requires ValidatedBrowserJourneySuite"):
            BrowserJourneyAdapter.adapt({"project_id": "123", "journeys": []})

    def test_reject_empty_suite(
        self,
        sample_project_id: uuid.UUID,
        sample_coverage_report: RequirementCoverageReport,
    ):
        suite = ValidatedBrowserJourneySuite(
            project_id=sample_project_id,
            suite_name="Empty Suite",
            summary="Suite without journeys",
            journeys=[
                ValidatedBrowserJourney(
                    journey_id="BJ-001",
                    title="Journey Test",
                    description="Description test",
                    category=JourneyCategory.NAVIGATION,
                    steps=[
                        BrowserJourneyStep(
                            step_id="S1",
                            action=BrowserActionType.NAVIGATE,
                            route="/",
                            description="Nav",
                        )
                    ],
                )
            ],
            coverage_report=sample_coverage_report,
        )
        suite.journeys = []  # artificially empty
        with pytest.raises(BrowserJourneyAdaptationError, match="at least one journey"):
            BrowserJourneyAdapter.adapt(suite)

    def test_reject_action_missing_required_target(self):
        step = BrowserJourneyStep(
            step_id="S01",
            action=BrowserActionType.CLICK,
            target=BrowserTarget(target_type=BrowserTargetType.TEST_ID, value="btn"),
            description="Click without target",
        )
        object.__setattr__(step, "target", None)
        with pytest.raises(BrowserJourneyAdaptationError, match="requires a target"):
            BrowserJourneyAdapter.step_to_interaction(step)


# ==============================================================================
# G. BrowserTestingService Integration Tests
# ==============================================================================

class TestBrowserTestingServiceIntegration:
    """Verifies that BrowserTestingService.execute_validated_browser_journey_suite integrates correctly."""

    @pytest.mark.asyncio
    async def test_service_rejects_unvalidated_candidate(
        self,
        sample_project_id: uuid.UUID,
    ):
        service = BrowserTestingService()
        candidate = BrowserJourneySuiteCandidate(
            project_id=sample_project_id,
            suite_name="Candidate",
            summary="Candidate summary",
            journeys=[],
        )
        with pytest.raises(TypeError, match="requires ValidatedBrowserJourneySuite"):
            await service.execute_validated_browser_journey_suite(candidate)

    @pytest.mark.asyncio
    async def test_service_adapts_and_executes_validated_suite(
        self,
        sample_validated_suite: ValidatedBrowserJourneySuite,
    ):
        service = BrowserTestingService()
        dummy_run = BrowserTestRun(
            run_id=uuid.uuid4(),
            project_id=sample_validated_suite.project_id,
            status=BrowserTestStatus.PASSED,
            summary="Test run passed",
        )

        with patch.object(service, "execute_browser_tests", new_callable=AsyncMock) as mock_exec:
            mock_exec.return_value = dummy_run

            result = await service.execute_validated_browser_journey_suite(sample_validated_suite)

            assert result == dummy_run
            mock_exec.assert_awaited_once()

            # Verify that adapted test_definitions were passed to execute_browser_tests
            call_kwargs = mock_exec.call_args.kwargs
            test_defs = call_kwargs["test_definitions"]
            assert len(test_defs) == 1
            assert test_defs[0].test_id == "journey_BJ-001"
            assert test_defs[0].metadata["journey_id"] == "BJ-001"
            assert test_defs[0].metadata["requirement_ids"] == ["REQ-01", "REQ-02"]
