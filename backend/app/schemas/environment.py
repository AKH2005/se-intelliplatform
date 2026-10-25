"""Pydantic Request and Response Schemas for Multi-Environment Development & Deployment (Phase 13)."""

from datetime import datetime
from typing import Any
import uuid
from pydantic import BaseModel, ConfigDict, Field

from app.models.environment import (
    DeploymentOperation,
    DeploymentStatus,
    EnvironmentStatus,
    EnvironmentType,
)


class EnvironmentResponse(BaseModel):
    """Schema representing an environment's state and active version pointer."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    project_id: uuid.UUID
    environment_type: EnvironmentType
    name: str
    status: EnvironmentStatus
    current_version_id: uuid.UUID | None = None
    current_version_number: int | None = None
    current_version_status: str | None = None
    current_version_hash: str | None = None
    is_production: bool
    configuration: dict[str, Any] = Field(default_factory=dict)
    last_deployed_at: datetime | None = None
    created_at: datetime
    updated_at: datetime


class DeploymentRecordResponse(BaseModel):
    """Schema representing a deployment, promotion, or rollback execution record."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    project_id: uuid.UUID
    environment_id: uuid.UUID
    environment_type: EnvironmentType
    version_id: uuid.UUID
    version_number: int | None = None
    previous_version_id: uuid.UUID | None = None
    previous_version_number: int | None = None
    operation: DeploymentOperation
    source_environment_id: uuid.UUID | None = None
    source_environment_type: EnvironmentType | None = None
    status: DeploymentStatus
    requested_by: str
    started_at: datetime
    completed_at: datetime | None = None
    verification_summary: dict[str, Any] | None = None
    failure_reason: str | None = None
    rollback_target_deployment_id: uuid.UUID | None = None
    metadata_payload: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime


class PromotionEligibilityRequest(BaseModel):
    """Query schema for evaluating whether a version is eligible for promotion."""

    version_id: uuid.UUID = Field(..., description="Target DevelopmentVersion UUID")
    target_environment: EnvironmentType = Field(..., description="Destination environment type (STAGING or PRODUCTION)")
    source_environment: EnvironmentType | None = Field(default=None, description="Optional origin environment type")


class PromotionEligibilityResponse(BaseModel):
    """Authoritative deterministic outcome of promotion eligibility evaluation."""

    eligible: bool = Field(..., description="True if version satisfies all promotion policy gates")
    version_id: uuid.UUID
    version_number: int
    source_environment: EnvironmentType
    target_environment: EnvironmentType
    reasons: list[str] = Field(default_factory=list, description="Explanatory reasons for eligibility verdict")
    passed_checks: list[str] = Field(default_factory=list, description="Checklist of verified prerequisite criteria")
    failed_checks: list[str] = Field(default_factory=list, description="Checklist of failed or missing criteria")
    warnings: list[str] = Field(default_factory=list, description="Advisory observations (e.g. non-blocking warnings)")
    requires_confirmation: bool = Field(default=True, description="Always True for mutating promotion actions")


class PromoteVersionRequest(BaseModel):
    """Payload to trigger promotion of a version to a target environment."""

    version_id: uuid.UUID = Field(..., description="DevelopmentVersion UUID to promote")
    target_environment: EnvironmentType = Field(..., description="Destination environment type (STAGING or PRODUCTION)")
    source_environment: EnvironmentType | None = Field(default=None, description="Optional source environment type")
    requested_by: str = Field(default="user", max_length=100)
    notes: str | None = Field(default=None, max_length=512)


class DeployVersionRequest(BaseModel):
    """Payload to directly deploy a verified version to an environment."""

    version_id: uuid.UUID = Field(..., description="DevelopmentVersion UUID to deploy")
    requested_by: str = Field(default="user", max_length=100)
    notes: str | None = Field(default=None, max_length=512)


class RollbackEnvironmentRequest(BaseModel):
    """Payload to trigger rollback of an environment to an earlier verified version."""

    target_version_id: uuid.UUID = Field(..., description="Earlier verified DevelopmentVersion UUID to restore")
    requested_by: str = Field(default="user", max_length=100)
    reason: str = Field(..., min_length=3, max_length=512, description="Audit reason for rollback")
