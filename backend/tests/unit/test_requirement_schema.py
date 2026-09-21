"""Unit Tests for Requirement Pydantic Schemas."""

import pytest
from pydantic import ValidationError

from app.models.requirement import (
    RequirementPriority,
    RequirementStatus,
    RequirementType,
)
from app.schemas.requirement import (
    RequirementCreate,
    RequirementUpdate,
)


def test_valid_requirement_create():
    """Verify valid requirement instantiates with defaults."""
    payload = {
        "title": "OAuth2 Token Authentication",
        "description": "System must support RS256 signed JWT tokens.",
        "type": "FUNCTIONAL",
        "priority": "HIGH",
        "status": "DRAFT",
    }
    req = RequirementCreate(**payload)
    assert req.title == "OAuth2 Token Authentication"
    assert req.description == "System must support RS256 signed JWT tokens."
    assert req.type == RequirementType.FUNCTIONAL
    assert req.priority == RequirementPriority.HIGH
    assert req.status == RequirementStatus.DRAFT


def test_requirement_create_defaults():
    """Verify default values for type, priority, status."""
    req = RequirementCreate(
        title="Minimal Requirement",
        description="Just title and description provided.",
    )
    assert req.type == RequirementType.FUNCTIONAL
    assert req.priority == RequirementPriority.MEDIUM
    assert req.status == RequirementStatus.DRAFT


def test_empty_title_fails():
    """Verify empty or whitespace-only title raises ValidationError."""
    with pytest.raises(ValidationError) as exc_info:
        RequirementCreate(title="   ", description="Valid description")
    assert "Requirement title cannot be empty" in str(exc_info.value)


def test_empty_description_fails():
    """Verify empty or whitespace-only description raises ValidationError."""
    with pytest.raises(ValidationError) as exc_info:
        RequirementCreate(title="Valid Title", description="    ")
    assert "Requirement description cannot be empty" in str(exc_info.value)


@pytest.mark.parametrize(
    "field,invalid_val",
    [
        ("type", "INVALID_TYPE"),
        ("priority", "SUPER_CRITICAL"),
        ("status", "IN_REVIEW"),
    ],
)
def test_invalid_enums_fail(field: str, invalid_val: str):
    """Verify arbitrary or unsupported enum values are rejected."""
    payload = {
        "title": "Test Title",
        "description": "Test Description",
        field: invalid_val,
    }
    with pytest.raises(ValidationError):
        RequirementCreate(**payload)


def test_requirement_update_partial():
    """Verify partial updates allow updating single fields."""
    update = RequirementUpdate(priority=RequirementPriority.CRITICAL)
    data = update.model_dump(exclude_unset=True)
    assert data == {"priority": RequirementPriority.CRITICAL}


def test_requirement_update_whitespace_validation():
    """Verify whitespace-only strings in update raise ValidationError."""
    with pytest.raises(ValidationError):
        RequirementUpdate(title="   ")

    with pytest.raises(ValidationError):
        RequirementUpdate(description="   ")
