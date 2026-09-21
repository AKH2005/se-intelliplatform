"""Unit Tests for ProjectService and Project Entity."""

import uuid
import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictError, NotFoundError
from app.models.project import Project, ProjectStatus
from app.schemas.project import ProjectCreate, ProjectUpdate
from app.services.project_service import ProjectService


@pytest.mark.asyncio
async def test_project_repr():
    """Verify Project ORM model __repr__ format."""
    p = Project(name="Test", slug="test-slug", status=ProjectStatus.DRAFT)
    assert "test-slug" in repr(p)


@pytest.mark.asyncio
async def test_service_create_and_get_by_id(db_session: AsyncSession):
    """Verify creating and retrieving project via service."""
    service = ProjectService(db_session)
    project_in = ProjectCreate(name="Platform", slug="platform-unique")
    created = await service.create_project(project_in)
    assert created.id is not None

    fetched = await service.get_by_id(created.id)
    assert fetched.slug == "platform-unique"


@pytest.mark.asyncio
async def test_service_get_by_id_not_found(db_session: AsyncSession):
    """Verify NotFoundError on unknown UUID."""
    service = ProjectService(db_session)
    with pytest.raises(NotFoundError):
        await service.get_by_id(uuid.uuid4())


@pytest.mark.asyncio
async def test_service_create_duplicate_slug_raises_conflict(db_session: AsyncSession):
    """Verify ConflictError when attempting to create duplicate slug."""
    service = ProjectService(db_session)
    await service.create_project(ProjectCreate(name="First", slug="same-slug"))
    with pytest.raises(ConflictError):
        await service.create_project(ProjectCreate(name="Second", slug="same-slug"))


@pytest.mark.asyncio
async def test_service_update_conflict_slug(db_session: AsyncSession):
    """Verify updating project to another existing project's slug raises ConflictError."""
    service = ProjectService(db_session)
    p1 = await service.create_project(ProjectCreate(name="P1", slug="slug-one"))
    p2 = await service.create_project(ProjectCreate(name="P2", slug="slug-two"))

    with pytest.raises(ConflictError):
        await service.update_project(p2.id, ProjectUpdate(slug="slug-one"))


@pytest.mark.asyncio
async def test_service_list_with_status_filter(db_session: AsyncSession):
    """Verify listing projects filtered by status."""
    service = ProjectService(db_session)
    await service.create_project(ProjectCreate(name="D1", slug="d1", status=ProjectStatus.DRAFT))
    await service.create_project(ProjectCreate(name="A1", slug="a1", status=ProjectStatus.ARCHIVED))

    drafts, count = await service.list_projects(status=ProjectStatus.DRAFT)
    assert count == 1
    assert drafts[0].slug == "d1"


@pytest.mark.asyncio
async def test_service_hard_delete(db_session: AsyncSession):
    """Verify physical deletion of project."""
    service = ProjectService(db_session)
    p = await service.create_project(ProjectCreate(name="ToDelete", slug="to-delete"))
    await service.hard_delete_project(p.id)

    with pytest.raises(NotFoundError):
        await service.get_by_id(p.id)


def test_project_update_validators():
    """Verify validators on ProjectUpdate."""
    with pytest.raises(ValueError):
        ProjectUpdate(name="   ")

    with pytest.raises(ValueError):
        ProjectUpdate(slug="INVALID SLUG!")
