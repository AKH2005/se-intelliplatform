"""Unit Tests for Phase 11K Stage 1 Browser Journey Contracts & Security Validation.

Tests structural constraints, controlled enumerations, action-specific completeness,
and schema-level security rejection of dangerous URI schemes, external URLs, shell commands,
raw Playwright code snippets, and secrets.
"""

import pytest
from pydantic import ValidationError

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
    MAX_JOURNEYS_PER_SUITE,
    MAX_STEPS_PER_JOURNEY,
)


# ==============================================================================
# 1. Controlled Enumerations Tests
# ==============================================================================

def test_all_journey_categories_supported():
    expected_categories = {
        "HAPPY_PATH",
        "VALIDATION",
        "AUTHENTICATION",
        "AUTHORIZATION",
        "CRUD",
        "ERROR_HANDLING",
        "EDGE_CASE",
        "BUSINESS_RULE",
        "NAVIGATION",
        "REGRESSION",
    }
    actual_categories = {c.value for c in JourneyCategory}
    assert actual_categories == expected_categories


def test_all_journey_priorities_supported():
    expected_priorities = {"HIGH", "MEDIUM", "LOW"}
    actual_priorities = {p.value for p in JourneyPriority}
    assert actual_priorities == expected_priorities


def test_all_browser_action_types_supported():
    expected_actions = {
        "NAVIGATE",
        "CLICK",
        "FILL",
        "SELECT",
        "CHECK",
        "UNCHECK",
        "SUBMIT",
        "ASSERT_TEXT",
        "ASSERT_VISIBLE",
        "ASSERT_URL",
        "ASSERT_ELEMENT",
        "WAIT",
    }
    actual_actions = {a.value for a in BrowserActionType}
    assert actual_actions == expected_actions


def test_all_browser_target_types_supported():
    expected_targets = {
        "TEST_ID",
        "ROLE",
        "LABEL",
        "NAME",
        "TEXT",
        "CSS_SELECTOR",
    }
    actual_targets = {t.value for t in BrowserTargetType}
    assert actual_targets == expected_targets


# ==============================================================================
# 2. Valid Contract Creation Tests
# ==============================================================================

def test_valid_browser_target():
    target = BrowserTarget(
        target_type=BrowserTargetType.TEST_ID,
        value="login-submit-button",
        description="Submit button on login form",
    )
    assert target.target_type == BrowserTargetType.TEST_ID
    assert target.value == "login-submit-button"
    assert target.description == "Submit button on login form"


def test_valid_browser_journey_steps():
    # 1. NAVIGATE step
    s1 = BrowserJourneyStep(
        step_id="s1",
        action=BrowserActionType.NAVIGATE,
        route="/login",
        description="Navigate to login page",
    )
    assert s1.action == BrowserActionType.NAVIGATE
    assert s1.route == "/login"

    # 2. FILL step
    s2 = BrowserJourneyStep(
        step_id="s2",
        action=BrowserActionType.FILL,
        target=BrowserTarget(target_type=BrowserTargetType.TEST_ID, value="email-input"),
        value="test@example.com",
        description="Enter test email",
    )
    assert s2.action == BrowserActionType.FILL
    assert s2.value == "test@example.com"

    # 3. CLICK step
    s3 = BrowserJourneyStep(
        step_id="s3",
        action=BrowserActionType.CLICK,
        target=BrowserTarget(target_type=BrowserTargetType.ROLE, value="button"),
        description="Click login button",
    )
    assert s3.action == BrowserActionType.CLICK

    # 4. ASSERT_TEXT step
    s4 = BrowserJourneyStep(
        step_id="s4",
        action=BrowserActionType.ASSERT_TEXT,
        target=BrowserTarget(target_type=BrowserTargetType.TEST_ID, value="welcome-banner"),
        value="Welcome back!",
        description="Assert welcome message is displayed",
    )
    assert s4.action == BrowserActionType.ASSERT_TEXT
    assert s4.value == "Welcome back!"

    # 5. WAIT step
    s5 = BrowserJourneyStep(
        step_id="s5",
        action=BrowserActionType.WAIT,
        timeout_seconds=2.0,
        description="Wait for transition",
    )
    assert s5.action == BrowserActionType.WAIT
    assert s5.timeout_seconds == 2.0


def test_valid_browser_journey():
    journey = BrowserJourney(
        journey_id="BJ-001",
        title="User Authentication Happy Path",
        description="Verifies a registered user can sign in and reach the dashboard.",
        category=JourneyCategory.AUTHENTICATION,
        priority=JourneyPriority.HIGH,
        requirement_ids=["REQ-AUTH-01"],
        preconditions=["User is registered in test database"],
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
                target=BrowserTarget(target_type=BrowserTargetType.NAME, value="username"),
                value="test@example.com",
                description="Type username",
            ),
            BrowserJourneyStep(
                step_id="step-3",
                action=BrowserActionType.CLICK,
                target=BrowserTarget(target_type=BrowserTargetType.TEST_ID, value="login-btn"),
                description="Click submit",
            ),
            BrowserJourneyStep(
                step_id="step-4",
                action=BrowserActionType.ASSERT_URL,
                route="/dashboard",
                description="Verify redirected to dashboard",
            ),
        ],
        expected_outcomes=["User session is active", "Dashboard is visible"],
    )
    assert journey.journey_id == "BJ-001"
    assert len(journey.steps) == 4
    assert journey.category == JourneyCategory.AUTHENTICATION
    assert journey.priority == JourneyPriority.HIGH


def test_valid_candidate_suite():
    journey = BrowserJourney(
        journey_id="BJ-001",
        title="Homepage Navigation",
        description="Verify homepage loads correctly",
        category=JourneyCategory.NAVIGATION,
        priority=JourneyPriority.MEDIUM,
        target_routes=["/"],
        steps=[
            BrowserJourneyStep(
                step_id="s1",
                action=BrowserActionType.NAVIGATE,
                route="/",
                description="Navigate to root",
            ),
            BrowserJourneyStep(
                step_id="s2",
                action=BrowserActionType.ASSERT_VISIBLE,
                target=BrowserTarget(target_type=BrowserTargetType.TEST_ID, value="main-nav"),
                description="Verify navigation bar is visible",
            ),
        ],
    )
    suite = BrowserJourneySuiteCandidate(
        suite_name="Smoke Suite",
        summary="Basic sanity journeys",
        journeys=[journey],
    )
    assert suite.suite_name == "Smoke Suite"
    assert len(suite.journeys) == 1
    assert suite.journeys[0].journey_id == "BJ-001"


# ==============================================================================
# 3. Malformed Contract & Invariant Rejection Tests
# ==============================================================================

def test_invalid_category_rejected():
    with pytest.raises(ValidationError):
        BrowserJourney(
            journey_id="BJ-001",
            title="Invalid Category Journey",
            description="Testing invalid category string",
            category="CUSTOM_UNSUPPORTED_CATEGORY",  # type: ignore
            steps=[
                BrowserJourneyStep(
                    step_id="s1",
                    action=BrowserActionType.NAVIGATE,
                    route="/",
                    description="Navigate",
                )
            ],
        )


def test_invalid_priority_rejected():
    with pytest.raises(ValidationError):
        BrowserJourney(
            journey_id="BJ-001",
            title="Invalid Priority Journey",
            description="Testing invalid priority",
            category=JourneyCategory.HAPPY_PATH,
            priority="CRITICAL_BLOCKER",  # type: ignore
            steps=[
                BrowserJourneyStep(
                    step_id="s1",
                    action=BrowserActionType.NAVIGATE,
                    route="/",
                    description="Navigate",
                )
            ],
        )


def test_invalid_action_rejected():
    with pytest.raises(ValidationError):
        BrowserJourneyStep(
            step_id="s1",
            action="ARBITRARY_ACTION",  # type: ignore
            description="Unsupported action",
        )


def test_invalid_target_type_rejected():
    with pytest.raises(ValidationError):
        BrowserTarget(
            target_type="XPATH_ARBITRARY",  # type: ignore
            value="//div[@class='btn']",
        )


def test_navigate_step_missing_route_rejected():
    with pytest.raises(ValidationError) as exc:
        BrowserJourneyStep(
            step_id="s1",
            action=BrowserActionType.NAVIGATE,
            description="Navigate without route",
        )
    assert "NAVIGATE step requires a valid relative 'route'" in str(exc.value)


def test_click_step_missing_target_rejected():
    with pytest.raises(ValidationError) as exc:
        BrowserJourneyStep(
            step_id="s1",
            action=BrowserActionType.CLICK,
            description="Click without target",
        )
    assert "CLICK step requires a valid 'target'" in str(exc.value)


def test_fill_step_missing_value_rejected():
    with pytest.raises(ValidationError) as exc:
        BrowserJourneyStep(
            step_id="s1",
            action=BrowserActionType.FILL,
            target=BrowserTarget(target_type=BrowserTargetType.TEST_ID, value="input-box"),
            description="Fill without value",
        )
    assert "FILL step requires a 'value'" in str(exc.value)


def test_assert_text_missing_value_and_assertion_rejected():
    with pytest.raises(ValidationError) as exc:
        BrowserJourneyStep(
            step_id="s1",
            action=BrowserActionType.ASSERT_TEXT,
            target=BrowserTarget(target_type=BrowserTargetType.TEST_ID, value="banner"),
            description="Assert text without expectation",
        )
    assert "ASSERT_TEXT step requires either 'value' or 'assertion'" in str(exc.value)


def test_journey_empty_steps_rejected():
    with pytest.raises(ValidationError):
        BrowserJourney(
            journey_id="BJ-001",
            title="Empty Journey",
            description="Journey without steps",
            category=JourneyCategory.NAVIGATION,
            steps=[],
        )


def test_journey_duplicate_step_ids_rejected():
    with pytest.raises(ValidationError) as exc:
        BrowserJourney(
            journey_id="BJ-001",
            title="Duplicate Step IDs",
            description="Journey with duplicated step ID",
            category=JourneyCategory.NAVIGATION,
            steps=[
                BrowserJourneyStep(
                    step_id="step-1",
                    action=BrowserActionType.NAVIGATE,
                    route="/",
                    description="First step",
                ),
                BrowserJourneyStep(
                    step_id="step-1",
                    action=BrowserActionType.CLICK,
                    target=BrowserTarget(target_type=BrowserTargetType.TEST_ID, value="btn"),
                    description="Second step with duplicate ID",
                ),
            ],
        )
    assert "Duplicate step_id 'step-1' found in journey" in str(exc.value)


def test_candidate_suite_duplicate_journey_ids_rejected():
    j1 = BrowserJourney(
        journey_id="DUPE-ID",
        title="Journey 1",
        description="First journey",
        category=JourneyCategory.HAPPY_PATH,
        steps=[
            BrowserJourneyStep(
                step_id="s1",
                action=BrowserActionType.NAVIGATE,
                route="/",
                description="Step 1",
            )
        ],
    )
    j2 = BrowserJourney(
        journey_id="DUPE-ID",
        title="Journey 2",
        description="Second journey with dupe ID",
        category=JourneyCategory.VALIDATION,
        steps=[
            BrowserJourneyStep(
                step_id="s1",
                action=BrowserActionType.NAVIGATE,
                route="/login",
                description="Step 1",
            )
        ],
    )
    with pytest.raises(ValidationError) as exc:
        BrowserJourneySuiteCandidate(
            suite_name="Dupe Suite",
            journeys=[j1, j2],
        )
    assert "Duplicate journey_id 'DUPE-ID' found in candidate suite" in str(exc.value)


# ==============================================================================
# 4. Security Boundaries Tests
# ==============================================================================

@pytest.mark.parametrize(
    "unsafe_route",
    [
        "javascript:alert(1)",
        "data:text/html,<script>alert(1)</script>",
        "file:///etc/passwd",
        "about:blank",
        "http://external-evil.com/login",
        "https://google.com",
        "relative-without-leading-slash",
    ],
)
def test_unsafe_routes_rejected(unsafe_route: str):
    with pytest.raises(ValidationError):
        BrowserJourneyStep(
            step_id="s1",
            action=BrowserActionType.NAVIGATE,
            route=unsafe_route,
            description="Dangerous route test",
        )


@pytest.mark.parametrize(
    "raw_playwright_snippet",
    [
        "page.goto('/login')",
        "await page.click('#submit')",
        "page.fill('#email', 'val')",
        "page.evaluate('() => window.token')",
        "locator('#btn').click()",
        "browser.new_page()",
        "async def test_something():",
        "import playwright",
        "from playwright.sync_api import sync_playwright",
    ],
)
def test_raw_playwright_code_rejected_in_fields(raw_playwright_snippet: str):
    # In target value
    with pytest.raises(ValidationError) as exc1:
        BrowserTarget(
            target_type=BrowserTargetType.CSS_SELECTOR,
            value=f"#btn; {raw_playwright_snippet}",
        )
    assert "Executable Playwright code is strictly forbidden" in str(exc1.value)

    # In step description
    with pytest.raises(ValidationError) as exc2:
        BrowserJourneyStep(
            step_id="s1",
            action=BrowserActionType.NAVIGATE,
            route="/login",
            description=f"Executing {raw_playwright_snippet}",
        )
    assert "Executable Playwright code is strictly forbidden" in str(exc2.value)


@pytest.mark.parametrize(
    "shell_or_docker_command",
    [
        "docker run -d -p 80:80 nginx",
        "docker exec container_id ls",
        "rm -rf /",
        "curl http://169.254.169.254/metadata",
        "powershell Get-Process",
        "bash -c 'whoami'",
        "subprocess.Popen(['ls'])",
    ],
)
def test_shell_and_docker_commands_rejected(shell_or_docker_command: str):
    with pytest.raises(ValidationError) as exc:
        BrowserJourneyStep(
            step_id="s1",
            action=BrowserActionType.NAVIGATE,
            route="/login",
            description=f"Run command: {shell_or_docker_command}",
        )
    assert "Prohibited shell/Docker command detected" in str(exc.value)


@pytest.mark.parametrize(
    "script_injection",
    [
        "<script>alert(document.cookie)</script>",
        "eval('fetch(/steal)')",
        "window.localStorage.getItem('token')",
        "document.location='http://evil.com'",
    ],
)
def test_script_injections_rejected(script_injection: str):
    with pytest.raises(ValidationError) as exc:
        BrowserTarget(
            target_type=BrowserTargetType.TEXT,
            value=script_injection,
        )
    assert "Prohibited script execution syntax detected" in str(exc.value)


@pytest.mark.parametrize(
    "secret_string",
    [
        "-----BEGIN RSA PRIVATE KEY-----\nMIIEowIBAAKCAQEA...",
        "bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
        "api_key = 'abcdef1234567890abcdef1234567890'",
    ],
)
def test_secrets_and_private_keys_rejected(secret_string: str):
    with pytest.raises(ValidationError) as exc:
        BrowserJourneyStep(
            step_id="s1",
            action=BrowserActionType.FILL,
            target=BrowserTarget(target_type=BrowserTargetType.TEST_ID, value="key-input"),
            value=secret_string,
            description="Fill with secret",
        )
    assert "Prohibited credential or secret pattern detected" in str(exc.value)


# ==============================================================================
# 5. Input Context Contract Tests
# ==============================================================================

def test_browser_journey_generation_input_completeness():
    import uuid

    proj_id = uuid.uuid4()
    gen_input = BrowserJourneyGenerationInput(
        project_id=proj_id,
        project_name="Inventory App",
        version_number=1,
        requirements=[
            BoundedRequirementInfo(
                id="REQ-001",
                title="Product List",
                description="Users can view inventory items",
                category="FUNCTIONAL",
            )
        ],
        routes=[
            BoundedRouteInfo(path="/products", method="GET", name="Product List"),
            BoundedRouteInfo(path="/products/new", method="POST", name="Create Product"),
        ],
        architecture_components=["InventoryService", "WebFrontend"],
        file_manifest=["src/pages/Products.tsx", "src/pages/CreateProduct.tsx"],
        max_journeys=3,
        target_categories=[JourneyCategory.HAPPY_PATH, JourneyCategory.CRUD],
    )

    assert gen_input.project_id == proj_id
    assert len(gen_input.requirements) == 1
    assert len(gen_input.routes) == 2
    assert gen_input.max_journeys == 3
    assert len(gen_input.target_categories) == 2
