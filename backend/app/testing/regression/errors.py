"""Exceptions and Error Hierarchies for Selective Regression Planning (Phase 11L Stage 4).

Provides strongly-typed exception classes for regression plan generation,
project isolation enforcement, and plan validation.
"""


class RegressionPlanError(Exception):
    """Base exception for all regression planning errors."""

    pass


class RegressionPlanIsolationError(RegressionPlanError):
    """Raised when cross-project boundaries are violated during regression planning or validation."""

    pass


class RegressionPlanValidationError(RegressionPlanError):
    """Raised when a regression plan fails deterministic validation checks."""

    pass


class RegressionExecutionError(RegressionPlanError):
    """Base exception for all regression execution errors."""

    pass


class RegressionExecutionSafetyError(RegressionExecutionError):
    """Raised when execution is blocked by safety or validation invariants."""

    pass

