"""Project Domain Entity Model."""

import enum
from typing import Any
from sqlalchemy import Enum, Index, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import JSON

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class ProjectStatus(str, enum.Enum):
    """Lifecycle status enum for projects."""
    DRAFT = "DRAFT"
    IN_PROGRESS = "IN_PROGRESS"
    ARCHIVED = "ARCHIVED"


class Project(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Authoritative Project persistent entity."""

    __tablename__ = "projects"

    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        index=True,
    )

    slug: Mapped[str] = mapped_column(
        String(100),
        unique=True,
        index=True,
        nullable=False,
    )

    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    status: Mapped[ProjectStatus] = mapped_column(
        Enum(ProjectStatus, name="project_status", native_enum=False),
        default=ProjectStatus.DRAFT,
        nullable=False,
        index=True,
    )

    settings: Mapped[dict[str, Any]] = mapped_column(
        JSON().with_variant(JSONB, "postgresql"),
        default=dict,
        nullable=False,
        server_default="{}",
    )

    __table_args__ = (
        Index("ix_projects_slug_status", "slug", "status"),
    )

    def __repr__(self) -> str:
        return f"<Project id={self.id} slug={self.slug} status={self.status}>"
