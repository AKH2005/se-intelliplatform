"""Workflow Execution Entity Model.

Represents a persistent, authoritative audit and outcome record for a multi-agent
workflow execution pipeline run against canonical Project Context.
"""

import uuid
import enum
from datetime import datetime, timezone
from typing import Any
from sqlalchemy import DateTime, Enum, ForeignKey, Index, Integer, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import JSON

from app.models.base import Base, UUIDPrimaryKeyMixin


class WorkflowExecutionStatus(str, enum.Enum):
    """Deterministic states of a multi-agent workflow execution lifecycle."""

    PENDING = "PENDING"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    PARTIAL_SUCCESS = "PARTIAL_SUCCESS"
    FAILED = "FAILED"


# Alias for domain contract compatibility
WorkflowStatus = WorkflowExecutionStatus


class WorkflowExecution(Base, UUIDPrimaryKeyMixin):
    """Authoritative persistent record of a multi-agent workflow execution run.

    Preserves full execution provenance, step-level outcomes, and in-memory artifact
    representations across the SDLC.
    """

    __tablename__ = "workflow_executions"

    workflow_execution_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        unique=True,
        index=True,
        nullable=False,
        doc="Unique correlation UUID for this entire workflow execution run",
    )

    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        doc="Project ID on which this workflow execution was run",
    )

    workflow_id: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
        doc="Canonical identifier of the executed workflow definition",
    )

    workflow_version: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        doc="Semantic version of the executed workflow definition",
    )

    status: Mapped[WorkflowStatus] = mapped_column(
        Enum(WorkflowStatus, name="workflow_execution_status", native_enum=False),
        default=WorkflowStatus.PENDING,
        nullable=False,
        index=True,
        doc="Deterministic terminal or active status of the workflow execution",
    )

    context_snapshot_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("project_context_snapshots.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        doc="UUID of ContextSnapshot if execution was snapshot-backed, else NULL for live context",
    )

    context_version: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
        index=True,
        doc="Sequence number of ContextSnapshot if execution was snapshot-backed, else NULL for live context",
    )

    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
        index=True,
        doc="Timestamp when workflow execution commenced (UTC)",
    )

    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        doc="Timestamp when workflow execution terminated (UTC)",
    )

    step_count: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        doc="Total number of steps defined in the executed pipeline",
    )

    completed_steps: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        doc="Number of steps that completed successfully",
    )

    failed_steps: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        doc="Number of steps that failed execution",
    )

    skipped_steps: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        doc="Number of steps that were skipped due to unmet preconditions",
    )

    artifacts: Mapped[dict[str, Any]] = mapped_column(
        JSON().with_variant(JSONB, "postgresql"),
        default=dict,
        server_default="{}",
        nullable=False,
        doc="Serialized validated domain artifacts produced by completed steps",
    )

    errors: Mapped[list[str]] = mapped_column(
        JSON().with_variant(JSONB, "postgresql"),
        default=list,
        server_default="[]",
        nullable=False,
        doc="List of blocking errors or failure summaries",
    )

    warnings: Mapped[list[str]] = mapped_column(
        JSON().with_variant(JSONB, "postgresql"),
        default=list,
        server_default="[]",
        nullable=False,
        doc="List of non-blocking advisories or skipped step notices",
    )

    metadata_payload: Mapped[dict[str, Any]] = mapped_column(
        "metadata",
        JSON().with_variant(JSONB, "postgresql"),
        default=dict,
        server_default="{}",
        nullable=False,
        doc="Sanitized execution metadata, provenance, and telemetry (no secrets)",
    )

    # Relationships
    project: Mapped["Project"] = relationship("Project")  # noqa: F821
    context_snapshot: Mapped["ContextSnapshot | None"] = relationship("ContextSnapshot")  # noqa: F821

    __table_args__ = (
        Index("ix_workflow_executions_project_status", "project_id", "status"),
        Index("ix_workflow_executions_project_started", "project_id", "started_at"),
    )

    def __repr__(self) -> str:
        return (
            f"<WorkflowExecution id={self.id} workflow={self.workflow_id} "
            f"exec_id={self.workflow_execution_id} status={self.status}>"
        )
