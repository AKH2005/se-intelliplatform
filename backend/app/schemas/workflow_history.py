"""Pydantic Schemas for Workflow History and Persisted Execution Detail.

Defines client-facing DTOs for listing historical workflow executions,
paginated responses, and granular run details according to RFC 7807 and
platform security invariants.
"""

import uuid
from datetime import datetime
from typing import Any
from pydantic import BaseModel, ConfigDict, Field

from app.models.workflow_execution import WorkflowExecution
from app.workflows.contracts import WorkflowStatus


class WorkflowExecutionSummaryResponse(BaseModel):
    """Sanitized summary DTO for a persisted workflow execution run."""

    model_config = ConfigDict(extra="forbid")

    workflow_execution_id: uuid.UUID = Field(
        ...,
        description="Unique correlation UUID for this entire workflow execution run",
    )
    project_id: uuid.UUID = Field(
        ...,
        description="UUID of the project on which this workflow was executed",
    )
    workflow_id: str = Field(
        ...,
        description="Canonical identifier of the executed workflow",
    )
    workflow_version: str = Field(
        ...,
        description="Semantic version of the executed workflow definition",
    )
    status: WorkflowStatus = Field(
        ...,
        description="Deterministic status of the workflow execution",
    )
    started_at: datetime = Field(
        ...,
        description="Timestamp when execution commenced (UTC)",
    )
    completed_at: datetime | None = Field(
        default=None,
        description="Timestamp when execution terminated (UTC)",
    )
    context_snapshot_id: uuid.UUID | None = Field(
        default=None,
        description="ContextSnapshot UUID if execution was snapshot-backed, else None",
    )
    context_version: int | None = Field(
        default=None,
        description="ContextSnapshot version sequence number if snapshot-backed, else None",
    )
    step_count: int = Field(
        ...,
        description="Total steps defined in this pipeline",
    )
    completed_steps: int = Field(
        ...,
        description="Count of steps that completed successfully",
    )
    failed_steps: int = Field(
        ...,
        description="Count of steps that failed",
    )
    skipped_steps: int = Field(
        ...,
        description="Count of steps that were skipped",
    )
    error_count: int = Field(
        ...,
        description="Count of blocking errors",
    )
    warning_count: int = Field(
        ...,
        description="Count of non-blocking advisories or skip notices",
    )
    artifact_keys: list[str] = Field(
        default_factory=list,
        description="List of step IDs for which validated domain artifacts exist",
    )

    @classmethod
    def from_orm_model(cls, record: WorkflowExecution) -> "WorkflowExecutionSummaryResponse":
        """Transform an ORM WorkflowExecution entity into a safe summary DTO."""
        artifacts_dict = record.artifacts or {}
        errors_list = record.errors or []
        warnings_list = record.warnings or []

        return cls(
            workflow_execution_id=record.workflow_execution_id,
            project_id=record.project_id,
            workflow_id=record.workflow_id,
            workflow_version=record.workflow_version,
            status=record.status,
            started_at=record.started_at,
            completed_at=record.completed_at,
            context_snapshot_id=record.context_snapshot_id,
            context_version=record.context_version,
            step_count=record.step_count,
            completed_steps=record.completed_steps,
            failed_steps=record.failed_steps,
            skipped_steps=record.skipped_steps,
            error_count=len(errors_list),
            warning_count=len(warnings_list),
            artifact_keys=sorted(list(artifacts_dict.keys())),
        )


class WorkflowHistoryListResponse(BaseModel):
    """Paginated list of historical workflow execution summaries."""

    model_config = ConfigDict(extra="forbid")

    items: list[WorkflowExecutionSummaryResponse] = Field(
        default_factory=list,
        description="List of workflow execution summaries ordered newest first",
    )
    total: int = Field(
        ...,
        ge=0,
        description="Total number of matching workflow execution records",
    )
    limit: int = Field(
        ...,
        ge=1,
        le=100,
        description="Pagination limit applied to this request",
    )
    offset: int = Field(
        ...,
        ge=0,
        description="Pagination offset applied to this request",
    )


class WorkflowExecutionDetailResponse(BaseModel):
    """Authoritative sanitized representation of a completed/persisted workflow execution."""

    model_config = ConfigDict(extra="forbid")

    workflow_execution_id: uuid.UUID = Field(
        ...,
        description="Unique correlation UUID for this entire workflow execution run",
    )
    project_id: uuid.UUID = Field(
        ...,
        description="UUID of the project on which this workflow was executed",
    )
    workflow_id: str = Field(
        ...,
        description="Canonical identifier of the executed workflow",
    )
    workflow_version: str = Field(
        ...,
        description="Semantic version of the executed workflow definition",
    )
    status: WorkflowStatus = Field(
        ...,
        description="Deterministic terminal status of the workflow execution",
    )
    started_at: datetime = Field(
        ...,
        description="Timestamp when execution commenced (UTC)",
    )
    completed_at: datetime | None = Field(
        default=None,
        description="Timestamp when execution terminated (UTC)",
    )
    context_snapshot_id: uuid.UUID | None = Field(
        default=None,
        description="ContextSnapshot UUID if snapshot-backed, else None",
    )
    context_version: int | None = Field(
        default=None,
        description="ContextSnapshot version sequence number if snapshot-backed, else None",
    )
    step_count: int = Field(
        ...,
        description="Total steps defined in this pipeline",
    )
    completed_steps: int = Field(
        ...,
        description="Count of steps that completed successfully",
    )
    failed_steps: int = Field(
        ...,
        description="Count of steps that failed",
    )
    skipped_steps: int = Field(
        ...,
        description="Count of steps that were skipped",
    )
    artifacts: dict[str, Any] = Field(
        default_factory=dict,
        description="Serialized validated domain artifacts produced by completed steps",
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
        description="Sanitized execution metadata, provenance, and telemetry (no secrets)",
    )

    @classmethod
    def from_orm_model(cls, record: WorkflowExecution) -> "WorkflowExecutionDetailResponse":
        """Transform an ORM WorkflowExecution entity into a safe execution detail DTO."""
        return cls(
            workflow_execution_id=record.workflow_execution_id,
            project_id=record.project_id,
            workflow_id=record.workflow_id,
            workflow_version=record.workflow_version,
            status=record.status,
            started_at=record.started_at,
            completed_at=record.completed_at,
            context_snapshot_id=record.context_snapshot_id,
            context_version=record.context_version,
            step_count=record.step_count,
            completed_steps=record.completed_steps,
            failed_steps=record.failed_steps,
            skipped_steps=record.skipped_steps,
            artifacts=record.artifacts or {},
            errors=record.errors or [],
            warnings=record.warnings or [],
            metadata=record.metadata_payload or {},
        )
