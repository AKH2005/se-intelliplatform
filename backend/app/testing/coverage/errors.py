"""Domain Exceptions for Multi-Tier Coverage Intelligence (Phase 11L Stage 2)."""


class UnifiedCoverageError(Exception):
    """Base exception for all unified coverage intelligence failures."""
    pass


class UnifiedCoverageIsolationError(UnifiedCoverageError):
    """Raised when cross-project requirements or tests attempt to contaminate coverage."""
    pass


class UnifiedCoverageValidationError(UnifiedCoverageError):
    """Raised when input validation for coverage calculation fails."""
    pass
