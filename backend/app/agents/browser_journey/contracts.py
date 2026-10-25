"""Contracts, Enums, and Conservative Bounds for Browser Journey Generation.

Phase 11K — Stage 1: Browser Journey Contracts
Defines strongly typed, deterministic data models for AI-generated browser test intent.

ARCHITECTURAL INVARIANTS:
1. Candidate representation ONLY: Outputs represent user/test intent (BrowserJourneySuiteCandidate),
   NOT executable Playwright scripts, NOT validated test suites.
2. Zero Playwright code generation: Candidate fields MUST NOT contain executable Playwright,
   Selenium, or JavaScript code (page.goto, locator, await, page.evaluate, etc.).
3. Schema-level security boundaries: Obvious external URLs, dangerous URI schemes (javascript:, file:, data:),
   shell execution patterns, Docker invocations, and credential/secret patterns are rejected at the contract boundary.
4. Relative application routes: All navigation targets and routes must represent relative application paths (e.g. '/login').
"""

import enum
import re
import uuid
from typing import Any
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


# ==============================================================================
# 1. Conservative Platform Bounds
# ==============================================================================

MAX_JOURNEYS_PER_SUITE: int = 15
MAX_STEPS_PER_JOURNEY: int = 30
MAX_STEP_TIMEOUT_SECONDS: float = 60.0
MIN_STEP_TIMEOUT_SECONDS: float = 0.1
MAX_TITLE_LENGTH: int = 150
MAX_DESCRIPTION_LENGTH: int = 1000
MAX_VALUE_LENGTH: int = 500
MAX_ROUTE_LENGTH: int = 250
MAX_STEP_ID_LENGTH: int = 64
MAX_JOURNEY_ID_LENGTH: int = 64


# ==============================================================================
# 2. Security Patterns & Validation Helpers
# ==============================================================================

# Dangerous URI schemes prohibited in all fields
RE_DANGEROUS_SCHEMES = re.compile(
    r"(?i)\b(javascript:|data:|file:|about:|blob:|chrome:|edge:)"
)

# External absolute web URLs prohibited (journeys only target the application under test)
RE_EXTERNAL_URL = re.compile(
    r"(?i)^https?://"
)

# Raw Playwright execution syntax strictly forbidden
RE_RAW_PLAYWRIGHT = re.compile(
    r"(?i)(page\.(goto|click|fill|evaluate|wait_for|locator|type|press|screenshot|content)"
    r"|browser\.(new_page|close)|locator\(|async\s+def\s+test_|import\s+playwright|from\s+playwright"
    r"|await\s+page\.)"
)

# Shell commands, process execution, and Docker invocations forbidden
RE_DANGEROUS_COMMANDS = re.compile(
    r"(?i)\b(docker\s+run|docker\s+exec|docker\s+build|docker-compose|rm\s+-rf|curl\b|wget\b"
    r"|powershell\b|cmd\.exe|bash\b|sh\s+-c|subprocess\b|os\.system|exec\(|system\()"
)

# DOM / script injection forbidden
RE_SCRIPT_INJECTION = re.compile(
    r"(?i)(<script|eval\(|window\.|document\.|setTimeout\(|setInterval\(|Function\()"
)

# Sensitive secrets / keys / credentials detection
RE_SECRET_PATTERNS = re.compile(
    r"(?i)(-+\s*BEGIN\s+(?:[A-Z0-9_-]+\s+)*KEY"
    r"|bearer\s+[a-zA-Z0-9_\-\.]{20,}"
    r"|api[_-]?key\s*[:=]\s*['\"][a-zA-Z0-9_\-]{16,}['\"]"
    r"|secret[_-]?key\s*[:=]"
    r"|access[_-]?token\s*[:=])"
)


def assert_safe_text(value: str, field_name: str) -> None:
    """Validate that a string field contains no prohibited commands, scripts, or secrets."""
    if not value:
        return

    if RE_DANGEROUS_SCHEMES.search(value):
        raise ValueError(f"Prohibited dangerous URI scheme detected in '{field_name}'.")

    if RE_RAW_PLAYWRIGHT.search(value):
        raise ValueError(
            f"Executable Playwright code is strictly forbidden in '{field_name}'. "
            "Journeys must express structured test intent only."
        )

    if RE_DANGEROUS_COMMANDS.search(value):
        raise ValueError(f"Prohibited shell/Docker command detected in '{field_name}'.")

    if RE_SCRIPT_INJECTION.search(value):
        raise ValueError(f"Prohibited script execution syntax detected in '{field_name}'.")

    if RE_SECRET_PATTERNS.search(value):
        raise ValueError(f"Prohibited credential or secret pattern detected in '{field_name}'.")


def assert_safe_route(route: str, field_name: str = "route") -> None:
    """Validate that a route is a safe relative application path."""
    if not route:
        return

    assert_safe_text(route, field_name)

    if RE_EXTERNAL_URL.search(route):
        raise ValueError(
            f"External URLs are prohibited in '{field_name}' ('{route}'). "
            "Journeys must only target relative application paths."
        )

    if not route.startswith("/"):
        raise ValueError(
            f"Invalid route format in '{field_name}' ('{route}'). "
            "Application routes must be relative and begin with '/'."
        )


# ==============================================================================
# 3. Controlled Enumerations
# ==============================================================================

class JourneyCategory(str, enum.Enum):
    """Controlled functional classification of a browser journey."""
    HAPPY_PATH = "HAPPY_PATH"
    VALIDATION = "VALIDATION"
    AUTHENTICATION = "AUTHENTICATION"
    AUTHORIZATION = "AUTHORIZATION"
    CRUD = "CRUD"
    ERROR_HANDLING = "ERROR_HANDLING"
    EDGE_CASE = "EDGE_CASE"
    BUSINESS_RULE = "BUSINESS_RULE"
    NAVIGATION = "NAVIGATION"
    REGRESSION = "REGRESSION"


class JourneyPriority(str, enum.Enum):
    """Controlled descriptive priority for journey reporting.
    
    In accordance with platform invariants, priority is descriptive metadata only
    and never modifies security policies or execution boundaries.
    """
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


class BrowserActionType(str, enum.Enum):
    """Controlled set of permitted browser user interactions and assertions."""
    NAVIGATE = "NAVIGATE"
    CLICK = "CLICK"
    FILL = "FILL"
    SELECT = "SELECT"
    CHECK = "CHECK"
    UNCHECK = "UNCHECK"
    SUBMIT = "SUBMIT"
    ASSERT_TEXT = "ASSERT_TEXT"
    ASSERT_VISIBLE = "ASSERT_VISIBLE"
    ASSERT_URL = "ASSERT_URL"
    ASSERT_ELEMENT = "ASSERT_ELEMENT"
    WAIT = "WAIT"


class BrowserTargetType(str, enum.Enum):
    """Controlled mechanism for targeting elements in the application under test."""
    TEST_ID = "TEST_ID"
    ROLE = "ROLE"
    LABEL = "LABEL"
    NAME = "NAME"
    TEXT = "TEXT"
    CSS_SELECTOR = "CSS_SELECTOR"


# ==============================================================================
# 4. Target & Step Models
# ==============================================================================

class BrowserTarget(BaseModel):
    """Deterministic, controlled browser element target selector."""
    model_config = ConfigDict(extra="forbid")

    target_type: BrowserTargetType = Field(
        ...,
        description="Controlled selector mechanism (TEST_ID, ROLE, LABEL, NAME, TEXT, CSS_SELECTOR)",
    )
    value: str = Field(
        ...,
        min_length=1,
        max_length=MAX_VALUE_LENGTH,
        description="Selector value (e.g. 'submit-btn', 'Submit', '#login-form')",
    )
    description: str | None = Field(
        default=None,
        max_length=MAX_DESCRIPTION_LENGTH,
        description="Optional human-readable description of the element",
    )

    @field_validator("value")
    @classmethod
    def validate_target_value(cls, v: str) -> str:
        clean = v.strip()
        assert_safe_text(clean, "target.value")
        return clean

    @field_validator("description")
    @classmethod
    def validate_target_description(cls, v: str | None) -> str | None:
        if v:
            clean = v.strip()
            assert_safe_text(clean, "target.description")
            return clean
        return v


class BrowserJourneyStep(BaseModel):
    """Strongly-typed individual browser journey interaction or assertion step."""
    model_config = ConfigDict(extra="forbid")

    step_id: str = Field(
        ...,
        min_length=1,
        max_length=MAX_STEP_ID_LENGTH,
        description="Deterministic step identifier (e.g. 'step-1', 'S01')",
    )
    action: BrowserActionType = Field(
        ...,
        description="Controlled browser interaction or assertion type",
    )
    target: BrowserTarget | None = Field(
        default=None,
        description="Target element specification (required for CLICK, FILL, SELECT, etc.)",
    )
    value: str | None = Field(
        default=None,
        max_length=MAX_VALUE_LENGTH,
        description="Input test value (FILL, SELECT) or expected text (ASSERT_TEXT)",
    )
    route: str | None = Field(
        default=None,
        max_length=MAX_ROUTE_LENGTH,
        description="Target relative route for NAVIGATE or ASSERT_URL (e.g. '/login')",
    )
    assertion: str | None = Field(
        default=None,
        max_length=MAX_DESCRIPTION_LENGTH,
        description="Optional assertion rule or human-readable expectation description",
    )
    timeout_seconds: float = Field(
        default=5.0,
        ge=MIN_STEP_TIMEOUT_SECONDS,
        le=MAX_STEP_TIMEOUT_SECONDS,
        description="Bounded timeout in seconds for this step execution",
    )
    description: str = Field(
        ...,
        min_length=3,
        max_length=MAX_DESCRIPTION_LENGTH,
        description="Human-readable explanation of what this step does",
    )

    @field_validator("step_id")
    @classmethod
    def validate_step_id(cls, v: str) -> str:
        clean = v.strip()
        assert_safe_text(clean, "step_id")
        return clean

    @field_validator("value")
    @classmethod
    def validate_value(cls, v: str | None) -> str | None:
        if v is not None:
            clean = v.strip()
            assert_safe_text(clean, "value")
            return clean
        return v

    @field_validator("route")
    @classmethod
    def validate_route(cls, v: str | None) -> str | None:
        if v is not None:
            clean = v.strip()
            assert_safe_route(clean, "route")
            return clean
        return v

    @field_validator("assertion")
    @classmethod
    def validate_assertion(cls, v: str | None) -> str | None:
        if v is not None:
            clean = v.strip()
            assert_safe_text(clean, "assertion")
            return clean
        return v

    @field_validator("description")
    @classmethod
    def validate_description(cls, v: str) -> str:
        clean = v.strip()
        assert_safe_text(clean, "description")
        return clean

    @model_validator(mode="after")
    def validate_action_specific_requirements(self) -> "BrowserJourneyStep":
        """Deterministic validation of action-specific field completeness."""
        action = self.action

        if action == BrowserActionType.NAVIGATE:
            if not self.route:
                raise ValueError("NAVIGATE step requires a valid relative 'route' (e.g. '/dashboard').")

        elif action in (BrowserActionType.CLICK, BrowserActionType.CHECK, BrowserActionType.UNCHECK, BrowserActionType.SUBMIT):
            if not self.target:
                raise ValueError(f"{action.value} step requires a valid 'target'.")

        elif action in (BrowserActionType.FILL, BrowserActionType.SELECT):
            if not self.target:
                raise ValueError(f"{action.value} step requires a valid 'target'.")
            if self.value is None:
                raise ValueError(f"{action.value} step requires a 'value'.")

        elif action == BrowserActionType.ASSERT_TEXT:
            if not self.target:
                raise ValueError("ASSERT_TEXT step requires a valid 'target'.")
            if self.value is None and self.assertion is None:
                raise ValueError("ASSERT_TEXT step requires either 'value' or 'assertion' to verify text.")

        elif action in (BrowserActionType.ASSERT_VISIBLE, BrowserActionType.ASSERT_ELEMENT):
            if not self.target:
                raise ValueError(f"{action.value} step requires a valid 'target'.")

        elif action == BrowserActionType.ASSERT_URL:
            if not self.route and not self.value:
                raise ValueError("ASSERT_URL step requires 'route' or 'value' for expected URL verification.")

        elif action == BrowserActionType.WAIT:
            if self.timeout_seconds <= 0:
                raise ValueError("WAIT step requires positive 'timeout_seconds'.")

        return self


# ==============================================================================
# 5. Journey Model
# ==============================================================================

class BrowserJourney(BaseModel):
    """Strongly-typed multi-step browser user journey specification."""
    model_config = ConfigDict(extra="forbid")

    journey_id: str = Field(
        ...,
        min_length=1,
        max_length=MAX_JOURNEY_ID_LENGTH,
        description="Unique identifier for the journey (e.g. 'BJ-001')",
    )
    title: str = Field(
        ...,
        min_length=3,
        max_length=MAX_TITLE_LENGTH,
        description="Human-readable title of the journey",
    )
    description: str = Field(
        ...,
        min_length=5,
        max_length=MAX_DESCRIPTION_LENGTH,
        description="Detailed description of the user journey scenario",
    )
    category: JourneyCategory = Field(
        ...,
        description="Controlled functional classification of the journey",
    )
    priority: JourneyPriority = Field(
        default=JourneyPriority.MEDIUM,
        description="Controlled descriptive priority (HIGH, MEDIUM, LOW)",
    )
    requirement_ids: list[str] = Field(
        default_factory=list,
        description="Canonical project requirement IDs traced to this journey",
    )
    preconditions: list[str] = Field(
        default_factory=list,
        description="Prerequisites or initial system state requirements",
    )
    target_routes: list[str] = Field(
        default_factory=list,
        description="List of relative application routes traversed in this journey",
    )
    steps: list[BrowserJourneyStep] = Field(
        ...,
        min_length=1,
        description="Ordered sequence of browser interaction and assertion steps",
    )
    expected_outcomes: list[str] = Field(
        default_factory=list,
        description="Expected business outcomes upon successful journey completion",
    )

    @field_validator("journey_id")
    @classmethod
    def validate_journey_id(cls, v: str) -> str:
        clean = v.strip()
        assert_safe_text(clean, "journey_id")
        return clean

    @field_validator("title")
    @classmethod
    def validate_title(cls, v: str) -> str:
        clean = v.strip()
        assert_safe_text(clean, "title")
        return clean

    @field_validator("description")
    @classmethod
    def validate_description(cls, v: str) -> str:
        clean = v.strip()
        assert_safe_text(clean, "description")
        return clean

    @field_validator("target_routes")
    @classmethod
    def validate_target_routes(cls, routes: list[str]) -> list[str]:
        cleaned_routes = []
        for r in routes:
            clean = r.strip()
            assert_safe_route(clean, "target_routes")
            cleaned_routes.append(clean)
        return cleaned_routes

    @field_validator("preconditions", "expected_outcomes", "requirement_ids")
    @classmethod
    def validate_string_lists(cls, items: list[str]) -> list[str]:
        cleaned = []
        for item in items:
            clean = item.strip()
            assert_safe_text(clean, "list_item")
            cleaned.append(clean)
        return cleaned

    @field_validator("steps")
    @classmethod
    def validate_steps_length_and_uniqueness(cls, steps: list[BrowserJourneyStep]) -> list[BrowserJourneyStep]:
        if len(steps) > MAX_STEPS_PER_JOURNEY:
            raise ValueError(
                f"Journey exceeds maximum step bound of {MAX_STEPS_PER_JOURNEY} (received {len(steps)})."
            )
        step_ids: set[str] = set()
        for s in steps:
            if s.step_id in step_ids:
                raise ValueError(f"Duplicate step_id '{s.step_id}' found in journey.")
            step_ids.add(s.step_id)
        return steps


# ==============================================================================
# 6. Candidate Suite Schema (Agent Output)
# ==============================================================================

class BrowserJourneySuiteCandidate(BaseModel):
    """Raw candidate browser journey suite returned by LLM before deterministic Stage 2 validation."""
    model_config = ConfigDict(extra="ignore")

    suite_name: str = Field(
        default="AI-Generated Browser Journey Suite",
        max_length=MAX_TITLE_LENGTH,
        description="Human-readable name of the candidate suite",
    )
    summary: str = Field(
        default="Candidate browser journeys generated from bounded project context.",
        max_length=MAX_DESCRIPTION_LENGTH,
        description="High-level summary of the generated journey suite",
    )
    journeys: list[BrowserJourney] = Field(
        default_factory=list,
        description="List of candidate browser journeys",
    )
    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Generation metadata and telemetry",
    )

    @field_validator("suite_name")
    @classmethod
    def validate_suite_name(cls, v: str) -> str:
        clean = v.strip()
        assert_safe_text(clean, "suite_name")
        return clean

    @field_validator("summary")
    @classmethod
    def validate_summary(cls, v: str) -> str:
        clean = v.strip()
        assert_safe_text(clean, "summary")
        return clean

    @model_validator(mode="after")
    def validate_suite_candidate(self) -> "BrowserJourneySuiteCandidate":
        if len(self.journeys) > MAX_JOURNEYS_PER_SUITE:
            raise ValueError(
                f"Candidate suite exceeds maximum journey bound of {MAX_JOURNEYS_PER_SUITE} "
                f"(received {len(self.journeys)})."
            )
        journey_ids: set[str] = set()
        for j in self.journeys:
            if j.journey_id in journey_ids:
                raise ValueError(f"Duplicate journey_id '{j.journey_id}' found in candidate suite.")
            journey_ids.add(j.journey_id)
        return self


# ==============================================================================
# 7. Bounded Input Context Schemas
# ==============================================================================

class BoundedRequirementInfo(BaseModel):
    """Bounded, sanitized requirement context for journey generation."""
    model_config = ConfigDict(extra="forbid")

    id: str = Field(..., description="Canonical requirement ID or UUID")
    title: str = Field(..., description="Requirement title")
    description: str = Field(default="", description="Sanitized requirement description")
    category: str | None = Field(default=None, description="Requirement category")


class BoundedRouteInfo(BaseModel):
    """Bounded, sanitized application route context."""
    model_config = ConfigDict(extra="forbid")

    path: str = Field(..., description="Relative application route path (e.g. '/dashboard')")
    method: str = Field(default="GET", description="HTTP method")
    name: str | None = Field(default=None, description="Route name or label")
    description: str | None = Field(default=None, description="Route description or purpose")


class BrowserJourneyGenerationInput(BaseModel):
    """Authoritative, bounded input provided to BrowserJourneyGenerationAgent.
    
    Contains strictly bounded information required to generate meaningful browser journeys:
    - Active requirements and descriptions
    - Discovered application routes
    - Architecture summary and relevant component names
    - Bounded file manifest
    - DevelopmentVersion identity
    
    DO NOT pass: API keys, credentials, secrets, Docker configuration, container IDs,
    Docker network IDs, host filesystem paths, or internal infrastructure parameters.
    """
    model_config = ConfigDict(extra="forbid")

    project_id: uuid.UUID = Field(..., description="Canonical project UUID")
    project_name: str = Field(default="Application Under Test", description="Project display name")
    development_version_id: uuid.UUID | None = Field(
        default=None,
        description="DevelopmentVersion UUID if version-aware",
    )
    version_number: int | None = Field(
        default=None,
        description="DevelopmentVersion sequence number if version-aware",
    )
    requirements: list[BoundedRequirementInfo] = Field(
        default_factory=list,
        description="Active project requirements",
    )
    routes: list[BoundedRouteInfo] = Field(
        default_factory=list,
        description="Discovered or declared application routes",
    )
    architecture_components: list[str] = Field(
        default_factory=list,
        description="Relevant architecture component names",
    )
    file_manifest: list[str] = Field(
        default_factory=list,
        description="Bounded list of frontend / relevant application files",
    )
    max_journeys: int = Field(
        default=5,
        ge=1,
        le=MAX_JOURNEYS_PER_SUITE,
        description="Target number of journeys to generate",
    )
    target_categories: list[JourneyCategory] = Field(
        default_factory=lambda: list(JourneyCategory),
        description="Allowed or requested journey categories",
    )
