"""Pydantic Contracts and DTOs for Development Versions and Continuous Engineering Loop."""

import enum
import uuid
from datetime import datetime, timezone
from typing import Any
from pydantic import BaseModel, ConfigDict, Field

from app.models.development_version import (
    ChangeCategory,
    ChangeType,
    DevelopmentVersionStatus,
)


class VerificationStatus(str, enum.Enum):
    """Aggregate deterministic verification status."""

    PASSED = "PASSED"
    FAILED = "FAILED"
    PENDING = "PENDING"
    INCOMPLETE = "INCOMPLETE"
    NOT_RUN = "NOT_RUN"


class VerificationRequirementLevel(str, enum.Enum):
    """Whether a verification stage is required or optional."""

    REQUIRED = "REQUIRED"
    OPTIONAL = "OPTIONAL"
    NOT_APPLICABLE = "NOT_APPLICABLE"


class StageVerificationResult(BaseModel):
    """Granular verification outcome for a single SDLC stage."""

    model_config = ConfigDict(extra="forbid")

    stage: str = Field(..., description="Stage name (e.g. static_analysis, sandbox_execution, ai_tests)")
    requirement_level: VerificationRequirementLevel = Field(
        ...,
        description="Whether this stage was REQUIRED, OPTIONAL, or NOT_APPLICABLE",
    )
    status: VerificationStatus = Field(..., description="Stage outcome: PASSED, FAILED, NOT_RUN")
    details: str = Field(..., description="Concise diagnostic details or execution summary")
    error_count: int = Field(default=0, ge=0)
    warning_count: int = Field(default=0, ge=0)
    blocking_issues: list[str] = Field(default_factory=list)


class VerificationSnapshot(BaseModel):
    """Aggregated, deterministic verification snapshot for a software version."""

    model_config = ConfigDict(extra="forbid")

    verification_status: VerificationStatus = Field(
        ...,
        description="Overall aggregate verification status: PASSED or FAILED",
    )
    is_verified: bool = Field(
        ...,
        description="True if all REQUIRED verification stages passed and no blocking errors exist",
    )
    summary: str = Field(..., description="Human-readable synthesis of verification state")
    static_analysis: StageVerificationResult = Field(..., description="Static analysis & linting outcome")
    sandbox_execution: StageVerificationResult = Field(..., description="Isolated Docker sandbox execution outcome")
    ai_tests: StageVerificationResult = Field(..., description="AI test execution outcome")
    failure_analysis: StageVerificationResult = Field(..., description="Failure diagnosis and resolution status")
    browser_validation: StageVerificationResult | None = Field(
        default=None,
        description="Browser-based end-to-end application runtime verification outcome",
    )
    verified_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Timestamp when verification gate was evaluated (UTC)",
    )


class VersionFileSummary(BaseModel):
    """Lightweight summary of a generated file belonging to a version."""

    model_config = ConfigDict(extra="forbid")

    path: str = Field(..., description="Project-relative normalized path")
    size_bytes: int = Field(..., ge=0, description="File size in bytes")
    language: str = Field(default="python", description="Language identifier")
    architecture_component: str | None = Field(default=None)
    requirement_ids: list[str] = Field(default_factory=list)


class DevelopmentVersionResponse(BaseModel):
    """DTO representing an immutable DevelopmentVersion."""

    model_config = ConfigDict(extra="forbid")

    version_id: uuid.UUID = Field(..., description="Version UUID")
    project_id: uuid.UUID = Field(..., description="Project UUID")
    version_number: int = Field(..., ge=1, description="Version number (1, 2, 3...)")
    parent_version_id: uuid.UUID | None = Field(default=None, description="Parent version UUID if remediated")
    workflow_execution_id: uuid.UUID | None = Field(default=None, description="Originating workflow execution UUID")
    artifact_key: str = Field(..., description="Artifact key within WorkflowExecution")
    status: DevelopmentVersionStatus = Field(..., description="Lifecycle status")
    is_active: bool = Field(default=False, description="True if this is the project's current active version")
    content_hash: str = Field(..., description="SHA-256 hash of file contents")
    manifest_hash: str = Field(..., description="SHA-256 hash of manifest paths")
    file_count: int = Field(..., ge=0)
    total_size_bytes: int = Field(..., ge=0)
    source_reason: str = Field(..., description="Why this version was created")
    created_by: str = Field(..., description="Agent or user identifier")
    requirement_ids: list[str] = Field(default_factory=list)
    files_manifest: list[VersionFileSummary] = Field(default_factory=list)
    verification_summary: VerificationSnapshot | None = Field(default=None)
    diagnosis_reference: str | None = Field(default=None)
    remediation_reference: str | None = Field(default=None)
    created_at: datetime = Field(...)

    @property
    def id(self) -> uuid.UUID:
        """Alias for version_id for uniform object access."""
        return self.version_id


class DevelopmentVersionListResponse(BaseModel):
    """Paginated or complete list of development versions for a project."""

    model_config = ConfigDict(extra="forbid")

    items: list[DevelopmentVersionResponse] = Field(default_factory=list)
    total: int = Field(..., ge=0)
    active_version_id: uuid.UUID | None = Field(default=None)


class DevelopmentChangeResponse(BaseModel):
    """DTO representing an audit log entry for a version transition."""

    model_config = ConfigDict(extra="forbid")

    change_id: uuid.UUID = Field(...)
    project_id: uuid.UUID = Field(...)
    parent_version_id: uuid.UUID | None = Field(default=None)
    resulting_version_id: uuid.UUID = Field(...)
    change_category: ChangeCategory = Field(...)
    change_type: ChangeType = Field(...)
    reason: str = Field(...)
    diagnosis_id: str | None = Field(default=None)
    remediation_proposal_id: str | None = Field(default=None)
    approved_by: str | None = Field(default=None)
    approved_at: datetime | None = Field(default=None)
    created_at: datetime = Field(...)


class VersionFileDiff(BaseModel):
    """Deterministic diff record for a single file between two versions."""

    model_config = ConfigDict(extra="forbid")

    path: str = Field(...)
    change_type: str = Field(..., description="ADDED, REMOVED, MODIFIED, or UNCHANGED")
    size_delta_bytes: int = Field(...)
    unified_diff: str | None = Field(default=None, description="Unified textual diff if modified")


class VersionComparisonResponse(BaseModel):
    """Deterministic comparison between two development versions."""

    model_config = ConfigDict(extra="forbid")

    from_version_id: uuid.UUID = Field(...)
    to_version_id: uuid.UUID = Field(...)
    from_version_number: int = Field(...)
    to_version_number: int = Field(...)
    files_added: list[VersionFileDiff] = Field(default_factory=list)
    files_removed: list[VersionFileDiff] = Field(default_factory=list)
    files_modified: list[VersionFileDiff] = Field(default_factory=list)
    files_unchanged_count: int = Field(default=0, ge=0)
    requirements_added: list[str] = Field(default_factory=list)
    requirements_removed: list[str] = Field(default_factory=list)
    verification_change_summary: str = Field(...)
    diagnosis_reference: str | None = Field(default=None)
    remediation_proposal_id: str | None = Field(default=None)


class ActivateVersionRequest(BaseModel):
    """Request payload to explicitly activate a verified software version."""

    model_config = ConfigDict(extra="forbid")

    reason: str | None = Field(
        default=None,
        max_length=500,
        description="Optional human-readable activation reason",
    )


class RollbackVersionRequest(BaseModel):
    """Request payload to roll back active version pointer to an earlier verified version."""

    model_config = ConfigDict(extra="forbid")

    reason: str | None = Field(
        default=None,
        max_length=500,
        description="Optional justification for rolling back to this version",
    )


class RunVerificationRequest(BaseModel):
    """Request payload to re-evaluate or refresh the verification gate."""

    model_config = ConfigDict(extra="forbid")

    force: bool = Field(
        default=False,
        description="Force re-evaluation of verification status",
    )
