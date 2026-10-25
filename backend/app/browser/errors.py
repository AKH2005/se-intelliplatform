"""Browser Testing Subsystem Exception Hierarchy for Phase 11J (Stage 3).

Defines deterministic, typed exceptions for browser lifecycle, configuration,
navigation allowlisting, execution timeouts, and resource governance.
"""

from app.core.exceptions import ApplicationError


class BrowserErrorBase(ApplicationError):
    """Base exception for all browser subsystem failures."""

    def __init__(self, message: str, status_code: int = 500) -> None:
        super().__init__(message=message)
        self.status_code = status_code


class BrowserConfigurationError(BrowserErrorBase):
    """Raised when browser test configuration or manifest resolution fails."""

    def __init__(self, message: str) -> None:
        super().__init__(message=message, status_code=400)


class BrowserResourceLimitError(BrowserErrorBase):
    """Raised when concurrent browser session capacity (max 2) is exceeded."""

    def __init__(self, message: str = "Maximum concurrent browser sessions exceeded.") -> None:
        super().__init__(message=message, status_code=503)


class BrowserStartupError(BrowserErrorBase):
    """Raised when the browser container or Chromium process fails to launch."""

    def __init__(self, message: str) -> None:
        super().__init__(message=message, status_code=500)


class BrowserTimeoutError(BrowserErrorBase):
    """Raised when browser execution or navigation exceeds strict time bounds."""

    def __init__(self, message: str = "Browser test execution timed out.") -> None:
        super().__init__(message=message, status_code=504)


class BrowserNavigationError(BrowserErrorBase):
    """Raised when an illegal or disallowed navigation target is attempted."""

    def __init__(self, message: str) -> None:
        super().__init__(message=message, status_code=403)


class BrowserExecutionError(BrowserErrorBase):
    """Raised when an internal error occurs during deterministic browser execution."""

    def __init__(self, message: str) -> None:
        super().__init__(message=message, status_code=500)


class BrowserArtifactError(BrowserErrorBase):
    """Raised when screenshot or artifact persistence/validation fails."""

    def __init__(self, message: str) -> None:
        super().__init__(message=message, status_code=500)
