"""Browser Testing Runtime Subsystem for Phase 11J (Stage 3).

Provides deterministic browser smoke testing against isolated application containers
running on ephemeral internal Docker networks.
"""

from app.browser.contracts import (
    DEFAULT_PLAYWRIGHT_IMAGE,
    MAX_BROWSER_SESSION_TIMEOUT_SECONDS,
    MAX_CONCURRENT_BROWSER_SESSIONS,
    BrowserInteractionType,
    BrowserLimits,
    BrowserSessionConfig,
    DeterministicBrowserTestDefinition,
    DeterministicInteraction,
    create_default_smoke_suite,
)
from app.browser.errors import (
    BrowserArtifactError,
    BrowserConfigurationError,
    BrowserErrorBase,
    BrowserExecutionError,
    BrowserNavigationError,
    BrowserResourceLimitError,
    BrowserStartupError,
    BrowserTimeoutError,
)
from app.browser.browser_executor import BrowserExecutor
from app.browser.browser_testing_service import BrowserTestingService
from app.browser.journey import (
    BrowserJourneyAdaptationError,
    BrowserJourneyAdapter,
    BrowserJourneyError,
    BrowserJourneyValidationError,
    BrowserJourneyValidator,
    BrowserJourneyWorkflowOrchestrator,
    BrowserJourneyWorkflowResult,
    BrowserJourneyWorkflowStatus,
    RequirementCoverageEngine,
    RequirementCoverageReport,
    ValidatedBrowserJourney,
    ValidatedBrowserJourneySuite,
    ValidationCategory,
    ValidationContext,
    ValidationIssue,
    ValidationOutcome,
    ValidationSeverity,
)

__all__ = [
    "DEFAULT_PLAYWRIGHT_IMAGE",
    "MAX_BROWSER_SESSION_TIMEOUT_SECONDS",
    "MAX_CONCURRENT_BROWSER_SESSIONS",
    "BrowserArtifactError",
    "BrowserConfigurationError",
    "BrowserErrorBase",
    "BrowserExecutionError",
    "BrowserExecutor",
    "BrowserInteractionType",
    "BrowserLimits",
    "BrowserNavigationError",
    "BrowserResourceLimitError",
    "BrowserSessionConfig",
    "BrowserStartupError",
    "BrowserTestingService",
    "BrowserTimeoutError",
    "DeterministicBrowserTestDefinition",
    "DeterministicInteraction",
    "create_default_smoke_suite",
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
