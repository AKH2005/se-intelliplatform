"""Request and Response Schemas for Testing and Selective Regression (Phase 11L Stage 6)."""

from datetime import datetime, timezone
from typing import Any
import uuid
from pydantic import BaseModel, ConfigDict, Field

from app.testing.coverage.contracts import UnifiedCoverageReport
from app.testing.impact.contracts import ChangeImpactReport
from app.testing.regression.contracts import (
    RegressionPlan,
    RegressionPlanMode,
)


class ChangeImpactRequest(BaseModel):
    """Request payload for deterministic change impact analysis."""

    model_config = ConfigDict(extra="forbid")

    base_version_id: uuid.UUID | None = Field(
        default=None,
        description="Optional base development version UUID for diff comparison",
    )
    target_version_id: uuid.UUID | None = Field(
        default=None,
        description="Optional target development version UUID for diff comparison",
    )
    changed_files: list[str] | None = Field(
        default=None,
        description="Explicit list of project-relative changed file paths",
    )
    files_map: dict[str, str] | None = Field(
        default=None,
        description="Optional explicit file content mapping {path: content}",
    )


class PlanRegressionRequest(BaseModel):
    """Request payload for selective regression plan generation."""

    model_config = ConfigDict(extra="forbid")

    base_version_id: uuid.UUID | None = Field(
        default=None,
        description="Optional base development version UUID",
    )
    target_version_id: uuid.UUID | None = Field(
        default=None,
        description="Optional target development version UUID",
    )
    changed_files: list[str] | None = Field(
        default=None,
        description="Optional explicit list of project-relative changed file paths",
    )
    mode: RegressionPlanMode = Field(
        default=RegressionPlanMode.SELECTIVE,
        description="Regression execution mode: SELECTIVE, BROAD, FULL",
    )
    auto_broaden: bool = Field(
        default=False,
        description="Whether to automatically broaden scope if uncertainty or broad flags are detected",
    )
    impact_report: ChangeImpactReport | None = Field(
        default=None,
        description="Optional pre-computed ChangeImpactReport",
    )
    coverage_report: UnifiedCoverageReport | None = Field(
        default=None,
        description="Optional pre-computed UnifiedCoverageReport",
    )
    metadata: dict[str, Any] | None = Field(
        default=None,
        description="Optional caller metadata to attach to the regression plan",
    )


class ExecuteRegressionRequest(BaseModel):
    """Request payload for executing a selective regression plan."""

    model_config = ConfigDict(extra="forbid")

    plan: RegressionPlan | None = Field(
        default=None,
        description="Validated RegressionPlan to execute directly",
    )
    base_version_id: uuid.UUID | None = Field(
        default=None,
        description="Optional base development version UUID if plan is to be generated",
    )
    target_version_id: uuid.UUID | None = Field(
        default=None,
        description="Optional target development version UUID if plan is to be generated",
    )
    changed_files: list[str] | None = Field(
        default=None,
        description="Optional list of changed file paths if plan is to be generated",
    )
    mode: RegressionPlanMode = Field(
        default=RegressionPlanMode.SELECTIVE,
        description="Regression execution mode if plan is generated: SELECTIVE, BROAD, FULL",
    )
    auto_broaden: bool = Field(
        default=False,
        description="Auto-broaden scope if plan is generated and uncertainty exists",
    )
    skip_browser_tests: bool = Field(
        default=False,
        description="Whether to skip browser tier executions",
    )
    browser_base_url: str | None = Field(
        default=None,
        description="Optional base URL for browser smoke tests",
    )
    execution_timeout_seconds: int = Field(
        default=300,
        ge=10,
        le=1800,
        description="Maximum execution timeout in seconds",
    )


class CoverageGapItem(BaseModel):
    """Itemized coverage gap for a single uncovered active requirement."""

    model_config = ConfigDict(extra="forbid")

    requirement_id: str = Field(..., description="Uncovered requirement ID")
    covering_tiers: list[str] = Field(
        default_factory=list,
        description="List of tiers covering this requirement (empty for total gap)",
    )
    available_test_ids: list[str] = Field(
        default_factory=list,
        description="Available test IDs linked to this requirement across all tiers",
    )
    tests_by_tier: dict[str, list[str]] = Field(
        default_factory=dict,
        description="Test IDs mapped by tier",
    )


class CoverageGapsResponse(BaseModel):
    """Response payload detailing requirement coverage gaps derived from UnifiedCoverageReport."""

    model_config = ConfigDict(extra="forbid")

    project_id: str = Field(..., description="Project UUID string")
    total_active_requirements: int = Field(..., ge=0, description="Total active requirements")
    uncovered_count: int = Field(..., ge=0, description="Count of uncovered active requirements")
    uncovered_requirement_ids: list[str] = Field(
        default_factory=list,
        description="Sorted list of uncovered active requirement IDs",
    )
    gaps: list[CoverageGapItem] = Field(
        default_factory=list,
        description="Detailed itemized breakdown for each uncovered requirement",
    )
    tier_uncovered_summary: dict[str, int] = Field(
        default_factory=dict,
        description="Uncovered requirement count by tier",
    )
    calculated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Timestamp of gap calculation",
    )
    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Sanitized metadata from coverage report",
    )
