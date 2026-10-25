"""Unit Tests for Phase 11K Stage 2 Browser Journey Validator.

Tests deterministic structural checks, requirement validation with project isolation,
authoritative route manifest matching (including parameterized paths), security sniffing,
complexity limits, and conversion to ValidatedBrowserJourneySuite.
"""

import uuid
import pytest

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
from app.browser.journey.contracts import (
    ValidatedBrowserJourneySuite,
    ValidationCategory,
    ValidationContext,
    ValidationSeverity,
)
from app.browser.journey.errors import BrowserJourneyValidationError
from app.browser.journey.validator import BrowserJourneyValidator


# ==============================================================================
# Fixtures & Helpers
# ==============================================================================

@pytest.fixture
def project_id() -> uuid.UUID:
    return uuid.uuid4()


@pytest.fixture
def base_context(project_id: uuid.UUID) -> ValidationContext:
    return ValidationContext(
        project_id=project_id,
        active_requirement_ids={"REQ-001", "REQ-002", "REQ-003"},
        all_project_requirement_ids={"REQ-001", "REQ-002", "REQ-003", "REQ-INACTIVE-01"},
        other_project_requirement_ids={"FOREIGN-REQ-999"},
        authoritative_routes=["/", "/login", "/dashboard", "/projects/{project_id}"],
    )


def _make_valid_step(step_id: str = "s1") -> BrowserJourneyStep:
    return BrowserJourneyStep(
        step_id=step_id,
        action=BrowserActionType.NAVIGATE,
        route="/login",
        description="Navigate to login page",
    )


def _make_valid_journey(journey_id: str = "BJ-001", req_ids: list[str] | None = None) -> BrowserJourney:
    return BrowserJourney(
        journey_id=journey_id,
        title="Sign In Journey",
        description="User authentication happy path",
        category=JourneyCategory.AUTHENTICATION,
        priority=JourneyPriority.HIGH,
        requirement_ids=req_ids or ["REQ-001"],
        target_routes=["/login", "/dashboard"],
        steps=[
            BrowserJourneyStep(
                step_id="step-1",
                action=BrowserActionType.NAVIGATE,
                route="/login",
                description="Go to login page",
            ),
            BrowserJourneyStep(
                step_id="step-2",
                action=BrowserActionType.FILL,
                target=BrowserTarget(target_type=BrowserTargetType.TEST_ID, value="email-input"),
                value="test@example.com",
                description="Enter test email",
            ),
            BrowserJourneyStep(
                step_id="step-3",
                action=BrowserActionType.CLICK,
                target=BrowserTarget(target_type=BrowserTargetType.TEST_ID, value="login-btn"),
                description="Click submit button",
            ),
            BrowserJourneyStep(
                step_id="step-4",
                action=BrowserActionType.ASSERT_URL,
                route="/dashboard",
                description="Verify redirected to dashboard",
            ),
        ],
        expected_outcomes=["User reaches dashboard"],
    )


# ==============================================================================
# 1. Structural & Core Validation Tests
# ==============================================================================

def test_valid_candidate_suite_compiles_successfully(base_context: ValidationContext):
    journey = _make_valid_journey("BJ-001", ["REQ-001", "REQ-002"])
    candidate = BrowserJourneySuiteCandidate(
        suite_name="Auth Test Suite",
        summary="Verifies authentication flows",
        journeys=[journey],
    )

    validated_suite, outcome = BrowserJourneyValidator.validate(candidate, base_context)

    assert outcome.is_valid is True
    assert len(outcome.errors) == 0
    assert validated_suite is not None
    assert isinstance(validated_suite, ValidatedBrowserJourneySuite)
    assert validated_suite.project_id == base_context.project_id
    assert len(validated_suite.journeys) == 1
    assert validated_suite.journeys[0].journey_id == "BJ-001"
    assert validated_suite.journeys[0].validated_requirement_ids == ["REQ-001", "REQ-002"]
    assert validated_suite.coverage_report.covered_requirement_count == 2
    assert validated_suite.coverage_report.total_active_requirements == 3


def test_empty_candidate_suite_rejected(base_context: ValidationContext):
    candidate = BrowserJourneySuiteCandidate(
        suite_name="Empty Suite",
        journeys=[],
    )

    validated_suite, outcome = BrowserJourneyValidator.validate(candidate, base_context)

    assert outcome.is_valid is False
    assert validated_suite is None
    codes = [e.code for e in outcome.errors]
    assert "EMPTY_SUITE" in codes


def test_duplicate_journey_content_rejected(base_context: ValidationContext):
    j1 = _make_valid_journey("BJ-001")
    # Same title, category, and steps as j1, but different ID
    j2 = BrowserJourney(
        journey_id="BJ-002",
        title=j1.title,
        description="Different description",
        category=j1.category,
        priority=j1.priority,
        requirement_ids=j1.requirement_ids,
        target_routes=j1.target_routes,
        steps=j1.steps,
    )
    candidate = BrowserJourneySuiteCandidate(
        suite_name="Dupe Content Suite",
        journeys=[j1, j2],
    )

    validated_suite, outcome = BrowserJourneyValidator.validate(candidate, base_context)

    assert outcome.is_valid is False
    assert validated_suite is None
    codes = [e.code for e in outcome.errors]
    assert "DUPLICATE_JOURNEY_CONTENT" in codes


# ==============================================================================
# 2. Requirement Validation & Project Isolation Tests
# ==============================================================================

def test_hallucinated_requirement_id_rejected(base_context: ValidationContext):
    journey = _make_valid_journey("BJ-001", req_ids=["FABRICATED-REQ-007"])
    candidate = BrowserJourneySuiteCandidate(journeys=[journey])

    validated_suite, outcome = BrowserJourneyValidator.validate(candidate, base_context)

    assert outcome.is_valid is False
    assert validated_suite is None
    codes = [e.code for e in outcome.errors]
    assert "HALLUCINATED_REQUIREMENT" in codes
    assert any("FABRICATED-REQ-007" in e.message for e in outcome.errors)


def test_cross_project_requirement_isolation_enforced(base_context: ValidationContext):
    # References requirement belonging to a foreign project
    journey = _make_valid_journey("BJ-001", req_ids=["FOREIGN-REQ-999"])
    candidate = BrowserJourneySuiteCandidate(journeys=[journey])

    validated_suite, outcome = BrowserJourneyValidator.validate(candidate, base_context)

    assert outcome.is_valid is False
    assert validated_suite is None
    codes = [e.code for e in outcome.errors]
    assert "CROSS_PROJECT_REQUIREMENT_FORBIDDEN" in codes
    assert any("FOREIGN-REQ-999" in e.message for e in outcome.errors)


def test_inactive_requirement_rejected(base_context: ValidationContext):
    # REQ-INACTIVE-01 is in all_project_requirement_ids but not in active_requirement_ids
    journey = _make_valid_journey("BJ-001", req_ids=["REQ-INACTIVE-01"])
    candidate = BrowserJourneySuiteCandidate(journeys=[journey])

    validated_suite, outcome = BrowserJourneyValidator.validate(candidate, base_context)

    assert outcome.is_valid is False
    assert validated_suite is None
    codes = [e.code for e in outcome.errors]
    assert "INACTIVE_REQUIREMENT" in codes


# ==============================================================================
# 3. Route Validation & Parameterized Matching Tests
# ==============================================================================

def test_parameterized_route_matching_succeeds(base_context: ValidationContext):
    # Authoritative route is "/projects/{project_id}"
    journey = BrowserJourney(
        journey_id="BJ-PROJ",
        title="Project Details Journey",
        description="Inspect project details page",
        category=JourneyCategory.NAVIGATION,
        target_routes=["/projects/proj-12345"],
        steps=[
            BrowserJourneyStep(
                step_id="s1",
                action=BrowserActionType.NAVIGATE,
                route="/projects/proj-12345",
                description="Navigate to project details",
            )
        ],
    )
    candidate = BrowserJourneySuiteCandidate(journeys=[journey])

    validated_suite, outcome = BrowserJourneyValidator.validate(candidate, base_context)

    assert outcome.is_valid is True
    assert validated_suite is not None
    assert validated_suite.journeys[0].validated_target_routes == ["/projects/proj-12345"]


def test_nonexistent_route_rejected(base_context: ValidationContext):
    journey = BrowserJourney(
        journey_id="BJ-001",
        title="Bad Route Journey",
        description="Navigates to unmapped route",
        category=JourneyCategory.NAVIGATION,
        target_routes=["/unmapped/page"],
        steps=[
            BrowserJourneyStep(
                step_id="s1",
                action=BrowserActionType.NAVIGATE,
                route="/unmapped/page",
                description="Navigate to nonexistent route",
            )
        ],
    )
    candidate = BrowserJourneySuiteCandidate(journeys=[journey])

    validated_suite, outcome = BrowserJourneyValidator.validate(candidate, base_context)

    assert outcome.is_valid is False
    assert validated_suite is None
    codes = [e.code for e in outcome.errors]
    assert "NONEXISTENT_ROUTE" in codes


# ==============================================================================
# 4. Action & Target Validation Tests
# ==============================================================================

def test_css_selector_unbalanced_brackets_rejected(base_context: ValidationContext):
    # We construct with valid Pydantic field then test validator logic
    step = BrowserJourneyStep(
        step_id="s1",
        action=BrowserActionType.CLICK,
        target=BrowserTarget(
            target_type=BrowserTargetType.CSS_SELECTOR,
            value="div[data-testid='btn'",  # Missing closing bracket ']'
        ),
        description="Click element with bad selector",
    )
    journey = BrowserJourney(
        journey_id="BJ-001",
        title="CSS Test Journey",
        description="Journey with malformed CSS",
        category=JourneyCategory.VALIDATION,
        target_routes=["/login"],
        steps=[step],
    )
    candidate = BrowserJourneySuiteCandidate(journeys=[journey])

    validated_suite, outcome = BrowserJourneyValidator.validate(candidate, base_context)

    assert outcome.is_valid is False
    codes = [e.code for e in outcome.errors]
    assert "DANGEROUS_CSS_SELECTOR" in codes


def test_css_selector_injection_pattern_rejected(base_context: ValidationContext):
    step = BrowserJourneyStep(
        step_id="s1",
        action=BrowserActionType.CLICK,
        target=BrowserTarget(
            target_type=BrowserTargetType.CSS_SELECTOR,
            value="div.btn; expression(alert(1))",
        ),
        description="Click element with CSS expression injection",
    )
    journey = BrowserJourney(
        journey_id="BJ-001",
        title="CSS Test Journey",
        description="Journey with CSS expression injection",
        category=JourneyCategory.VALIDATION,
        target_routes=["/login"],
        steps=[step],
    )
    candidate = BrowserJourneySuiteCandidate(journeys=[journey])

    validated_suite, outcome = BrowserJourneyValidator.validate(candidate, base_context)

    assert outcome.is_valid is False
    codes = [e.code for e in outcome.errors]
    assert "DANGEROUS_CSS_SELECTOR" in codes


# ==============================================================================
# 5. Complexity & Bounds Validation Tests
# ==============================================================================

def test_too_many_total_steps_rejected(base_context: ValidationContext):
    # Create journeys with more than 100 total steps
    journeys = []
    for j_idx in range(5):
        steps = [
            BrowserJourneyStep(
                step_id=f"step-{j_idx}-{s_idx}",
                action=BrowserActionType.NAVIGATE,
                route="/login",
                description=f"Step {s_idx}",
            )
            for s_idx in range(25)  # 5 * 25 = 125 total steps > 100
        ]
        journeys.append(
            BrowserJourney(
                journey_id=f"BJ-{j_idx}",
                title=f"Journey {j_idx}",
                description="Long journey test",
                category=JourneyCategory.NAVIGATION,
                target_routes=["/login"],
                steps=steps,
            )
        )

    candidate = BrowserJourneySuiteCandidate(journeys=journeys)

    validated_suite, outcome = BrowserJourneyValidator.validate(candidate, base_context)

    assert outcome.is_valid is False
    codes = [e.code for e in outcome.errors]
    assert "COMPLEXITY_LIMIT_EXCEEDED" in codes


# ==============================================================================
# 6. validate_or_raise Convenience Method Tests
# ==============================================================================

def test_validate_or_raise_raises_on_invalid_candidate(base_context: ValidationContext):
    candidate = BrowserJourneySuiteCandidate(
        suite_name="Empty Suite",
        journeys=[],
    )

    with pytest.raises(BrowserJourneyValidationError) as exc_info:
        BrowserJourneyValidator.validate_or_raise(candidate, base_context)

    assert "failed deterministic validation" in str(exc_info.value)
    assert len(exc_info.value.errors) > 0


def test_validate_or_raise_succeeds_on_valid_candidate(base_context: ValidationContext):
    journey = _make_valid_journey("BJ-001")
    candidate = BrowserJourneySuiteCandidate(journeys=[journey])

    validated_suite = BrowserJourneyValidator.validate_or_raise(candidate, base_context)

    assert isinstance(validated_suite, ValidatedBrowserJourneySuite)
    assert validated_suite.journeys[0].journey_id == "BJ-001"
