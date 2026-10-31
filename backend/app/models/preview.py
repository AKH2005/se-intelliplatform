"""Preview Runtime Domain Entity Models for TaskFlow & Template Applications."""

import uuid
from typing import Any, Optional
from sqlalchemy import ForeignKey, Index, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin


class PreviewTask(Base, TimestampMixin):
    """Persistent task record for Live Preview applications (TaskFlow, Kanban)."""

    __tablename__ = "preview_tasks"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )

    project_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=True,
        doc="Project UUID owning this task (null for unassigned/template starter tasks)",
    )

    title: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        default="Untitled Task",
    )

    description: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        default="",
    )

    priority: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        default="MEDIUM",
    )

    status: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        default="PENDING",
    )

    due_date: Mapped[str | None] = mapped_column(
        String(64),
        nullable=True,
        default="2026-12-31",
    )

    # Relationships
    project: Mapped[Optional["Project"]] = relationship(  # noqa: F821
        "Project",
        backref="preview_tasks",
    )

    __table_args__ = (
        Index("ix_preview_tasks_project_id", "project_id"),
    )

    def to_dict(self) -> dict[str, Any]:
        """Serialize task to dictionary representation expected by frontend and preview runtime."""
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description or "",
            "priority": self.priority,
            "status": self.status,
            "due_date": self.due_date or "2026-12-31",
            "project_id": str(self.project_id) if self.project_id else "",
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    def __repr__(self) -> str:
        return f"<PreviewTask id={self.id} project_id={self.project_id} title='{self.title}' status='{self.status}'>"


class PreviewScore(Base, TimestampMixin):
    """Persistent score record for Arcade / Snake Game template applications."""

    __tablename__ = "preview_scores"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )

    project_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=True,
        doc="Project UUID owning this score record",
    )

    player_name: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        default="Player 1",
    )

    score: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )

    # Relationships
    project: Mapped[Optional["Project"]] = relationship(  # noqa: F821
        "Project",
        backref="preview_scores",
    )

    __table_args__ = (
        Index("ix_preview_scores_project_id", "project_id"),
        Index("ix_preview_scores_score", "score"),
    )

    def to_dict(self) -> dict[str, Any]:
        """Serialize score to dictionary representation expected by frontend and preview runtime."""
        return {
            "id": self.id,
            "player_name": self.player_name,
            "score": self.score,
            "project_id": str(self.project_id) if self.project_id else "",
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

    def __repr__(self) -> str:
        return f"<PreviewScore id={self.id} project_id={self.project_id} player='{self.player_name}' score={self.score}>"
