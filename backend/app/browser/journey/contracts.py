"""Contracts and Data Models for Deterministic Browser Journey Validation & Coverage.

Phase 11K — Stage 2: Browser Journey Validation & Requirement Coverage Engine
Defines the authoritative validated suite, validation issues, controlled categories,
and requirement coverage reporting structures.

ARCHITECTURAL INVARIANTS:
1. Authoritative Validation: AI proposes (BrowserJourneySuiteCandidate); deterministic backend
   validates and produces ValidatedBrowserJourneySuite.
2. Single-Direction Transformation: Only candidates that pass ALL deterministic validation checks
   can be compiled into a ValidatedBrowserJourneySuite.
3. Deterministic Coverage Calculation: Coverage percentage, covered IDs, and uncovered IDs are
   calculated strictly by Python backend arithmetic; LLM is never the authority.
4. Zero Execution: This module is pure data and validation; it never executes Playwright, Docker,
   or shell commands.
"""

import enum
import uuid
from datetime import datetime, timezone
from typing import Any
from pydantic import BaseModel, ConfigDict, Field

from app.agents.browser_journey.contracts import (
    BrowserActionType,
    BrowserJourneyStep,
    BrowserTarget,
    BrowserTargetType,
    BoundedRequirementInfo,
    BoundedRouteInfo,
    BrowserJourneyGenerationInput,
    BrowserJourneySuiteCandidate,
    JourneyCategory,
    JourneyPriority,
    MAX_DESCRIPTION_LENGTH,
    MAX_JOURNEYS_PER_SUITE,
    MAX_ROUTE_LENGTH,
    MAX_STEP_ID_LENGTH,
    MAX_STEPS_PER_JOURNEY,
    MAX_TITLE_LENGTH,
    MAX_VALUE_LENGTH,
)
from app.agents.failure_analysis.contracts import FailureDiagnosis
from app.browser.contracts import DeterministicBrowserTestDefinition
from app.schemas.browser_testing import BrowserTestRun
from app.schemas.context import ProjectContextResponse
from app.schemas.runtime import ApplicationRuntimeManifest


# ==============================================================================
# 1. Conservative Platform Bounds for Stage 2 Validation
# ==============================================================================

MAX_TOTAL_STEPS_PER_SUITE: int = 100
MAX_PRECONDITION_LENGTH: int = 500
MAX_EXPECTED_OUTCOME_LENGTH: int = 500
MAX_ASSERTION_LENGTH: int = 500
MAX_WAIT_SECONDS: float = 60.0
MIN_WAIT_SECONDS: float = 0.1
MAX_CSS_SELECTOR_LENGTH: int = 200


# ==============================================================================
# 2. Validation Enumerations
# ==============================================================================

class ValidationCategory(str, enum.Enum):
    """Controlled taxonomy of validation rule checks."""
    STRUCTURE = "STRUCTURE"
    REQUIREMENT = "REQUIREMENT"
    ROUTE = "ROUTE"
    ACTION = "ACTION"
    TARGET = "TARGET"
    SECURITY = "SECURITY"
    TRACEABILITY = "TRACEABILITY"
    COMPLEXITY = "COMPLEXITY"
    DUPLICATE = "DUPLICATE"
    CROSS_JOURNEY = "CROSS_JOURNEY"


class ValidationSeverity(str, enum.Enum):
    """Severity level of a validation finding."""
    ERROR = "ERROR"
    WARNING = "WARNING"


# ==============================================================================
# 3. Validation Finding & Outcome Models
# ==============================================================================

class ValidationIssue(BaseModel):
    """Detailed deterministic record of a single validation rule failure or advisory."""
    model_config = ConfigDict(extra="forbid")

    category: ValidationCategory = Field(
        ...,
        description="Controlled category of the validation failure",
    )
    severity: ValidationSeverity = Field(
        default=ValidationSeverity.ERROR,
        description="Severity level (ERROR blocks execution; WARNING is advisory)",
    )
    code: str = Field(
        ...,
        description="Machine-readable deterministic error code (e.g. 'NONEXISTENT_ROUTE')",
    )
    message: str = Field(
        ...,
        description="Human-readable explanation of the validation failure",
    )
    journey_id: str | None = Field(
        default=None,
        description="ID of the journey where the issue was detected, if applicable",
    )
    step_id: str | None = Field(
        default=None,
        description="ID of the step where the issue was detected, if applicable",
    )
    field: str | None = Field(
        default=None,
        description="Name of the offending field, if applicable",
    )


class ValidationOutcome(BaseModel):
    """Comprehensive summary of all deterministic validation checks performed on a candidate suite."""
    model_config = ConfigDict(extra="forbid")

    is_valid: bool = Field(
        ...,
        description="True if no blocking ERROR findings were detected",
    )
    issues: list[ValidationIssue] = Field(
        default_factory=list,
        description="Complete list of all validation findings (errors and warnings)",
    )

    @property
    def errors(self) -> list[ValidationIssue]:
        """All blocking error findings."""
        return [i for i in self.issues if i.severity == ValidationSeverity.ERROR]

    @property
    def warnings(self) -> list[ValidationIssue]:
        """All non-blocking warning findings."""
        return [i for i in self.issues if i.severity == ValidationSeverity.WARNING]

    @property
    def error_messages(self) -> list[str]:
        """Formatted list of error messages for logging and auditing."""
        return [f"[{i.code}] {i.message}" for i in self.errors]


# ==============================================================================
# 4. Requirement Coverage Report
# ==============================================================================

class RequirementCoverageReport(BaseModel):
    """Deterministic requirement coverage metrics calculated from validated journeys."""
    model_config = ConfigDict(extra="forbid")

    total_active_requirements: int = Field(
        ...,
        ge=0,
        description="Total authoritative active requirements in the project scope",
    )
    covered_requirement_count: int = Field(
        ...,
        ge=0,
        description="Count of active requirements covered by at least one validated journey",
    )
    uncovered_requirement_count: int = Field(
        ...,
        ge=0,
        description="Count of active requirements not covered by any validated journey",
    )
    covered_requirement_ids: list[str] = Field(
        default_factory=list,
        description="Sorted list of covered active requirement IDs",
    )
    uncovered_requirement_ids: list[str] = Field(
        default_factory=list,
        description="Sorted list of uncovered active requirement IDs",
    )
    coverage_percentage: float = Field(
        ...,
        ge=0.0,
        le=100.0,
        description="Deterministic coverage percentage: (covered / total) * 100.0",
    )
    journey_count: int = Field(
        ...,
        ge=0,
        description="Total validated journeys contributing to this report",
    )
    requirement_to_journeys_map: dict[str, list[str]] = Field(
        default_factory=dict,
        description="Bidirectional traceability: Requirement ID -> list of Journey IDs",
    )
    journey_to_requirements_map: dict[str, list[str]] = Field(
        default_factory=dict,
        description="Bidirectional traceability: Journey ID -> list of validated Requirement IDs",
    )


# ==============================================================================
# 5. Validated Browser Journey & Suite Models
# ==============================================================================

class ValidatedBrowserJourney(BaseModel):
    """Strongly-typed, deterministically validated browser user journey specification.
    
    Guarantees:
    - Every requirement ID is verified against the canonical project requirements.
    - Every route is verified against the authoritative application route manifest.
    - Every step adheres to action semantics, target bounds, and security rules.
    - Eligible for transformation into executable browser tests in Stage 3.
    """
    model_config = ConfigDict(extra="forbid")

    journey_id: str = Field(
        ...,
        min_length=1,
        max_length=64,
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
    validated_requirement_ids: list[str] = Field(
        default_factory=list,
        description="Authoritatively verified active requirement IDs traced to this journey",
    )
    preconditions: list[str] = Field(
        default_factory=list,
        description="Prerequisites or initial system state requirements",
    )
    validated_target_routes: list[str] = Field(
        default_factory=list,
        description="Authoritatively verified relative application routes traversed in this journey",
    )
    steps: list[BrowserJourneyStep] = Field(
        ...,
        min_length=1,
        max_length=MAX_STEPS_PER_JOURNEY,
        description="Ordered sequence of validated interaction and assertion steps",
    )
    expected_outcomes: list[str] = Field(
        default_factory=list,
        description="Expected business outcomes upon successful journey completion",
    )


class ValidatedBrowserJourneySuite(BaseModel):
    """Authoritative, deterministically validated suite of browser user journeys.
    
    This is the primary artifact produced by Stage 2. It represents verified,
    traceable browser test intent ready for Stage 3 adaptation and execution.
    """
    model_config = ConfigDict(extra="forbid")

    suite_id: str = Field(
        default_factory=lambda: str(uuid.uuid4()),
        description="Deterministic or generated UUID identifying this validated suite",
    )
    project_id: uuid.UUID = Field(
        ...,
        description="Canonical project UUID owning this suite",
    )
    suite_name: str = Field(
        ...,
        max_length=MAX_TITLE_LENGTH,
        description="Human-readable suite name",
    )
    summary: str = Field(
        ...,
        max_length=MAX_DESCRIPTION_LENGTH,
        description="High-level summary of the validated suite",
    )
    journeys: list[ValidatedBrowserJourney] = Field(
        ...,
        min_length=1,
        max_length=MAX_JOURNEYS_PER_SUITE,
        description="List of authoritatively validated user journeys",
    )
    coverage_report: RequirementCoverageReport = Field(
        ...,
        description="Authoritative requirement coverage report calculated from validated journeys",
    )
    validation_timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Timestamp when deterministic validation was completed",
    )
    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Sanitized telemetry and audit metadata",
    )


# ==============================================================================
# 6. Authoritative Validation Context
# ==============================================================================

class ValidationContext(BaseModel):
    """Authoritative project and application context supplied to BrowserJourneyValidator.
    
    Supplies the single sources of truth for:
    - Active project requirements (eligible for coverage)
    - All project requirements (to identify inactive vs hallucinated)
    - Foreign project requirements (to enforce project isolation)
    - Authoritative application routes (manifest or runtime routes)
    """
    model_config = ConfigDict(extra="forbid")

    project_id: uuid.UUID = Field(..., description="Target project UUID")
    active_requirement_ids: set[str] = Field(
        default_factory=set,
        description="Set of active, eligible requirement IDs (UUIDs or canonical titles) for coverage",
    )
    all_project_requirement_ids: set[str] = Field(
        default_factory=set,
        description="Set of all requirement IDs belonging to this project (including archived/deferred)",
    )
    other_project_requirement_ids: set[str] = Field(
        default_factory=set,
        description="Optional set of requirement IDs known to belong to other projects for isolation checks",
    )
    authoritative_routes: list[str] = Field(
        default_factory=list,
        description="Authoritative relative application routes (e.g. ['/', '/login', '/projects/{id}'])",
    )
    runtime_manifest: ApplicationRuntimeManifest | None = Field(
        default=None,
        description="Optional ApplicationRuntimeManifest providing framework defaults and health paths",
    )

    @classmethod
    def from_project_context(
        cls,
        context: ProjectContextResponse,
        authoritative_routes: list[str] | list[BoundedRouteInfo] | None = None,
        runtime_manifest: ApplicationRuntimeManifest | None = None,
        other_project_requirement_ids: set[str] | None = None,
    ) -> "ValidationContext":
        """Construct authoritative ValidationContext from canonical ProjectContextResponse."""
        active_ids: set[str] = set()
        all_ids: set[str] = set()

        if context.requirements:
            for r in context.requirements:
                r_id_str = str(r.id)
                all_ids.add(r_id_str)
                if hasattr(r, "title") and r.title:
                    all_ids.add(r.title)

                # Active rule: not archived and eligible status
                is_arch = getattr(r, "is_archived", False)
                status = getattr(r, "status", None)
                status_val = status.value if hasattr(status, "value") else str(status)

                if not is_arch and status_val in {"DRAFT", "APPROVED", "IMPLEMENTED"}:
                    active_ids.add(r_id_str)
                    if hasattr(r, "title") and r.title:
                        active_ids.add(r.title)

        # Normalize routes
        routes_list: list[str] = []
        if authoritative_routes:
            for r in authoritative_routes:
                if isinstance(r, BoundedRouteInfo):
                    routes_list.append(r.path)
                elif isinstance(r, str):
                    clean = r.strip()
                    if clean:
                        routes_list.append(clean)

        # Include runtime manifest health check path and standard FastAPI routes if applicable
        if runtime_manifest:
            if runtime_manifest.health_check_path and runtime_manifest.health_check_path not in routes_list:
                routes_list.append(runtime_manifest.health_check_path)
            # Default root and docs routes
            for default_r in ["/", "/docs", "/openapi.json"]:
                if default_r not in routes_list:
                    routes_list.append(default_r)

        if not routes_list:
            routes_list = ["/"]

        return cls(
            project_id=context.project.id,
            active_requirement_ids=active_ids,
            all_project_requirement_ids=all_ids,
            other_project_requirement_ids=other_project_requirement_ids or set(),
            authoritative_routes=routes_list,
            runtime_manifest=runtime_manifest,
        )


# ==============================================================================
# 7. Workflow Orchestration Contracts (Stage 4)
# ==============================================================================

class BrowserJourneyWorkflowStatus(str, enum.Enum):
    """Deterministic terminal outcomes of the Browser Journey Generation Workflow."""
    COMPLETED = "COMPLETED"
    GENERATION_FAILED = "WORKFLOW_GENERATION_FAILED"
    VALIDATION_FAILED = "WORKFLOW_VALIDATION_FAILED"
    ADAPTATION_FAILED = "WORKFLOW_ADAPTATION_FAILED"
    BROWSER_EXECUTION_FAILED = "WORKFLOW_BROWSER_EXECUTION_FAILED"


class BrowserJourneyWorkflowResult(BaseModel):
    """Comprehensive structured outcome envelope for a Stage 4 browser journey workflow run."""
    model_config = ConfigDict(arbitrary_types_allowed=True, extra="forbid")

    workflow_execution_id: uuid.UUID = Field(
        ...,
        description="Correlation UUID for this workflow execution run",
    )
    project_id: uuid.UUID = Field(
        ...,
        description="Target project UUID",
    )
    status: BrowserJourneyWorkflowStatus = Field(
        ...,
        description="Final deterministic outcome status",
    )
    stage_reached: str = Field(
        ...,
        description="Deepest pipeline stage reached: 'generation', 'validation', 'adaptation', 'browser_execution', 'completed'",
    )
    generation_input: BrowserJourneyGenerationInput | None = Field(
        default=None,
        description="Authoritative bounded input supplied to the generation agent",
    )
    candidate_suite: BrowserJourneySuiteCandidate | None = Field(
        default=None,
        description="Raw candidate journey suite proposed by BrowserJourneyGenerationAgent",
    )
    validation_outcome: ValidationOutcome | None = Field(
        default=None,
        description="Authoritative deterministic validation findings and outcome",
    )
    validated_suite: ValidatedBrowserJourneySuite | None = Field(
        default=None,
        description="Authoritatively validated browser journey suite if validation succeeded",
    )
    coverage_report: RequirementCoverageReport | None = Field(
        default=None,
        description="Deterministic requirement coverage report from Stage 2",
    )
    test_definitions: list[DeterministicBrowserTestDefinition] | None = Field(
        default=None,
        description="Adapted deterministic browser test definitions ready for container execution",
    )
    browser_test_run: BrowserTestRun | None = Field(
        default=None,
        description="Final browser container test execution result from BrowserTestingService",
    )
    failure_diagnosis: FailureDiagnosis | None = Field(
        default=None,
        description="Optional diagnostic root cause analysis produced by FailureAnalysisAgent if browser tests failed",
    )
    error_message: str | None = Field(
        default=None,
        description="Primary human-readable error description if workflow did not complete successfully",
    )
    errors: list[str] = Field(
        default_factory=list,
        description="Complete list of error messages",
    )
    artifacts: dict[str, Any] = Field(
        default_factory=dict,
        description="Serialized domain artifacts preserving the execution chain",
    )
    started_at: datetime = Field(
        ...,
        description="Timestamp when workflow run commenced",
    )
    completed_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Timestamp when workflow run finished",
    )
    duration_seconds: float = Field(
        default=0.0,
        ge=0.0,
        description="Elapsed duration in seconds",
    )
