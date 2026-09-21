"""Unit Tests for Project Pydantic Schemas."""

import pytest
from pydantic import ValidationError

from app.models.project import ProjectStatus
from app.schemas.project import ProjectCreate, ProjectUpdate


def test_valid_project_create_schema():
    """Verify valid project payload instantiates successfully."""
    payload = {
        "name": "Intelli Platform",
        "slug": "intelli-platform-v1",
        "description": "An AI-powered SE platform",
        "status": "DRAFT",
        "settings": {"architecture": "microservices"},
    }
    project_in = ProjectCreate(**payload)
    assert project_in.name == "Intelli Platform"
    assert project_in.slug == "intelli-platform-v1"
    assert project_in.status == ProjectStatus.DRAFT
    assert project_in.settings["architecture"] == "microservices"


def test_project_name_empty_fails():
    """Verify empty or whitespace-only name raises validation error."""
    with pytest.raises(ValidationError) as exc_info:
        ProjectCreate(name="   ", slug="valid-slug")
    assert "Project name cannot be empty" in str(exc_info.value)


@pytest.mark.parametrize(
    "invalid_slug",
    [
        "Invalid Slug",      # contains spaces and uppercase
        "slug_with_under",   # underscores not allowed
        "-leading-dash",     # starts with hyphen
        "trailing-dash-",    # ends with hyphen
        "double--dash",      # consecutive hyphens
        "slug@with#symbols", # special characters
    ],
)
def test_invalid_slug_fails(invalid_slug: str):
    """Verify various malformed slugs fail validation."""
    with pytest.raises(ValidationError) as exc_info:
        ProjectCreate(name="Test Project", slug=invalid_slug)
    assert "Slug must consist of lowercase alphanumeric" in str(exc_info.value)


def test_invalid_status_fails():
    """Verify unknown status values are rejected."""
    with pytest.raises(ValidationError):
        ProjectCreate(name="Test Project", slug="valid-slug", status="UNKNOWN_STATUS")


def test_project_update_partial():
    """Verify partial updates allow None or omitted fields."""
    update_in = ProjectUpdate(name="Updated Name")
    data = update_in.model_dump(exclude_unset=True)
    assert data == {"name": "Updated Name"}
