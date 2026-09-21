"""Pydantic v2 Schemas for Requirement Operations."""

import uuid
from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.models.requirement import (
    RequirementPriority,
    RequirementStatus,
    RequirementType,
)


class RequirementBase(BaseModel):
    """Base schema defining common Requirement fields."""

    title: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description="Human-readable requirement summary",
        examples=["User Authentication via JWT"],
    )
    description: str = Field(
        ...,
        min_length=1,
        description="Detailed requirement description, acceptance criteria, or constraints",
        examples=["System must support OAuth2 password flow with asymmetric RS256 token signing."],
    )
    type: RequirementType = Field(
        default=RequirementType.FUNCTIONAL,
        description="Category: FUNCTIONAL, NON_FUNCTIONAL, or CONSTRAINT",
    )
    priority: RequirementPriority = Field(
        default=RequirementPriority.MEDIUM,
        description="Priority: LOW, MEDIUM, HIGH, or CRITICAL",
    )
    status: RequirementStatus = Field(
        default=RequirementStatus.DRAFT,
        description="Lifecycle status: DRAFT, APPROVED, IMPLEMENTED, DEFERRED, or REJECTED",
    )

    @field_validator("title")
    @classmethod
    def validate_title_not_blank(cls, v: str) -> str:
        stripped = v.strip()
        if not stripped:
            raise ValueError("Requirement title cannot be empty or whitespace only.")
        return stripped

    @field_validator("description")
    @classmethod
    def validate_description_not_blank(cls, v: str) -> str:
        stripped = v.strip()
        if not stripped:
            raise ValueError("Requirement description cannot be empty or whitespace only.")
        return stripped


class RequirementCreate(RequirementBase):
    """Schema for requirement creation requests."""
    pass


class RequirementUpdate(BaseModel):
    """Schema for updating an existing requirement."""

    title: str | None = Field(
        default=None,
        min_length=1,
        max_length=255,
        description="Updated requirement title",
    )
    description: str | None = Field(
        default=None,
        min_length=1,
        description="Updated requirement description",
    )
    type: RequirementType | None = Field(
        default=None,
        description="Updated requirement type",
    )
    priority: RequirementPriority | None = Field(
        default=None,
        description="Updated priority level",
    )
    status: RequirementStatus | None = Field(
        default=None,
        description="Updated lifecycle status",
    )
    is_archived: bool | None = Field(
        default=None,
        description="Archive status flag",
    )

    @field_validator("title")
    @classmethod
    def validate_title_not_blank(cls, v: str | None) -> str | None:
        if v is not None:
            stripped = v.strip()
            if not stripped:
                raise ValueError("Requirement title cannot be empty or whitespace only.")
            return stripped
        return v

    @field_validator("description")
    @classmethod
    def validate_description_not_blank(cls, v: str | None) -> str | None:
        if v is not None:
            stripped = v.strip()
            if not stripped:
                raise ValueError("Requirement description cannot be empty or whitespace only.")
            return stripped
        return v


class RequirementResponse(RequirementBase):
    """Schema for requirement data returned to API consumers."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID = Field(..., description="Unique UUID identifier")
    project_id: uuid.UUID = Field(..., description="Parent project UUID")
    is_archived: bool = Field(..., description="Whether requirement is archived")
    created_at: datetime = Field(..., description="Creation timestamp (UTC)")
    updated_at: datetime = Field(..., description="Last update timestamp (UTC)")
