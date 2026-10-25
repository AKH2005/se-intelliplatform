"""Browser Journey Validation & Requirement Coverage Subsystem.

Phase 11K — Stage 2: Deterministic Browser Journey Validation & Requirement Coverage Engine.
"""

from app.browser.journey.adapter import BrowserJourneyAdapter
from app.browser.journey.contracts import (
    BrowserJourneyWorkflowResult,
    BrowserJourneyWorkflowStatus,
    RequirementCoverageReport,
    ValidatedBrowserJourney,
    ValidatedBrowserJourneySuite,
    ValidationCategory,
    ValidationContext,
    ValidationIssue,
    ValidationOutcome,
    ValidationSeverity,
)
from app.browser.journey.coverage import RequirementCoverageEngine
from app.browser.journey.errors import (
    BrowserJourneyAdaptationError,
    BrowserJourneyError,
    BrowserJourneyValidationError,
)
from app.browser.journey.orchestrator import BrowserJourneyWorkflowOrchestrator
from app.browser.journey.validator import BrowserJourneyValidator

__all__ = [
    "BrowserJourneyAdaptationError",
    "BrowserJourneyAdapter",
    "BrowserJourneyError",
    "BrowserJourneyValidationError",
    "BrowserJourneyValidator",
    "BrowserJourneyWorkflowOrchestrator",
    "BrowserJourneyWorkflowResult",
    "BrowserJourneyWorkflowStatus",
    "RequirementCoverageEngine",
    "RequirementCoverageReport",
    "ValidatedBrowserJourney",
    "ValidatedBrowserJourneySuite",
    "ValidationCategory",
    "ValidationContext",
    "ValidationIssue",
    "ValidationOutcome",
    "ValidationSeverity",
]


