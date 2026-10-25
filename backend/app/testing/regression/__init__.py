"""Selective Regression Planning Package (Phase 11L Stage 4).

Provides deterministic regression test planning and validation across all four platform
testing tiers (UNIT, AI_TEST, BROWSER_SMOKE, BROWSER_JOURNEY) based on Stage 3 ChangeImpactReport,
Stage 2 UnifiedCoverageReport, and Stage 1 UnifiedTestInventory.
"""

from app.testing.regression.contracts import (
    IndividualTestResult,
    PlanSelectionReason,
    RegressionExecutionResult,
    RegressionExecutionStatus,
    RegressionPlan,
    RegressionPlanMode,
    RequirementExecutionResult,
    SelectedTest,
    TestExecutionStatus,
    TierExecutionSummary,
)
from app.testing.regression.errors import (
    RegressionExecutionError,
    RegressionExecutionSafetyError,
    RegressionPlanError,
    RegressionPlanIsolationError,
    RegressionPlanValidationError,
)
from app.testing.regression.executor import RegressionExecutionService
from app.testing.regression.planner import (
    TIER_EXECUTION_ORDER,
    SelectiveRegressionPlanner,
)
from app.testing.regression.validator import RegressionPlanValidator

__all__ = [
    "IndividualTestResult",
    "PlanSelectionReason",
    "RegressionExecutionResult",
    "RegressionExecutionStatus",
    "RegressionPlan",
    "RegressionPlanMode",
    "RequirementExecutionResult",
    "SelectedTest",
    "TestExecutionStatus",
    "TierExecutionSummary",
    "RegressionExecutionError",
    "RegressionExecutionSafetyError",
    "RegressionPlanError",
    "RegressionPlanIsolationError",
    "RegressionPlanValidationError",
    "RegressionExecutionService",
    "TIER_EXECUTION_ORDER",
    "SelectiveRegressionPlanner",
    "RegressionPlanValidator",
]
