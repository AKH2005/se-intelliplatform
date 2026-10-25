"""Browser Journey Intelligence Agent Package.

Phase 11K — AI-Powered Browser Journey Generation.
"""

from app.agents.browser_journey.contracts import (
    BoundedRequirementInfo,
    BoundedRouteInfo,
    BrowserActionType,
    BrowserJourney,
    BrowserJourneyGenerationInput,
    BrowserJourneyStep,
    BrowserJourneySuiteCandidate,
    BrowserTarget,
    BrowserTargetType,
    JourneyCategory,
    JourneyPriority,
)
from app.agents.browser_journey.agent import BrowserJourneyGenerationAgent

__all__ = [
    "BrowserActionType",
    "BrowserJourney",
    "BrowserJourneyGenerationAgent",
    "BrowserJourneyGenerationInput",
    "BrowserJourneyStep",
    "BrowserJourneySuiteCandidate",
    "BrowserTarget",
    "BrowserTargetType",
    "BoundedRequirementInfo",
    "BoundedRouteInfo",
    "JourneyCategory",
    "JourneyPriority",
]
