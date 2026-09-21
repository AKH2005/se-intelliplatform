"""Centralized Agent Framework Exception Hierarchy."""

from typing import Any
from app.core.exceptions import ApplicationError, NotFoundError


class AgentError(ApplicationError):
    """Base exception for all agent framework errors."""

    status_code: int = 500
    title: str = "Agent Framework Error"
    type_uri: str = "https://api.se-intelliplatform.local/errors/agent-error"


class ProviderError(AgentError):
    """Raised when an underlying LLM provider fails communication or invocation."""

    status_code: int = 502
    title: str = "LLM Provider Error"
    type_uri: str = "https://api.se-intelliplatform.local/errors/provider-error"

    def __init__(
        self,
        message: str = "An error occurred communicating with the LLM provider.",
        provider_name: str = "unknown",
        transient: bool = False,
        extra: dict[str, Any] | None = None,
    ):
        ext = extra or {}
        ext["provider"] = provider_name
        ext["transient"] = transient
        super().__init__(message=message, detail=message, extra=ext)
        self.provider_name = provider_name
        self.transient = transient


class TransientProviderError(ProviderError):
    """Raised for transient provider failures (rate limits, network drops) eligible for retry."""

    status_code: int = 503
    title: str = "Transient LLM Provider Error"
    type_uri: str = "https://api.se-intelliplatform.local/errors/transient-provider-error"

    def __init__(
        self,
        message: str = "Temporary LLM provider error. Eligible for retry.",
        provider_name: str = "unknown",
        extra: dict[str, Any] | None = None,
    ):
        super().__init__(
            message=message,
            provider_name=provider_name,
            transient=True,
            extra=extra,
        )


class AgentExecutionError(AgentError):
    """Raised when an agent lifecycle execution encounters an unexpected failure."""

    status_code: int = 500
    title: str = "Agent Execution Error"
    type_uri: str = "https://api.se-intelliplatform.local/errors/agent-execution-error"


class AgentValidationError(AgentError):
    """Raised when an agent output fails structural or deterministic domain validation."""

    status_code: int = 422
    title: str = "Agent Output Validation Error"
    type_uri: str = "https://api.se-intelliplatform.local/errors/agent-validation-error"

    def __init__(
        self,
        message: str = "Agent output failed schema or business validation constraints.",
        validation_errors: list[str] | None = None,
        extra: dict[str, Any] | None = None,
    ):
        ext = extra or {}
        errs = validation_errors or []
        ext["validation_errors"] = errs
        full_detail = f"{message} [{'; '.join(errs)}]" if errs else message
        super().__init__(message=full_detail, detail=full_detail, extra=ext)
        self.validation_errors = errs


class AgentConfigurationError(AgentError):
    """Raised when agent metadata, dependencies, or parameters are invalid."""

    status_code: int = 500
    title: str = "Agent Configuration Error"
    type_uri: str = "https://api.se-intelliplatform.local/errors/agent-configuration-error"


class AgentNotFoundError(NotFoundError):
    """Raised when an agent is not found in the AgentRegistry."""

    def __init__(self, agent_id: str):
        super().__init__(resource_type="Agent", identifier=agent_id)
