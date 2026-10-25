"""Exceptions for Browser Journey Validation and Coverage Subsystem.

Phase 11K — Stage 2: Browser Journey Errors
"""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.browser.journey.contracts import ValidationOutcome


class BrowserJourneyError(Exception):
    """Base exception for all browser journey processing errors."""
    pass


class BrowserJourneyValidationError(BrowserJourneyError):
    """Raised when candidate browser journeys fail deterministic validation."""

    def __init__(self, message: str, outcome: "ValidationOutcome") -> None:
        super().__init__(message)
        self.message = message
        self.outcome = outcome
        self.errors = outcome.errors
        self.warnings = outcome.warnings

    def __str__(self) -> str:
        error_lines = [f"- {e.code}: {e.message}" for e in self.errors[:5]]
        if len(self.errors) > 5:
            error_lines.append(f"- ... ({len(self.errors) - 5} additional errors)")
        return f"{self.message}\n" + "\n".join(error_lines)


class BrowserJourneyAdaptationError(BrowserJourneyError, ValueError):
    """Raised when deterministic adaptation of a validated browser journey fails."""
    pass

