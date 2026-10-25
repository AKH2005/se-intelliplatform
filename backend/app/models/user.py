"""User Domain Entity Model for Authentication and Multi-Tenancy."""

import enum
import uuid
from typing import TYPE_CHECKING
from sqlalchemy import Boolean, Enum, Index, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.project import Project


class UserRole(str, enum.Enum):
    """User authorization roles."""
    ADMIN = "admin"
    DEVELOPER = "developer"
    USER = "user"


class User(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Authoritative User persistent entity."""

    __tablename__ = "users"

    email: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        index=True,
        nullable=False,
        doc="Unique user email address",
    )

    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        doc="Full display name of user",
    )

    hashed_password: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        doc="Bcrypt salted password hash",
    )

    role: Mapped[UserRole] = mapped_column(
        Enum(UserRole, name="user_role", native_enum=False),
        default=UserRole.USER,
        nullable=False,
        doc="Authorization role",
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
        doc="Active account status flag",
    )

    # Relationships
    projects: Mapped[list["Project"]] = relationship(
        "Project",
        back_populates="owner",
        cascade="all, delete-orphan",
        order_by="Project.created_at.desc()",
    )

    __table_args__ = (
        Index("ix_users_email_is_active", "email", "is_active"),
    )

    def __repr__(self) -> str:
        return f"<User id={self.id} email={self.email} role={self.role}>"
