"""Domain Exceptions for Change Impact Intelligence (Phase 11L Stage 3)."""


class ChangeImpactError(Exception):
    """Base exception for all change impact intelligence failures."""
    pass


class ChangeImpactIsolationError(ChangeImpactError):
    """Raised when cross-project files, dependencies, or versions violate isolation."""
    pass


class ChangeImpactValidationError(ChangeImpactError):
    """Raised when input validation for change impact analysis fails."""
    pass
