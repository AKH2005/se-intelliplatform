"""Strongly-typed Domain Contracts for Multi-Tier Coverage Intelligence (Phase 11L Stage 2).

Defines tier-level coverage summaries, requirement traceability records,
and the aggregate UnifiedCoverageReport model.
"""

from datetime import datetime, timezone
from typing import Any
from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.testing.inventory.contracts import TestTier


class TierCoverageSummary(BaseModel):
    """Deterministic requirement coverage metrics for a specific test tier."""

    __test__ = False
    model_config = ConfigDict(extra="forbid")

    tier: TestTier = Field(
        ...,
        description="Testing tier for this summary (UNIT, AI_TEST, BROWSER_SMOKE, BROWSER_JOURNEY)",
    )
    total_active_requirements: int = Field(
        ...,
        ge=0,
        description="Total authoritative active requirements in project scope",
    )
    covered_requirement_count: int = Field(
        ...,
        ge=0,
        description="Count of active requirements covered by at least one test in this tier",
    )
    uncovered_requirement_count: int = Field(
        ...,
        ge=0,
        description="Count of active requirements not covered by tests in this tier",
    )
    covered_requirement_ids: list[str] = Field(
        default_factory=list,
        description="Sorted list of active requirement IDs covered by this tier",
    )
    uncovered_requirement_ids: list[str] = Field(
        default_factory=list,
        description="Sorted list of active requirement IDs not covered by this tier",
    )
    coverage_percentage: float = Field(
        ...,
        ge=0.0,
        le=100.0,
        description="Deterministic tier coverage percentage: (covered / total) * 100.0",
    )
    test_count: int = Field(
        ...,
        ge=0,
        description="Total count of tests in this tier",
    )
    test_ids_by_requirement: dict[str, list[str]] = Field(
        default_factory=dict,
        description="Mapping of Requirement ID -> sorted list of test IDs in this tier",
    )


class RequirementTraceabilityRecord(BaseModel):
    """Detailed multi-tier test traceability record for a single active requirement."""

    __test__ = False
    model_config = ConfigDict(extra="forbid")

    requirement_id: str = Field(
        ...,
        min_length=1,
        description="Canonical requirement identifier or UUID",
    )
    is_covered: bool = Field(
        ...,
        description="True if covered by at least one authoritative test across any tier",
    )
    covering_tiers: list[TestTier] = Field(
        default_factory=list,
        description="List of test tiers providing coverage for this requirement",
    )
    tests_by_tier: dict[str, list[str]] = Field(
        default_factory=dict,
        description="TestTier value -> sorted list of test IDs providing coverage",
    )
    total_tests: int = Field(
        default=0,
        ge=0,
        description="Total count of tests across all tiers covering this requirement",
    )


class UnifiedCoverageReport(BaseModel):
    """Comprehensive, deterministic requirement-level coverage report across all 4 tiers."""

    __test__ = False
    model_config = ConfigDict(extra="forbid")

    project_id: str = Field(
        ...,
        description="Canonical project UUID string owning this report",
    )
    total_active_requirements: int = Field(
        ...,
        ge=0,
        description="Denominator: total active requirements in project scope",
    )
    active_requirement_ids: list[str] = Field(
        default_factory=list,
        description="Sorted list of all active requirement IDs in project scope",
    )
    tier_coverages: dict[str, TierCoverageSummary] = Field(
        default_factory=dict,
        description="TestTier value -> TierCoverageSummary for each tier",
    )
    combined_covered_requirement_ids: list[str] = Field(
        default_factory=list,
        description="Union of active requirement IDs covered by at least one authoritative tier",
    )
    combined_covered_count: int = Field(
        ...,
        ge=0,
        description="Count of active requirements covered by at least one tier",
    )
    combined_uncovered_requirement_ids: list[str] = Field(
        default_factory=list,
        description="Coverage Gaps: active requirements without any authoritative test",
    )
    combined_uncovered_count: int = Field(
        ...,
        ge=0,
        description="Count of uncovered active requirements (coverage gaps)",
    )
    combined_coverage_percentage: float = Field(
        ...,
        ge=0.0,
        le=100.0,
        description="Combined coverage percentage: (combined_covered / total_active) * 100.0",
    )
    requirement_traceability: dict[str, RequirementTraceabilityRecord] = Field(
        default_factory=dict,
        description="Requirement ID -> detailed multi-tier traceability breakdown",
    )
    calculated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Timestamp when coverage was computed",
    )
    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Sanitized telemetry and audit metadata",
    )

    @field_validator("project_id", mode="before")
    @classmethod
    def normalize_project_id(cls, v: Any) -> str:
        return str(v).strip().lower()

    # Convenience Query Helpers
    def get_tier_coverage(self, tier: TestTier | str) -> TierCoverageSummary | None:
        """Retrieve the TierCoverageSummary for a specified TestTier."""
        tier_key = tier.value if isinstance(tier, TestTier) else str(tier)
        return self.tier_coverages.get(tier_key)

    def get_coverage_gaps(self) -> list[str]:
        """Retrieve active requirement IDs that have zero coverage across all tiers."""
        return list(self.combined_uncovered_requirement_ids)

    def is_requirement_covered(self, requirement_id: str) -> bool:
        """Check if a specific active requirement is covered by any authoritative tier."""
        clean_id = str(requirement_id).strip()
        record = self.requirement_traceability.get(clean_id)
        return record.is_covered if record else False

    def get_tests_for_requirement(self, requirement_id: str) -> dict[str, list[str]]:
        """Retrieve tests by tier for a specific requirement."""
        clean_id = str(requirement_id).strip()
        record = self.requirement_traceability.get(clean_id)
        return dict(record.tests_by_tier) if record else {}

    def __eq__(self, other: Any) -> bool:
        """Deterministic equivalence check comparing all logical coverage properties.
        
        Volatile execution attributes like calculated_at are excluded.
        """
        if not isinstance(other, UnifiedCoverageReport):
            return False
        return (
            self.project_id == other.project_id
            and self.total_active_requirements == other.total_active_requirements
            and self.active_requirement_ids == other.active_requirement_ids
            and self.tier_coverages == other.tier_coverages
            and self.combined_covered_requirement_ids == other.combined_covered_requirement_ids
            and self.combined_covered_count == other.combined_covered_count
            and self.combined_uncovered_requirement_ids == other.combined_uncovered_requirement_ids
            and self.combined_uncovered_count == other.combined_uncovered_count
            and self.combined_coverage_percentage == other.combined_coverage_percentage
            and self.requirement_traceability == other.requirement_traceability
            and self.metadata == other.metadata
        )
