"""Centralized Domain & Application Exception Hierarchy."""

from typing import Any


class ApplicationError(Exception):
    """Base exception for all domain and application errors."""

    status_code: int = 500
    title: str = "Internal Server Error"
    type_uri: str = "https://api.se-intelliplatform.local/errors/internal-error"

    def __init__(
        self,
        message: str = "An unexpected error occurred processing your request.",
        detail: str | None = None,
        extra: dict[str, Any] | None = None,
    ):
        super().__init__(message)
        self.message = message
        self.detail = detail or message
        self.extra = extra or {}


class NotFoundError(ApplicationError):
    """Raised when a requested resource is not found."""

    status_code: int = 404
    title: str = "Resource Not Found"
    type_uri: str = "https://api.se-intelliplatform.local/errors/not-found"

    def __init__(self, resource_type: str, identifier: Any):
        detail = f"{resource_type} with identifier '{identifier}' was not found."
        super().__init__(message=detail, detail=detail, extra={"resource": resource_type, "id": str(identifier)})


class ConflictError(ApplicationError):
    """Raised when an operation conflicts with existing system state (e.g. duplicate slug)."""

    status_code: int = 409
    title: str = "Resource Conflict"
    type_uri: str = "https://api.se-intelliplatform.local/errors/conflict"

    def __init__(self, message: str, field: str | None = None, value: Any = None):
        extra = {}
        if field:
            extra["field"] = field
        if value is not None:
            extra["value"] = str(value)
        super().__init__(message=message, detail=message, extra=extra)


class ValidationError(ApplicationError):
    """Raised when input data violates domain-specific invariants."""

    status_code: int = 422
    title: str = "Domain Validation Error"
    type_uri: str = "https://api.se-intelliplatform.local/errors/validation-error"

    def __init__(self, message: str, errors: list[dict[str, Any]] | None = None):
        super().__init__(message=message, detail=message, extra={"errors": errors or []})


class ConfigurationError(ApplicationError):
    """Raised when system configuration is invalid or missing required values."""

    status_code: int = 500
    title: str = "Configuration Error"
    type_uri: str = "https://api.se-intelliplatform.local/errors/configuration-error"
