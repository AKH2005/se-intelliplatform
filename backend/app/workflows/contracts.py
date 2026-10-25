"""Core Contracts, Enums, and Structured Envelopes for Workflow Orchestration."""

import enum
import uuid
from datetime import datetime, timezone
from typing import Any
from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.agents.contracts import AgentErrorDetail, AgentExecutionStatus, AgentResult
from app.agents.code_review.contracts import CodeReviewInput
from app.schemas.context import ProjectContextResponse


class WorkflowStatus(str, enum.Enum):
    """Deterministic states of a multi-agent workflow lifecycle."""

    PENDING = "PENDING"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    PARTIAL_SUCCESS = "PARTIAL_SUCCESS"
    FAILED = "FAILED"


class WorkflowStepStatus(str, enum.Enum):
    """Deterministic lifecycle state of an individual workflow step."""

    PENDING = "PENDING"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    SKIPPED = "SKIPPED"


class WorkflowStep(BaseModel):
    """Specification of an individual step within a workflow definition."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    step_id: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Unique identifier for the step within its parent workflow",
        examples=["step-req-analysis"],
    )
    agent_id: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Canonical ID of the agent to execute (must exist in AgentRegistry)",
        examples=["requirement-analysis"],
    )
    required: bool = Field(
        default=True,
        description="If True, step failure or skip causes workflow failure. If False, failure permits partial success.",
    )
    depends_on: list[str] = Field(
        default_factory=list,
        description="List of prerequisite step_ids that must execute before this step",
    )
    description: str | None = Field(
        default=None,
        max_length=500,
        description="Optional human-readable description of step intent",
    )
    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Optional step configuration and routing directives",
    )


class WorkflowDefinition(BaseModel):
    """Authoritative, declarative specification of a multi-agent workflow."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    workflow_id: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Canonical identifier for the workflow pipeline",
        examples=["software-design-workflow"],
    )
    version: str = Field(
        ...,
        pattern=r"^\d+\.\d+\.\d+$",
        description="Semantic version of the workflow definition",
        examples=["1.0.0"],
    )
    name: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description="Human-readable name of the workflow",
    )
    description: str = Field(
        ...,
        min_length=5,
        description="Detailed explanation of the workflow's purpose and output",
    )
    steps: list[WorkflowStep] = Field(
        ...,
        min_length=1,
        description="Ordered sequence of workflow steps to evaluate and execute",
    )

    @model_validator(mode="after")
    def validate_step_graph(self) -> "WorkflowDefinition":
        """Deterministic invariant checks:
        1. All step_ids must be unique within the workflow.
        2. All depends_on entries must reference a preceding step_id (no forward or circular refs).
        """
        seen_ids: set[str] = set()
        for idx, step in enumerate(self.steps):
            if step.step_id in seen_ids:
                raise ValueError(
                    f"Duplicate step_id '{step.step_id}' found in workflow '{self.workflow_id}'."
                )
            seen_ids.add(step.step_id)

            # Dependencies must exist and appear BEFORE the dependent step (guarantees topological order)
            preceding_ids = {s.step_id for s in self.steps[:idx]}
            for dep in step.depends_on:
                if dep == step.step_id:
                    raise ValueError(
                        f"Step '{step.step_id}' cannot depend on itself."
                    )
                if dep not in preceding_ids:
                    raise ValueError(
                        f"Step '{step.step_id}' depends on '{dep}', which is not defined prior to it in the steps list."
                    )
        return self


class WorkflowInput(BaseModel):
    """Typed input payload envelope consumed by a workflow execution run.

    Provides canonical Project Context and optional external inputs required by specific agents.
    """

    model_config = ConfigDict(arbitrary_types_allowed=True, extra="forbid")

    context: ProjectContextResponse = Field(
        ...,
        description="Authoritative canonical ProjectContextResponse for the target project",
    )
    code_review_input: CodeReviewInput | None = Field(
        default=None,
        description="Optional source code files payload required if CodeReviewAgent is executed",
    )
    explainability_target_scope: str | None = Field(
        default=None,
        max_length=500,
        description="Optional focus scope passed to ExplainabilityAgent",
    )
    explainability_user_query: str | None = Field(
        default=None,
        max_length=1000,
        description="Optional natural-language developer question passed to ExplainabilityAgent",
    )
    browser_journey_input: Any | None = Field(
        default=None,
        description="Optional input payload required if BrowserJourneyGenerationAgent is executed",
    )
    options: dict[str, Any] = Field(
        default_factory=dict,
        description="Sanitized workflow runtime options (e.g. timeout, feature flags)",
    )
    initial_artifacts: dict[str, Any] = Field(
        default_factory=dict,
        description="Pre-seeded upstream artifacts from prior workflow stages",
    )


class WorkflowStepResult(BaseModel):
    """Deterministic outcome of a single workflow step execution."""

    model_config = ConfigDict(arbitrary_types_allowed=True, extra="forbid")

    step_id: str = Field(..., description="Identifier of the executed workflow step")
    agent_id: str = Field(..., description="Canonical ID of the agent assigned to this step")
    status: WorkflowStepStatus = Field(..., description="Lifecycle status of this step")
    execution_id: uuid.UUID | None = Field(
        default=None,
        description="Correlation execution UUID emitted by AgentExecutor, or None if skipped",
    )
    agent_result: AgentResult[Any] | None = Field(
        default=None,
        description="Full structured AgentResult envelope if executed, or None if skipped",
    )
    error: AgentErrorDetail | None = Field(
        default=None,
        description="Failure details if step status is FAILED",
    )
    skip_reason: str | None = Field(
        default=None,
        description="Deterministic explanation if step status is SKIPPED",
    )
    started_at: datetime | None = Field(
        default=None,
        description="Timestamp when step execution commenced",
    )
    completed_at: datetime | None = Field(
        default=None,
        description="Timestamp when step execution terminated",
    )


class WorkflowResult(BaseModel):
    """Authoritative structured output envelope for a completed workflow execution.

    Maintains full execution provenance, per-step outcomes, and in-memory artifact references.
    """

    model_config = ConfigDict(arbitrary_types_allowed=True, extra="forbid")

    workflow_execution_id: uuid.UUID = Field(
        ...,
        description="Unique correlation UUID for this entire workflow execution run",
    )
    workflow_id: str = Field(..., description="Identifier of the executed workflow definition")
    workflow_version: str = Field(..., description="Version of the executed workflow definition")
    status: WorkflowStatus = Field(..., description="Final deterministic status of the workflow")
    started_at: datetime = Field(..., description="Timestamp when workflow run commenced")
    completed_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Timestamp when workflow run terminated",
    )
    step_results: list[WorkflowStepResult] = Field(
        default_factory=list,
        description="Ordered list of individual step execution outcomes",
    )
    artifacts: dict[str, Any] = Field(
        default_factory=dict,
        description="Map of step_id -> validated domain output model for completed steps",
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
        description="Sanitized workflow execution metadata and telemetry (no secrets)",
    )
