"""Domain Contracts and Data Models for Selective Regression Planning (Phase 11L Stage 4).

Defines regression plan models, plan modes, test selection reasons, test provenance,
and deterministic execution safety semantics.
"""

from datetime import datetime, timezone
from enum import Enum
from typing import Any
from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.testing.inventory.contracts import TestTier


class RegressionPlanMode(str, Enum):
    """Execution scope mode of a deterministic regression plan."""

    __test__ = False

    SELECTIVE = "SELECTIVE"
    BROAD = "BROAD"
    FULL = "FULL"


class PlanSelectionReason(str, Enum):
    """Deterministic rationale explaining why a specific test is selected in the plan."""

    __test__ = False

    DIRECT_CHANGE = "DIRECT_CHANGE"
    DEPENDENCY_IMPACT = "DEPENDENCY_IMPACT"
    REQUIREMENT_PROTECTION = "REQUIREMENT_PROTECTION"
    BROWSER_ROUTE_IMPACT = "BROWSER_ROUTE_IMPACT"
    CONSERVATIVE_FALLBACK = "CONSERVATIVE_FALLBACK"
    COVERAGE_PROTECTION = "COVERAGE_PROTECTION"
    FULL_REGRESSION = "FULL_REGRESSION"
    BROAD_REGRESSION = "BROAD_REGRESSION"


class SelectedTest(BaseModel):
    """Deterministic provenance record for a test selected in a regression plan."""

    __test__ = False
    model_config = ConfigDict(extra="forbid")

    test_id: str = Field(
        ...,
        min_length=1,
        max_length=200,
        description="Deterministic identifier of the test from UnifiedTestInventory",
    )
    tier: TestTier = Field(
        ...,
        description="TestTier classification (UNIT, AI_TEST, BROWSER_SMOKE, BROWSER_JOURNEY)",
    )
    name: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description="Human-readable title or test function name",
    )
    source_reference: str = Field(
        ...,
        min_length=1,
        max_length=500,
        description="Source code location, pytest node ID, or route reference",
    )
    selection_reasons: list[PlanSelectionReason] = Field(
        default_factory=list,
        description="Sorted list of deterministic reasons why this test was selected",
    )
    affected_requirements: list[str] = Field(
        default_factory=list,
        description="Sorted list of affected requirements authoritatively protected by this test",
    )
    affected_files: list[str] = Field(
        default_factory=list,
        description="Sorted list of impacted files associated with this test",
    )
    selection_scope: str = Field(
        ...,
        description="Primary selection category (DIRECT, DEPENDENCY, REQUIREMENT, CONSERVATIVE, BROADENING, FULL)",
    )
    target_file: str | None = Field(
        default=None,
        description="Project-relative path of the target source file, if known",
    )
    target_symbol: str | None = Field(
        default=None,
        description="Symbol targeted by this test, if known",
    )


class RegressionPlan(BaseModel):
    """Authoritative, deterministic regression plan ready for Stage 5 execution consumption."""

    __test__ = False
    model_config = ConfigDict(extra="forbid")

    project_id: str = Field(
        ...,
        description="Canonical project UUID string owning this plan",
    )
    mode: RegressionPlanMode = Field(
        ...,
        description="Selected plan scope mode (SELECTIVE, BROAD, FULL)",
    )
    base_version_id: str | None = Field(
        default=None,
        description="Optional base version ID compared against",
    )
    target_version_id: str | None = Field(
        default=None,
        description="Optional target version ID being planned",
    )
    inventory_id: str = Field(
        ...,
        min_length=5,
        max_length=100,
        description="Deterministic identifier of the source UnifiedTestInventory",
    )
    selected_test_ids: list[str] = Field(
        default_factory=list,
        description="Sorted list of all unique test IDs selected in this plan",
    )
    selected_tests: list[SelectedTest] = Field(
        default_factory=list,
        description="Deterministic list of SelectedTest objects ordered by tier and test_id",
    )
    selected_tests_by_tier: dict[str, list[str]] = Field(
        default_factory=dict,
        description="TestTier value -> sorted list of selected test IDs",
    )
    selected_requirement_ids: list[str] = Field(
        default_factory=list,
        description="Sorted union of all authoritative requirement IDs linked to selected tests",
    )
    affected_requirement_ids: list[str] = Field(
        default_factory=list,
        description="Sorted list of active requirements impacted according to ChangeImpactReport",
    )
    protected_requirement_ids: list[str] = Field(
        default_factory=list,
        description="Sorted list of affected requirements covered by at least one selected test",
    )
    uncovered_affected_requirement_ids: list[str] = Field(
        default_factory=list,
        description="Coverage gaps: affected requirements that have no authoritative test protection in inventory",
    )
    unrelated_requirement_ids: list[str] = Field(
        default_factory=list,
        description="Active requirements completely unaffected and not selected in this plan",
    )
    selection_reasons_by_test: dict[str, list[PlanSelectionReason]] = Field(
        default_factory=dict,
        description="test_id -> sorted list of deterministic selection reasons",
    )
    broadening_reasons: list[str] = Field(
        default_factory=list,
        description="Deterministic reasons explaining why BROAD or FULL mode was selected/triggered",
    )
    requires_broader_regression: bool = Field(
        default=False,
        description="Flag indicating if underlying change impact flagged uncertainty requiring broader regression",
    )
    is_execution_safe: bool = Field(
        ...,
        description="Deterministic safety predicate: True if the plan is safe for execution according to its mode",
    )
    plan_warnings: list[str] = Field(
        default_factory=list,
        description="Sorted list of safety or coverage gap warnings",
    )
    total_inventory_tests: int = Field(
        default=0,
        ge=0,
        description="Total count of valid tests in source inventory",
    )
    unselected_test_count: int = Field(
        default=0,
        ge=0,
        description="Count of tests in inventory excluded from this plan",
    )
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Timestamp when plan was generated",
    )
    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Contextual telemetry and analysis audit annotations",
    )

    @field_validator("project_id", mode="before")
    @classmethod
    def normalize_project_id(cls, v: Any) -> str:
        return str(v).strip().lower()

    # Query Helper Methods
    def is_test_selected(self, test_id: str) -> bool:
        """Check if a test ID is selected in the plan."""
        return test_id in self.selected_test_ids

    def get_selected_tests_for_tier(self, tier: TestTier | str) -> list[SelectedTest]:
        """Retrieve all SelectedTest records belonging to a specific TestTier."""
        tier_key = tier.value if isinstance(tier, TestTier) else str(tier)
        return [t for t in self.selected_tests if t.tier.value == tier_key]

    def get_reasons_for_test(self, test_id: str) -> list[PlanSelectionReason]:
        """Retrieve the deterministic selection reasons for a given test ID."""
        return list(self.selection_reasons_by_test.get(test_id, []))

    def is_requirement_protected(self, requirement_id: str) -> bool:
        """Check if an affected requirement is protected by tests in this plan."""
        clean_req = str(requirement_id).strip()
        return clean_req in self.protected_requirement_ids

    def has_coverage_gap(self) -> bool:
        """Return True if any affected requirement lacks authoritative test protection."""
        return len(self.uncovered_affected_requirement_ids) > 0

    def __eq__(self, other: Any) -> bool:
        """Deterministic equivalence check comparing all logical plan properties.

        Volatile attributes like created_at are excluded so identical inputs evaluate to equal.
        """
        if not isinstance(other, RegressionPlan):
            return False
        return (
            self.project_id == other.project_id
            and self.mode == other.mode
            and self.base_version_id == other.base_version_id
            and self.target_version_id == other.target_version_id
            and self.inventory_id == other.inventory_id
            and self.selected_test_ids == other.selected_test_ids
            and self.selected_tests == other.selected_tests
            and self.selected_tests_by_tier == other.selected_tests_by_tier
            and self.selected_requirement_ids == other.selected_requirement_ids
            and self.affected_requirement_ids == other.affected_requirement_ids
            and self.protected_requirement_ids == other.protected_requirement_ids
            and self.uncovered_affected_requirement_ids == other.uncovered_affected_requirement_ids
            and self.unrelated_requirement_ids == other.unrelated_requirement_ids
            and self.selection_reasons_by_test == other.selection_reasons_by_test
            and self.broadening_reasons == other.broadening_reasons
            and self.requires_broader_regression == other.requires_broader_regression
            and self.is_execution_safe == other.is_execution_safe
            and self.plan_warnings == other.plan_warnings
            and self.total_inventory_tests == other.total_inventory_tests
            and self.unselected_test_count == other.unselected_test_count
            and self.metadata == other.metadata
        )


# ==============================================================================
# Execution Contracts (Phase 11L Stage 5)
# ==============================================================================

class TestExecutionStatus(str, Enum):
    """Deterministic terminal status of an individual test case execution."""

    __test__ = False

    PASSED = "PASSED"
    FAILED = "FAILED"
    ERROR = "ERROR"
    SKIPPED = "SKIPPED"
    BLOCKED = "BLOCKED"


class IndividualTestResult(BaseModel):
    """Normalized execution record for a single test case across any tier."""

    __test__ = False
    model_config = ConfigDict(extra="forbid")

    test_id: str = Field(
        ...,
        description="Deterministic identifier of the executed test",
    )
    tier: TestTier = Field(
        ...,
        description="TestTier classification of the test",
    )
    status: TestExecutionStatus = Field(
        ...,
        description="Terminal execution status (PASSED, FAILED, ERROR, SKIPPED, BLOCKED)",
    )
    duration_seconds: float = Field(
        default=0.0,
        ge=0.0,
        description="Execution duration in seconds",
    )
    message: str | None = Field(
        default=None,
        description="Summary explanation or failure reason",
    )
    stdout: str | None = Field(
        default=None,
        description="Captured test runner standard output (bounded)",
    )
    stderr: str | None = Field(
        default=None,
        description="Captured test runner standard error (bounded)",
    )
    error_details: str | None = Field(
        default=None,
        description="Stack trace or detailed diagnostic output if failed or errored",
    )
    is_infrastructure_failure: bool = False
    requirement_links: list[str] = Field(
        default_factory=list,
        description="Authoritative requirement IDs linked to this test",
    )


class TierExecutionSummary(BaseModel):
    """Deterministic execution metrics aggregated for a specific TestTier."""

    __test__ = False
    model_config = ConfigDict(extra="forbid")

    tier: TestTier = Field(
        ...,
        description="Testing tier for this summary",
    )
    total_tests: int = Field(
        default=0,
        ge=0,
        description="Total tests scheduled for this tier",
    )
    passed_tests: int = Field(
        default=0,
        ge=0,
        description="Count of tests that executed and passed",
    )
    failed_tests: int = Field(
        default=0,
        ge=0,
        description="Count of tests that executed and failed assertions",
    )
    errored_tests: int = Field(
        default=0,
        ge=0,
        description="Count of tests that encountered infrastructure errors",
    )
    skipped_tests: int = Field(
        default=0,
        ge=0,
        description="Count of tests skipped",
    )
    blocked_tests: int = Field(
        default=0,
        ge=0,
        description="Count of tests blocked from execution by safety preconditions",
    )
    duration_seconds: float = Field(
        default=0.0,
        ge=0.0,
        description="Total duration spent executing tests in this tier",
    )
    test_ids_passed: list[str] = Field(
        default_factory=list,
        description="Sorted list of test IDs that passed",
    )
    test_ids_failed: list[str] = Field(
        default_factory=list,
        description="Sorted list of test IDs that failed assertions",
    )
    test_ids_errored: list[str] = Field(
        default_factory=list,
        description="Sorted list of test IDs that experienced infrastructure errors",
    )
    test_ids_skipped: list[str] = Field(
        default_factory=list,
        description="Sorted list of test IDs that were skipped",
    )
    test_ids_blocked: list[str] = Field(
        default_factory=list,
        description="Sorted list of test IDs blocked from execution",
    )


class RequirementExecutionResult(BaseModel):
    """Deterministic requirement-level outcome derived from executed tests."""

    __test__ = False
    model_config = ConfigDict(extra="forbid")

    requirement_id: str = Field(
        ...,
        description="Authoritative requirement identifier",
    )
    is_satisfied: bool = Field(
        ...,
        description="True if all executed authoritative tests for this requirement passed and at least one passed",
    )
    total_tests: int = Field(
        default=0,
        ge=0,
        description="Total selected tests covering this requirement",
    )
    passed_tests: int = Field(
        default=0,
        ge=0,
        description="Passed test count for this requirement",
    )
    failed_tests: int = Field(
        default=0,
        ge=0,
        description="Failed or errored test count for this requirement",
    )
    covering_tiers: list[TestTier] = Field(
        default_factory=list,
        description="Tiers of tests that executed for this requirement",
    )
    test_ids_passed: list[str] = Field(
        default_factory=list,
        description="Sorted test IDs that passed for this requirement",
    )
    test_ids_failed: list[str] = Field(
        default_factory=list,
        description="Sorted test IDs that failed or errored for this requirement",
    )


class RegressionExecutionStatus(str, Enum):
    """Deterministic terminal status of a full regression execution run."""

    __test__ = False

    PASSED = "PASSED"
    FAILED = "FAILED"
    PARTIAL_FAILURE = "PARTIAL_FAILURE"
    BLOCKED = "BLOCKED"
    ERROR = "ERROR"
    TIMEOUT = "TIMEOUT"


class RegressionExecutionResult(BaseModel):
    """Authoritative result contract of a completed selective regression run."""

    __test__ = False
    model_config = ConfigDict(extra="forbid")

    execution_id: str = Field(
        default_factory=lambda: str(uuid.uuid4()),
        description="Unique identifier for this regression execution cycle",
    )
    project_id: str = Field(
        ...,
        description="Canonical project UUID string owning this execution",
    )
    inventory_id: str = Field(
        ...,
        description="Source UnifiedTestInventory identifier",
    )
    mode: RegressionPlanMode = Field(
        ...,
        description="Plan execution scope mode (SELECTIVE, BROAD, FULL)",
    )
    status: RegressionExecutionStatus = Field(
        ...,
        description="Deterministic terminal status of this regression execution",
    )
    started_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Execution start timestamp",
    )
    completed_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Execution completion timestamp",
    )
    duration_seconds: float = Field(
        default=0.0,
        ge=0.0,
        description="Total execution wall-clock time in seconds",
    )
    total_tests: int = Field(
        default=0,
        ge=0,
        description="Total tests in plan",
    )
    passed_tests: int = Field(
        default=0,
        ge=0,
        description="Count of tests that executed and passed",
    )
    failed_tests: int = Field(
        default=0,
        ge=0,
        description="Count of tests that executed and failed assertions",
    )
    errored_tests: int = Field(
        default=0,
        ge=0,
        description="Count of tests that encountered infrastructure errors",
    )
    skipped_tests: int = Field(
        default=0,
        ge=0,
        description="Count of tests skipped",
    )
    blocked_tests: int = Field(
        default=0,
        ge=0,
        description="Count of tests blocked by safety preconditions",
    )
    results_by_tier: dict[str, TierExecutionSummary] = Field(
        default_factory=dict,
        description="TestTier value -> TierExecutionSummary",
    )
    test_results: list[IndividualTestResult] = Field(
        default_factory=list,
        description="Individual test execution results ordered by tier and test_id",
    )
    requirement_results: dict[str, RequirementExecutionResult] = Field(
        default_factory=dict,
        description="Requirement ID -> RequirementExecutionResult",
    )
    protected_requirements_satisfied: list[str] = Field(
        default_factory=list,
        description="Sorted list of affected requirements whose tests all passed",
    )
    protected_requirements_failed: list[str] = Field(
        default_factory=list,
        description="Sorted list of affected requirements with at least one failed test",
    )
    uncovered_affected_requirements: list[str] = Field(
        default_factory=list,
        description="Coverage gaps: affected requirements without any test coverage",
    )
    failure_summary: str | None = Field(
        default=None,
        description="High-level diagnostic summary if any test failed",
    )
    infrastructure_failures: list[str] = Field(
        default_factory=list,
        description="Details of infrastructure errors (Docker unavailable, container timeout, etc.)",
    )
    artifacts: dict[str, Any] = Field(
        default_factory=dict,
        description="Associated execution artifacts (e.g. failure diagnosis, verification snapshot, logs)",
    )
    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Telemetry and contextual execution audit annotations",
    )

    @field_validator("project_id", mode="before")
    @classmethod
    def normalize_project_id(cls, v: Any) -> str:
        return str(v).strip().lower()

    # Query Helper Methods
    def is_successful(self) -> bool:
        """Return True if all scheduled tests passed."""
        return self.status == RegressionExecutionStatus.PASSED

    def get_failed_tests(self) -> list[IndividualTestResult]:
        """Retrieve tests that failed assertions or had infrastructure errors."""
        return [
            t for t in self.test_results
            if t.status in (TestExecutionStatus.FAILED, TestExecutionStatus.ERROR)
        ]

    def get_result_for_test(self, test_id: str) -> IndividualTestResult | None:
        """Lookup an individual test result by test_id."""
        for t in self.test_results:
            if t.test_id == test_id:
                return t
        return None

    def get_result_for_requirement(self, requirement_id: str) -> RequirementExecutionResult | None:
        """Lookup requirement execution result by requirement ID."""
        clean_req = str(requirement_id).strip()
        return self.requirement_results.get(clean_req)

    def __eq__(self, other: Any) -> bool:
        """Deterministic equivalence check comparing all logical execution attributes.

        Excludes volatile run identities and timestamps.
        """
        if not isinstance(other, RegressionExecutionResult):
            return False
        return (
            self.project_id == other.project_id
            and self.inventory_id == other.inventory_id
            and self.mode == other.mode
            and self.status == other.status
            and self.total_tests == other.total_tests
            and self.passed_tests == other.passed_tests
            and self.failed_tests == other.failed_tests
            and self.errored_tests == other.errored_tests
            and self.skipped_tests == other.skipped_tests
            and self.blocked_tests == other.blocked_tests
            and self.results_by_tier == other.results_by_tier
            and self.test_results == other.test_results
            and self.requirement_results == other.requirement_results
            and self.protected_requirements_satisfied == other.protected_requirements_satisfied
            and self.protected_requirements_failed == other.protected_requirements_failed
            and self.uncovered_affected_requirements == other.uncovered_affected_requirements
            and self.failure_summary == other.failure_summary
            and self.infrastructure_failures == other.infrastructure_failures
            and self.artifacts == other.artifacts
            and self.metadata == other.metadata
        )

