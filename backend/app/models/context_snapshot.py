"""Project Context Snapshot Entity Model."""

import uuid
from datetime import datetime, timezone
from typing import Any
from sqlalchemy import DateTime, ForeignKey, Index, Integer, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import JSON

from app.models.base import Base, UUIDPrimaryKeyMixin


class ContextSnapshot(Base, UUIDPrimaryKeyMixin):
    """Immutable point-in-time snapshot of canonical Project Context.
    
    Once created, a ContextSnapshot is NEVER modified. All future SDLC intelligence
    agents consume versioned snapshots as an immutable, reproducible source of truth.
    """

    __tablename__ = "project_context_snapshots"

    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    version: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        doc="Sequential version number for this project (1, 2, 3, ...)",
    )

    context_data: Mapped[dict[str, Any]] = mapped_column(
        JSON().with_variant(JSONB, "postgresql"),
        nullable=False,
        doc="Serialized canonical ProjectContextResponse dictionary",
    )

    summary: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
        doc="Optional engineer/system description of this snapshot milestone",
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
        doc="Timestamp when this immutable snapshot was committed",
    )

    # Relationship to project
    project: Mapped["Project"] = relationship("Project", back_populates="context_snapshots")  # noqa: F821

    __table_args__ = (
        UniqueConstraint("project_id", "version", name="uq_project_context_snapshot_version"),
        Index("ix_project_context_snapshots_project_version", "project_id", "version"),
    )

    def __repr__(self) -> str:
        return (
            f"<ContextSnapshot id={self.id} project_id={self.project_id} "
            f"version={self.version} created_at={self.created_at}>"
        )
