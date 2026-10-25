"""Development Version and Development Change Persistent Entity Models for Phase 11H."""

import enum
import uuid
from datetime import datetime, timezone
from typing import Any
from sqlalchemy import DateTime, Enum, ForeignKey, Index, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import JSON

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class DevelopmentVersionStatus(str, enum.Enum):
    """Controlled lifecycle states for a development software version."""

    GENERATED = "GENERATED"
    VERIFIED = "VERIFIED"
    FAILED_VERIFICATION = "FAILED_VERIFICATION"
    SUPERSEDED = "SUPERSEDED"
    REJECTED = "REJECTED"


class ChangeCategory(str, enum.Enum):
    """Epistemic classification of development changes."""

    CODE_PRODUCING = "CODE_PRODUCING"
    LIFECYCLE_EVENT = "LIFECYCLE_EVENT"


class ChangeType(str, enum.Enum):
    """Categorical type of change between versions."""

    INITIAL_CREATION = "INITIAL_CREATION"
    REMEDIATION_PATCH = "REMEDIATION_PATCH"
    ACTIVATION = "ACTIVATION"
    ROLLBACK = "ROLLBACK"


class DevelopmentVersion(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Authoritative persistent record of an immutable software version."""

    __tablename__ = "development_versions"

    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        doc="Project UUID owning this version",
    )

    version_number: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        doc="Monotonically increasing version number for the project (1, 2, 3...)",
    )

    parent_version_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("development_versions.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        doc="Preceding version UUID if produced from an earlier version",
    )

    workflow_execution_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("workflow_executions.workflow_execution_id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        doc="Originating WorkflowExecution UUID providing authoritative artifacts",
    )

    artifact_key: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        default="code-generation",
        doc="Key within WorkflowExecution.artifacts containing the code artifact",
    )

    status: Mapped[DevelopmentVersionStatus] = mapped_column(
        Enum(DevelopmentVersionStatus, name="development_version_status", native_enum=False),
        default=DevelopmentVersionStatus.GENERATED,
        nullable=False,
        index=True,
        doc="Current lifecycle state of this software version",
    )

    content_hash: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        doc="Deterministic SHA-256 hash of sorted file paths and contents",
    )

    manifest_hash: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        doc="Deterministic SHA-256 hash of project file manifest",
    )

    file_count: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        doc="Total number of generated files in this version",
    )

    total_size_bytes: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        doc="Total size of all files in bytes",
    )

    source_reason: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
        default="INITIAL_GENERATION",
        doc="Reason why this version was synthesized (e.g. INITIAL_GENERATION, REMEDIATION_PATCH)",
    )

    created_by: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        default="system",
        doc="Identity or agent responsible for creating this version",
    )

    requirement_ids: Mapped[list[str]] = mapped_column(
        JSON().with_variant(JSONB, "postgresql"),
        default=list,
        server_default="[]",
        nullable=False,
        doc="Traceable requirement UUIDs satisfied by this version",
    )

    files_manifest: Mapped[list[dict[str, Any]]] = mapped_column(
        JSON().with_variant(JSONB, "postgresql"),
        default=list,
        server_default="[]",
        nullable=False,
        doc="Lightweight metadata manifest of files (path, size, language, req_ids)",
    )

    verification_summary: Mapped[dict[str, Any] | None] = mapped_column(
        JSON().with_variant(JSONB, "postgresql"),
        nullable=True,
        doc="Aggregated deterministic verification snapshot outcome",
    )

    diagnosis_reference: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        doc="Correlation ID of FailureDiagnosis that initiated this change if remediated",
    )

    remediation_reference: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        doc="Correlation ID of RemediationProposal that synthesized this version if remediated",
    )

    metadata_payload: Mapped[dict[str, Any]] = mapped_column(
        "metadata",
        JSON().with_variant(JSONB, "postgresql"),
        default=dict,
        server_default="{}",
        nullable=False,
        doc="Execution metadata and environment flags",
    )

    # Relationships
    project: Mapped["Project"] = relationship("Project")  # noqa: F821
    parent_version: Mapped["DevelopmentVersion | None"] = relationship(
        "DevelopmentVersion",
        remote_side="DevelopmentVersion.id",
    )

    __table_args__ = (
        Index("ix_development_versions_project_number", "project_id", "version_number", unique=True),
        Index("ix_development_versions_project_status", "project_id", "status"),
    )

    def __repr__(self) -> str:
        return (
            f"<DevelopmentVersion id={self.id} project_id={self.project_id} "
            f"v={self.version_number} status={self.status}>"
        )


class DevelopmentChange(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Authoritative audit record of a version transition or lifecycle event."""

    __tablename__ = "development_changes"

    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        doc="Project UUID owning this change",
    )

    parent_version_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("development_versions.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        doc="Preceding version UUID if applicable",
    )

    resulting_version_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("development_versions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        doc="Resulting version UUID associated with this change",
    )

    change_category: Mapped[ChangeCategory] = mapped_column(
        Enum(ChangeCategory, name="change_category", native_enum=False),
        nullable=False,
        doc="CODE_PRODUCING vs LIFECYCLE_EVENT",
    )

    change_type: Mapped[ChangeType] = mapped_column(
        Enum(ChangeType, name="change_type", native_enum=False),
        nullable=False,
        doc="INITIAL_CREATION, REMEDIATION_PATCH, ACTIVATION, or ROLLBACK",
    )

    reason: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        doc="Human-readable justification or event reason",
    )

    diagnosis_id: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        doc="Associated failure diagnosis identifier if applicable",
    )

    remediation_proposal_id: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        doc="Associated remediation proposal identifier if applicable",
    )

    approved_by: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
        doc="User or approver identifier",
    )

    approved_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        doc="Timestamp of human approval if applicable",
    )

    metadata_payload: Mapped[dict[str, Any]] = mapped_column(
        "metadata",
        JSON().with_variant(JSONB, "postgresql"),
        default=dict,
        server_default="{}",
        nullable=False,
        doc="Additional telemetry and event metadata",
    )

    # Relationships
    project: Mapped["Project"] = relationship("Project")  # noqa: F821
    resulting_version: Mapped["DevelopmentVersion"] = relationship(
        "DevelopmentVersion",
        foreign_keys=[resulting_version_id],
    )

    __table_args__ = (
        Index("ix_development_changes_project_created", "project_id", "created_at"),
    )

    def __repr__(self) -> str:
        return (
            f"<DevelopmentChange id={self.id} project_id={self.project_id} "
            f"type={self.change_type} resulting_v={self.resulting_version_id}>"
        )
