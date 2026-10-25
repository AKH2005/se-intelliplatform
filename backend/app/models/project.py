"""Project Domain Entity Model."""

import enum
import uuid
from typing import Any
from sqlalchemy import Enum, ForeignKey, Index, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
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

    owner_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        doc="User UUID owning this project (null for legacy/unowned)",
    )

    settings: Mapped[dict[str, Any]] = mapped_column(
        JSON().with_variant(JSONB, "postgresql"),
        default=dict,
        nullable=False,
        server_default="{}",
    )

    # Relationships
    owner: Mapped["User | None"] = relationship(  # noqa: F821
        "User",
        back_populates="projects",
    )
    requirements: Mapped[list["Requirement"]] = relationship(  # noqa: F821
        "Requirement",
        back_populates="project",
        cascade="all, delete-orphan",
        order_by="Requirement.created_at.desc()",
    )
    context_snapshots: Mapped[list["ContextSnapshot"]] = relationship(  # noqa: F821
        "ContextSnapshot",
        back_populates="project",
        cascade="all, delete-orphan",
        order_by="ContextSnapshot.version.desc()",
    )
    environments: Mapped[list["Environment"]] = relationship(  # noqa: F821
        "Environment",
        back_populates="project",
        cascade="all, delete-orphan",
        order_by="Environment.created_at.asc()",
    )

    __table_args__ = (
        Index("ix_projects_slug_status", "slug", "status"),
    )

    def __repr__(self) -> str:
        return f"<Project id={self.id} slug={self.slug} status={self.status}>"
