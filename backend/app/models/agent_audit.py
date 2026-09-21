"""Agent Execution Audit Entity Model."""

import uuid
from datetime import datetime
from typing import Any
from sqlalchemy import DateTime, Enum, ForeignKey, Index, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import JSON

from app.agents.contracts import AgentExecutionStatus
from app.models.base import Base, UUIDPrimaryKeyMixin


class AgentExecutionAudit(Base, UUIDPrimaryKeyMixin):
    """Authoritative persistent audit log of all agent operations.
    
    Tracks exact Project Context versions consumed by AI operations to guarantee
    reproducibility and complete traceability across the SDLC.
    """

    __tablename__ = "agent_execution_audits"

    execution_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        unique=True,
        index=True,
        nullable=False,
        doc="Unique correlation execution UUID",
    )

    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        doc="Project ID on which this execution occurred",
    )

    agent_id: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
        doc="Canonical ID of the executed agent (e.g. 'requirement-analysis')",
    )

    agent_version: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        doc="Semantic version of the agent code",
    )

    status: Mapped[AgentExecutionStatus] = mapped_column(
        Enum(AgentExecutionStatus, name="agent_execution_status", native_enum=False),
        default=AgentExecutionStatus.PENDING,
        nullable=False,
        index=True,
        doc="Lifecycle state of execution (PENDING, RUNNING, COMPLETED, FAILED)",
    )

    context_version: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        index=True,
        doc="Exact sequence number of the canonical Project Context consumed",
    )

    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        doc="Execution start instant (UTC)",
    )

    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        doc="Execution completion or failure instant (UTC)",
    )

    output_summary: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        doc="High-level sanitized summary of output (no full prompts or sensitive data)",
    )

    error_code: Mapped[str | None] = mapped_column(
        String(64),
        nullable=True,
        doc="Error category code if execution failed",
    )

    error_message: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        doc="Descriptive error explanation if execution failed",
    )

    metadata_payload: Mapped[dict[str, Any]] = mapped_column(
        "metadata",
        JSON().with_variant(JSONB, "postgresql"),
        default=dict,
        server_default="{}",
        nullable=False,
        doc="Execution telemetry, provider info, and latency metrics",
    )

    # Relationships
    project: Mapped["Project"] = relationship("Project")  # noqa: F821

    __table_args__ = (
        Index("ix_agent_audits_project_agent", "project_id", "agent_id"),
        Index("ix_agent_audits_project_status", "project_id", "status"),
    )

    def __repr__(self) -> str:
        return (
            f"<AgentExecutionAudit id={self.id} agent={self.agent_id} "
            f"context_v={self.context_version} status={self.status}>"
        )
