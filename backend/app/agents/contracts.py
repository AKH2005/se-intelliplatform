"""Core Contracts, Enums, and Structured Envelopes for Agent Framework."""

import enum
import uuid
from datetime import datetime, timezone
from typing import Any, Generic, TypeVar
from pydantic import BaseModel, ConfigDict, Field

OutputT = TypeVar("OutputT", bound=BaseModel)


class AgentType(str, enum.Enum):
    """Categorization of agent operational domain."""
    ANALYSIS = "ANALYSIS"
    ARCHITECTURE = "ARCHITECTURE"
    GENERATION = "GENERATION"
    REVIEW = "REVIEW"
    TESTING = "TESTING"
    VALIDATION = "VALIDATION"


class AgentExecutionStatus(str, enum.Enum):
    """Deterministic states of an agent execution lifecycle."""
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    VALIDATING = "VALIDATING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class AgentMetadata(BaseModel):
    """Authoritative metadata defining an agent's identity and capabilities."""

    agent_id: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Unique identifier for the agent (e.g. 'requirement-analysis')",
        examples=["requirement-analysis"],
    )
    name: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description="Human-readable display name",
        examples=["Requirement Analysis Agent"],
    )
    description: str = Field(
        ...,
        description="Detailed explanation of agent responsibilities and domain focus",
    )
    version: str = Field(
        ...,
        pattern=r"^\d+\.\d+\.\d+$",
        description="Semantic version of the agent specification",
        examples=["1.0.0"],
    )
    agent_type: AgentType = Field(
        ...,
        description="Functional domain classification",
    )


class ValidationResult(BaseModel):
    """Result of structural and deterministic validation hooks."""

    is_valid: bool = Field(
        ...,
        description="True if output satisfies all schema constraints and domain business rules",
    )
    errors: list[str] = Field(
        default_factory=list,
        description="List of blocking validation error messages",
    )
    warnings: list[str] = Field(
        default_factory=list,
        description="List of non-blocking advisories or lint warnings",
    )


class AgentErrorDetail(BaseModel):
    """Structured failure representation for agent execution errors."""

    error_code: str = Field(..., description="Machine-readable error category code")
    message: str = Field(..., description="Human-readable explanation of failure")
    transient: bool = Field(
        default=False,
        description="True if error was caused by a transient condition eligible for retry",
    )


class AgentResult(BaseModel, Generic[OutputT]):
    """Generic structured result envelope emitted by all framework agents.
    
    Treats agent output as typed structured data rather than unverified raw LLM text.
    Maintains provenance of which context version and agent version produced the result.
    """

    model_config = ConfigDict(arbitrary_types_allowed=True)

    execution_id: uuid.UUID = Field(..., description="Unique UUID for this execution run")
    agent_id: str = Field(..., description="ID of executing agent")
    agent_version: str = Field(..., description="Version of executing agent")
    status: AgentExecutionStatus = Field(..., description="Terminal execution status")
    output: OutputT | None = Field(
        default=None,
        description="Validated typed domain output model, or None on failure",
    )
    validation: ValidationResult = Field(
        default_factory=lambda: ValidationResult(is_valid=True),
        description="Detailed structural and deterministic validation outcome",
    )
    error: AgentErrorDetail | None = Field(
        default=None,
        description="Failure details if status is FAILED",
    )
    context_version: int = Field(
        ...,
        description="Version sequence number of the Project Context consumed",
    )
    started_at: datetime = Field(..., description="Timestamp when execution commenced")
    completed_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Timestamp when execution terminated",
    )
    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Sanitized execution metadata and telemetry (no secrets)",
    )
