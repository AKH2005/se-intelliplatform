"""Unified Multi-Tier Coverage Intelligence Package (Phase 11L Stage 2).

Provides deterministic, side-effect free requirement-level coverage calculation
across all four platform test tiers (UNIT, AI_TEST, BROWSER_SMOKE, BROWSER_JOURNEY).
"""

from app.testing.coverage.contracts import (
    RequirementTraceabilityRecord,
    TierCoverageSummary,
    UnifiedCoverageReport,
)
from app.testing.coverage.engine import UnifiedCoverageEngine
from app.testing.coverage.errors import (
    UnifiedCoverageError,
    UnifiedCoverageIsolationError,
    UnifiedCoverageValidationError,
)

__all__ = [
    "RequirementTraceabilityRecord",
    "TierCoverageSummary",
    "UnifiedCoverageReport",
    "UnifiedCoverageEngine",
    "UnifiedCoverageError",
    "UnifiedCoverageIsolationError",
    "UnifiedCoverageValidationError",
]
