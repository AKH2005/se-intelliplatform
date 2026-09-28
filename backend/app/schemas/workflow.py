"""Pydantic v2 Schemas for Workflow API Integration and Discovery.

Defines client-facing request envelopes, sanitized execution outcome models,
and declarative workflow metadata discovery schemas adhering strictly to
RFC 7807 and platform security invariants.
"""

import uuid
from datetime import datetime
from typing import Any
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.agents.code_review.contracts import CodeReviewInput
from app.agents.code_review.validation import validate_code_review_input
from app.agents.contracts import AgentErrorDetail
from app.agents.exceptions import AgentValidationError
from app.workflows.contracts import (
    WorkflowResult,
    WorkflowStatus,
    WorkflowStepResult,
    WorkflowStepStatus,
)

ALLOWED_WORKFLOW_OPTIONS: set[str] = {"fail_fast"}


class WorkflowStepMetadata(BaseModel):
    """Declarative metadata for a single workflow step exposed via discovery."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    step_id: str = Field(..., description="Unique step identifier within the workflow")
    agent_id: str = Field(..., description="Framework agent executed by this step")
    required: bool = Field(..., description="Whether step failure causes pipeline failure")
    depends_on: list[str] = Field(default_factory=list, description="Prerequisite step IDs")
    description: str | None = Field(default=None, description="Human-readable description of intent")


class WorkflowMetadataResponse(BaseModel):
    """Authoritative declarative discovery schema for a predefined workflow pipeline."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    workflow_id: str = Field(..., description="Canonical workflow identifier")
    version: str = Field(..., description="Semantic version of the workflow definition")
    name: str = Field(..., description="Human-readable name")
    description: str = Field(..., description="Detailed description of purpose and outcomes")
    step_count: int = Field(..., description="Total number of steps in the pipeline")
    steps: list[WorkflowStepMetadata] = Field(..., description="Ordered step pipeline definitions")
    required_inputs: list[str] = Field(
        default_factory=list,
        description="List of mandatory input payload fields (e.g. ['project_id'])",
    )
    optional_inputs: list[str] = Field(
        default_factory=list,
        description="List of supported optional payload fields (e.g. ['snapshot_id', 'code_review_input'])",
    )


class WorkflowExecuteRequest(BaseModel):
    """API request payload envelope for triggering synchronous workflow execution."""

    model_config = ConfigDict(extra="forbid")

    project_id: uuid.UUID = Field(
        ...,
        description="UUID of the project whose canonical context should be evaluated",
    )
    snapshot_id: uuid.UUID | None = Field(
        default=None,
        description="Optional UUID of an immutable ContextSnapshot. Mutually exclusive with snapshot_version.",
    )
    snapshot_version: int | None = Field(
        default=None,
        ge=1,
        description="Optional integer version of an immutable ContextSnapshot. Mutually exclusive with snapshot_id.",
    )
    code_review_input: CodeReviewInput | None = Field(
        default=None,
        description="Optional source code payload required if the workflow executes CodeReviewAgent",
    )
    explainability_target_scope: str | None = Field(
        default=None,
        max_length=500,
        description="Optional focus scope passed to ExplainabilityAgent",
    )
    explainability_user_query: str | None = Field(
        default=None,
        max_length=1000,
        description="Optional developer query or question passed to ExplainabilityAgent",
    )
    options: dict[str, Any] = Field(
        default_factory=dict,
        description="Strictly bounded execution directives (e.g. {'fail_fast': False})",
    )

    @field_validator("options")
    @classmethod
    def validate_options(cls, v: dict[str, Any]) -> dict[str, Any]:
        """Reject unapproved or speculative workflow options."""
        unknown = set(v.keys()) - ALLOWED_WORKFLOW_OPTIONS
        if unknown:
            raise ValueError(
                f"Unsupported workflow execution option(s): {', '.join(sorted(unknown))}. "
                f"Allowed options: {', '.join(sorted(ALLOWED_WORKFLOW_OPTIONS))}"
            )
        return v

    @model_validator(mode="after")
    def validate_request_invariants(self) -> "WorkflowExecuteRequest":
        """Validate mutually exclusive context selectors and enforce security on external inputs."""
        # 1. Mutually exclusive snapshot selectors
        if self.snapshot_id is not None and self.snapshot_version is not None:
            raise ValueError(
                "Cannot specify both 'snapshot_id' and 'snapshot_version'. Provide at most one."
            )

        # 2. Enforce deterministic security and size constraints on CodeReviewInput
        if self.code_review_input is not None:
            try:
                validate_code_review_input(self.code_review_input)
            except AgentValidationError as exc:
                raise ValueError(f"Invalid code_review_input: {exc}") from exc

        return self


class WorkflowStepResultResponse(BaseModel):
    """Sanitized API representation of a single workflow step execution outcome."""

    model_config = ConfigDict(extra="forbid")

    step_id: str = Field(..., description="Identifier of the executed step")
    agent_id: str = Field(..., description="Canonical ID of the assigned agent")
    status: WorkflowStepStatus = Field(..., description="Step lifecycle status")
    execution_id: uuid.UUID | None = Field(
        default=None,
        description="Audit execution UUID emitted by AgentExecutor, or None if skipped",
    )
    error: AgentErrorDetail | None = Field(
        default=None,
        description="Error details if step status is FAILED",
    )
    skip_reason: str | None = Field(
        default=None,
        description="Explanation if step status is SKIPPED",
    )
    started_at: datetime | None = Field(
        default=None,
        description="Timestamp when step started",
    )
    completed_at: datetime | None = Field(
        default=None,
        description="Timestamp when step completed",
    )

    @classmethod
    def from_step_result(cls, step_res: WorkflowStepResult) -> "WorkflowStepResultResponse":
        return cls(
            step_id=step_res.step_id,
            agent_id=step_res.agent_id,
            status=step_res.status,
            execution_id=step_res.execution_id,
            error=step_res.error,
            skip_reason=step_res.skip_reason,
            started_at=step_res.started_at,
            completed_at=step_res.completed_at,
        )


class WorkflowResultResponse(BaseModel):
    """Sanitized API response envelope representing terminal workflow execution."""

    model_config = ConfigDict(extra="forbid")

    workflow_execution_id: uuid.UUID = Field(
        ...,
        description="Unique correlation UUID for this entire workflow execution run",
    )
    workflow_id: str = Field(..., description="Identifier of executed workflow definition")
    workflow_version: str = Field(..., description="Version of executed workflow definition")
    status: WorkflowStatus = Field(..., description="Deterministic terminal workflow status")
    started_at: datetime = Field(..., description="Timestamp when execution commenced")
    completed_at: datetime = Field(..., description="Timestamp when execution terminated")
    step_results: list[WorkflowStepResultResponse] = Field(
        default_factory=list,
        description="Ordered list of individual step outcomes",
    )
    artifacts: dict[str, Any] = Field(
        default_factory=dict,
        description="Dictionary mapping step_id to validated structured output models",
    )
    errors: list[str] = Field(
        default_factory=list,
        description="List of blocking errors or failure summaries",
    )
    warnings: list[str] = Field(
        default_factory=list,
        description="List of non-blocking advisories or skipped step notices",
    )
    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Execution metadata and step count telemetry (no secrets)",
    )

    @classmethod
    def from_workflow_result(cls, res: WorkflowResult) -> "WorkflowResultResponse":
        """Convert domain WorkflowResult to sanitized API response with JSON-safe artifacts."""
        serialized_artifacts: dict[str, Any] = {}
        for k, v in res.artifacts.items():
            if hasattr(v, "model_dump"):
                serialized_artifacts[k] = v.model_dump(mode="json")
            else:
                serialized_artifacts[k] = v

        return cls(
            workflow_execution_id=res.workflow_execution_id,
            workflow_id=res.workflow_id,
            workflow_version=res.workflow_version,
            status=res.status,
            started_at=res.started_at,
            completed_at=res.completed_at,
            step_results=[
                WorkflowStepResultResponse.from_step_result(step)
                for step in res.step_results
            ],
            artifacts=serialized_artifacts,
            errors=res.errors,
            warnings=res.warnings,
            metadata=res.metadata,
        )
