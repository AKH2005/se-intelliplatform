"""Pydantic v2 Schemas for Project Operations."""

import re
import uuid
from datetime import datetime
from typing import Any
from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.models.project import ProjectStatus

SLUG_REGEX = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")


class ProjectBase(BaseModel):
    """Base fields shared across project schemas."""

    name: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description="Human-readable project name",
        examples=["E-Commerce Platform"],
    )
    slug: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="URL-safe unique identifier for the project",
        examples=["e-commerce-platform"],
    )
    description: str | None = Field(
        default=None,
        max_length=2000,
        description="Detailed project overview",
        examples=["Microservices-based e-commerce application"],
    )
    status: ProjectStatus = Field(
        default=ProjectStatus.DRAFT,
        description="Lifecycle status of the project",
    )
    settings: dict[str, Any] = Field(
        default_factory=dict,
        description="Platform configuration parameters and constraints",
        examples=[{"target_language": "python", "architecture_style": "modular_monolith"}],
    )

    @field_validator("name")
    @classmethod
    def validate_name_not_blank(cls, v: str) -> str:
        stripped = v.strip()
        if not stripped:
            raise ValueError("Project name cannot be empty or whitespace only.")
        return stripped

    @field_validator("slug")
    @classmethod
    def validate_slug_format(cls, v: str) -> str:
        normalized = v.strip().lower()
        if not SLUG_REGEX.match(normalized):
            raise ValueError(
                "Slug must consist of lowercase alphanumeric characters separated by single hyphens (e.g. 'my-project-1')."
            )
        return normalized


class ProjectCreate(ProjectBase):
    """Schema for project creation requests."""
    pass


class ProjectUpdate(BaseModel):
    """Schema for partial updates to project resources."""

    name: str | None = Field(
        default=None,
        min_length=1,
        max_length=255,
        description="Updated project name",
    )
    slug: str | None = Field(
        default=None,
        min_length=1,
        max_length=100,
        description="Updated unique slug",
    )
    description: str | None = Field(
        default=None,
        max_length=2000,
        description="Updated project description",
    )
    status: ProjectStatus | None = Field(
        default=None,
        description="Updated lifecycle status",
    )
    settings: dict[str, Any] | None = Field(
        default=None,
        description="Updated settings dictionary",
    )

    @field_validator("name")
    @classmethod
    def validate_name_not_blank(cls, v: str | None) -> str | None:
        if v is not None:
            stripped = v.strip()
            if not stripped:
                raise ValueError("Project name cannot be empty or whitespace only.")
            return stripped
        return v

    @field_validator("slug")
    @classmethod
    def validate_slug_format(cls, v: str | None) -> str | None:
        if v is not None:
            normalized = v.strip().lower()
            if not SLUG_REGEX.match(normalized):
                raise ValueError(
                    "Slug must consist of lowercase alphanumeric characters separated by single hyphens."
                )
            return normalized
        return v


class ProjectResponse(ProjectBase):
    """Schema for project representations returned from API endpoints."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID = Field(..., description="Unique UUID identifier")
    created_at: datetime = Field(..., description="Creation timestamp (UTC)")
    updated_at: datetime = Field(..., description="Last update timestamp (UTC)")
