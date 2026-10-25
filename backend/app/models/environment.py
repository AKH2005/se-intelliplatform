"""Multi-Environment and Deployment Persistent Entity Models for Phase 13."""

from datetime import datetime, timezone
import enum
from typing import Any
import uuid
from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, Index, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import JSON

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class EnvironmentType(str, enum.Enum):
    """Authoritative controlled types of environments per project."""

    DEVELOPMENT = "DEVELOPMENT"
    STAGING = "STAGING"
    PRODUCTION = "PRODUCTION"


class EnvironmentStatus(str, enum.Enum):
    """Operational status of a deployment environment."""

    HEALTHY = "HEALTHY"
    DEGRADED = "DEGRADED"
    DEPLOYING = "DEPLOYING"
    FAILED = "FAILED"
    MAINTENANCE = "MAINTENANCE"


class DeploymentStatus(str, enum.Enum):
    """Lifecycle progression states for a deployment run."""

    REQUESTED = "REQUESTED"
    VALIDATING = "VALIDATING"
    DEPLOYING = "DEPLOYING"
    VERIFYING = "VERIFYING"
    SUCCEEDED = "SUCCEEDED"
    FAILED = "FAILED"
    ROLLED_BACK = "ROLLED_BACK"
    CANCELLED = "CANCELLED"


class DeploymentOperation(str, enum.Enum):
    """Categorical operation represented by a deployment execution."""

    DEPLOYMENT = "DEPLOYMENT"
    PROMOTION = "PROMOTION"
    ROLLBACK = "ROLLBACK"


class Environment(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Authoritative persistent record of a project deployment environment."""

    __tablename__ = "environments"

    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        doc="Project UUID owning this environment",
    )

    environment_type: Mapped[EnvironmentType] = mapped_column(
        Enum(EnvironmentType, name="environment_type", native_enum=False),
        nullable=False,
        doc="Controlled environment type: DEVELOPMENT, STAGING, or PRODUCTION",
    )

    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        doc="Display name for the environment",
    )

    status: Mapped[EnvironmentStatus] = mapped_column(
        Enum(EnvironmentStatus, name="environment_status", native_enum=False),
        default=EnvironmentStatus.HEALTHY,
        nullable=False,
        doc="Current operational health/state of the environment",
    )

    current_version_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("development_versions.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        doc="Authoritative immutable DevelopmentVersion currently deployed/active in this environment",
    )

    is_production: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        doc="Flag indicating strict production safety gating applies",
    )

    configuration: Mapped[dict[str, Any]] = mapped_column(
        JSON().with_variant(JSONB, "postgresql"),
        default=dict,
        server_default="{}",
        nullable=False,
        doc="Environment runtime configuration, target hosts, replica counts, and health endpoints",
    )

    last_deployed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        doc="Timestamp of the most recent successful deployment or promotion",
    )

    # Relationships
    project: Mapped["Project"] = relationship("Project", back_populates="environments")  # noqa: F821
    current_version: Mapped["DevelopmentVersion | None"] = relationship(  # noqa: F821
        "DevelopmentVersion",
        foreign_keys=[current_version_id],
        lazy="selectin",
    )
    deployments: Mapped[list["DeploymentRecord"]] = relationship(
        "DeploymentRecord",
        back_populates="environment",
        foreign_keys="[DeploymentRecord.environment_id]",
        cascade="all, delete-orphan",
        order_by="DeploymentRecord.created_at.desc()",
    )

    __table_args__ = (
        Index("ix_environments_project_type", "project_id", "environment_type", unique=True),
    )

    def __repr__(self) -> str:
        return (
            f"<Environment id={self.id} project_id={self.project_id} "
            f"type={self.environment_type} current_v={self.current_version_id}>"
        )


class DeploymentRecord(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Authoritative append-only audit trail of environment deployment, promotion, and rollback executions."""

    __tablename__ = "deployment_records"

    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        doc="Project UUID owning this deployment record",
    )

    environment_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("environments.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        doc="Target environment UUID",
    )

    version_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("development_versions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        doc="Target DevelopmentVersion UUID deployed or promoted",
    )

    previous_version_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("development_versions.id", ondelete="SET NULL"),
        nullable=True,
        doc="Previous DevelopmentVersion UUID active before this deployment",
    )

    operation: Mapped[DeploymentOperation] = mapped_column(
        Enum(DeploymentOperation, name="deployment_operation", native_enum=False),
        default=DeploymentOperation.DEPLOYMENT,
        nullable=False,
        doc="Type of operation: DEPLOYMENT, PROMOTION, or ROLLBACK",
    )

    source_environment_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("environments.id", ondelete="SET NULL"),
        nullable=True,
        doc="Source environment UUID if this execution represents a promotion",
    )

    status: Mapped[DeploymentStatus] = mapped_column(
        Enum(DeploymentStatus, name="deployment_status", native_enum=False),
        default=DeploymentStatus.REQUESTED,
        nullable=False,
        doc="Current execution status of the deployment lifecycle",
    )

    requested_by: Mapped[str] = mapped_column(
        String(100),
        default="system",
        nullable=False,
        doc="Actor, user, or service initiating the deployment",
    )

    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
        doc="Timestamp when deployment execution commenced",
    )

    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        doc="Timestamp when deployment reached a terminal state (SUCCEEDED, FAILED, CANCELLED)",
    )

    verification_summary: Mapped[dict[str, Any] | None] = mapped_column(
        JSON().with_variant(JSONB, "postgresql"),
        nullable=True,
        doc="Snapshot of verification and eligibility gates evaluated for this deployment",
    )

    failure_reason: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        doc="Diagnostic explanation if deployment failed or was rejected",
    )

    rollback_target_deployment_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("deployment_records.id", ondelete="SET NULL"),
        nullable=True,
        doc="Reference to prior DeploymentRecord if this is a rollback",
    )

    metadata_payload: Mapped[dict[str, Any]] = mapped_column(
        "metadata",
        JSON().with_variant(JSONB, "postgresql"),
        default=dict,
        server_default="{}",
        nullable=False,
        doc="Deployment telemetry, target container details, and audit metadata",
    )

    # Relationships
    project: Mapped["Project"] = relationship("Project")  # noqa: F821
    environment: Mapped["Environment"] = relationship(
        "Environment",
        back_populates="deployments",
        foreign_keys=[environment_id],
        lazy="selectin",
    )
    source_environment: Mapped["Environment | None"] = relationship(
        "Environment",
        foreign_keys=[source_environment_id],
        lazy="selectin",
    )
    version: Mapped["DevelopmentVersion"] = relationship(  # noqa: F821
        "DevelopmentVersion",
        foreign_keys=[version_id],
        lazy="selectin",
    )
    previous_version: Mapped["DevelopmentVersion | None"] = relationship(  # noqa: F821
        "DevelopmentVersion",
        foreign_keys=[previous_version_id],
        lazy="selectin",
    )

    __table_args__ = (
        Index("ix_deployment_records_project_env_created", "project_id", "environment_id", "created_at"),
    )

    def __repr__(self) -> str:
        return (
            f"<DeploymentRecord id={self.id} project_id={self.project_id} "
            f"env={self.environment_id} op={self.operation} status={self.status}>"
        )
