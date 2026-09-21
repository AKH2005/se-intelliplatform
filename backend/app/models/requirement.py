"""Requirement Domain Entity Model."""

import enum
import uuid
from sqlalchemy import Boolean, Enum, ForeignKey, Index, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class RequirementType(str, enum.Enum):
    """Categorization of requirement scope and nature."""
    FUNCTIONAL = "FUNCTIONAL"
    NON_FUNCTIONAL = "NON_FUNCTIONAL"
    CONSTRAINT = "CONSTRAINT"


class RequirementPriority(str, enum.Enum):
    """Business priority of the requirement."""
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class RequirementStatus(str, enum.Enum):
    """Lifecycle status of the requirement."""
    DRAFT = "DRAFT"
    APPROVED = "APPROVED"
    IMPLEMENTED = "IMPLEMENTED"
    DEFERRED = "DEFERRED"
    REJECTED = "REJECTED"


class Requirement(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Authoritative persistent Requirement entity."""

    __tablename__ = "requirements"

    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    title: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        index=True,
    )

    description: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    type: Mapped[RequirementType] = mapped_column(
        Enum(RequirementType, name="requirement_type", native_enum=False),
        default=RequirementType.FUNCTIONAL,
        nullable=False,
        index=True,
    )

    priority: Mapped[RequirementPriority] = mapped_column(
        Enum(RequirementPriority, name="requirement_priority", native_enum=False),
        default=RequirementPriority.MEDIUM,
        nullable=False,
        index=True,
    )

    status: Mapped[RequirementStatus] = mapped_column(
        Enum(RequirementStatus, name="requirement_status", native_enum=False),
        default=RequirementStatus.DRAFT,
        nullable=False,
        index=True,
    )

    is_archived: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        index=True,
    )

    # Relationships
    project: Mapped["Project"] = relationship("Project", back_populates="requirements")  # noqa: F821

    __table_args__ = (
        Index("ix_requirements_project_status", "project_id", "status"),
        Index("ix_requirements_project_type", "project_id", "type"),
        Index("ix_requirements_project_priority", "project_id", "priority"),
        Index("ix_requirements_project_archived", "project_id", "is_archived"),
    )

    def __repr__(self) -> str:
        return (
            f"<Requirement id={self.id} project_id={self.project_id} "
            f"title='{self.title[:30]}' type={self.type} status={self.status}>"
        )
