"""Pydantic v2 Schemas for Project Context and Versioned Snapshots."""

import uuid
from datetime import datetime
from typing import Any
from pydantic import BaseModel, ConfigDict, Field

from app.schemas.project import ProjectResponse
from app.schemas.requirement import RequirementResponse


class RequirementStatistics(BaseModel):
    """Deterministic statistics calculated across project requirements.
    
    All values are computed strictly by deterministic backend algorithms;
    no LLM or non-deterministic inference is ever used.
    """

    total_requirements: int = Field(
        ...,
        description="Total requirements recorded in the project",
    )
    active_requirements: int = Field(
        ...,
        description="Active/eligible requirements (DRAFT + APPROVED + IMPLEMENTED)",
    )
    functional_count: int = Field(
        ...,
        description="Count of active functional requirements",
    )
    non_functional_count: int = Field(
        ...,
        description="Count of active non-functional requirements",
    )
    constraint_count: int = Field(
        ...,
        description="Count of active constraint requirements",
    )
    by_priority: dict[str, int] = Field(
        default_factory=dict,
        description="Count of active requirements grouped by priority (LOW, MEDIUM, HIGH, CRITICAL)",
    )
    by_status: dict[str, int] = Field(
        default_factory=dict,
        description="Total count grouped by lifecycle status (DRAFT, APPROVED, IMPLEMENTED, DEFERRED, REJECTED)",
    )
    completion_percentage: float = Field(
        ...,
        description="Deterministic progress: (IMPLEMENTED / active_requirements) * 100.0 (0.0 if no active)",
        examples=[33.33],
    )


class ProjectContextResponse(BaseModel):
    """Canonical Project Context structured representation.
    
    Serves as the authoritative, validated single source of truth for all future
    SDLC intelligence agents. Agents MUST consume this canonical structure rather
    than querying raw database tables.
    """

    model_config = ConfigDict(from_attributes=True)

    project: ProjectResponse = Field(
        ...,
        description="Canonical project metadata and identity",
    )
    requirements: list[RequirementResponse] = Field(
        default_factory=list,
        description="Active/eligible requirements (DRAFT, APPROVED, IMPLEMENTED)",
    )
    statistics: RequirementStatistics = Field(
        ...,
        description="Deterministic metrics and progress calculations",
    )
    context_version: int = Field(
        ...,
        description="Active context version sequence number",
    )
    generated_at: datetime = Field(
        ...,
        description="Timestamp (UTC) at which this context was assembled",
    )


class ContextSnapshotCreate(BaseModel):
    """Schema for triggering creation of a new immutable context snapshot."""

    summary: str | None = Field(
        default=None,
        max_length=500,
        description="Optional human/agent summary describing the snapshot reason or milestone",
        examples=["Initial requirements freeze for sprint 1"],
    )


class ContextSnapshotResponse(BaseModel):
    """Schema for immutable, versioned project context snapshots."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID = Field(..., description="Unique snapshot UUID")
    project_id: uuid.UUID = Field(..., description="Associated project UUID")
    version: int = Field(..., description="Sequential integer version (1, 2, 3...)")
    context_data: dict[str, Any] = Field(..., description="Immutable point-in-time canonical context")
    summary: str | None = Field(None, description="Milestone summary description")
    created_at: datetime = Field(..., description="Timestamp (UTC) of snapshot creation")
