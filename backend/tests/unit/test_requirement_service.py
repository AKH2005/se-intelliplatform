"""Unit Tests for RequirementService."""

import uuid
import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.models.project import Project, ProjectStatus
from app.models.requirement import (
    RequirementPriority,
    RequirementStatus,
    RequirementType,
)
from app.schemas.requirement import RequirementCreate, RequirementUpdate
from app.services.requirement_service import RequirementService


@pytest.fixture
async def sample_project(db_session: AsyncSession) -> Project:
    """Create a persistent project for requirement scoping."""
    project = Project(
        name="Test Engineering Project",
        slug=f"test-proj-{uuid.uuid4().hex[:8]}",
        status=ProjectStatus.DRAFT,
    )
    db_session.add(project)
    await db_session.commit()
    await db_session.refresh(project)
    return project


@pytest.mark.asyncio
async def test_create_requirement(db_session: AsyncSession, sample_project: Project):
    """Verify creating a requirement associated with a project."""
    service = RequirementService(db_session)
    req_in = RequirementCreate(
        title="Async Event Processing",
        description="Must handle 10,000 events/sec via Redis Streams.",
        type=RequirementType.NON_FUNCTIONAL,
        priority=RequirementPriority.HIGH,
        status=RequirementStatus.APPROVED,
    )
    created = await service.create_requirement(sample_project.id, req_in)

    assert created.id is not None
    assert created.project_id == sample_project.id
    assert created.title == req_in.title
    assert created.type == RequirementType.NON_FUNCTIONAL
    assert created.priority == RequirementPriority.HIGH
    assert created.status == RequirementStatus.APPROVED
    assert created.is_archived is False


@pytest.mark.asyncio
async def test_create_requirement_non_existent_project_fails(db_session: AsyncSession):
    """Verify creating a requirement for non-existent project raises NotFoundError."""
    service = RequirementService(db_session)
    req_in = RequirementCreate(
        title="Orphan Requirement",
        description="Has no parent project.",
    )
    fake_project_id = uuid.uuid4()
    with pytest.raises(NotFoundError) as exc_info:
        await service.create_requirement(fake_project_id, req_in)
    assert str(fake_project_id) in str(exc_info.value)


@pytest.mark.asyncio
async def test_get_by_id_and_project_ownership_isolation(
    db_session: AsyncSession,
    sample_project: Project,
):
    """Verify that a requirement cannot be fetched using an unauthorized/mismatched project ID."""
    service = RequirementService(db_session)
    req = await service.create_requirement(
        sample_project.id,
        RequirementCreate(title="Scoped Req", description="Valid scoped requirement"),
    )

    # Success when querying with correct project ID
    fetched = await service.get_by_id(sample_project.id, req.id)
    assert fetched.id == req.id

    # Fails with NotFoundError when querying with another project ID
    other_project_id = uuid.uuid4()
    with pytest.raises(NotFoundError):
        await service.get_by_id(other_project_id, req.id)


@pytest.mark.asyncio
async def test_list_requirements_with_filtering(
    db_session: AsyncSession,
    sample_project: Project,
):
    """Verify listing requirements filtered by type, priority, status."""
    service = RequirementService(db_session)

    await service.create_requirement(
        sample_project.id,
        RequirementCreate(
            title="Func High",
            description="Functional requirement",
            type=RequirementType.FUNCTIONAL,
            priority=RequirementPriority.HIGH,
            status=RequirementStatus.DRAFT,
        ),
    )
    await service.create_requirement(
        sample_project.id,
        RequirementCreate(
            title="NonFunc Critical",
            description="Non-functional requirement",
            type=RequirementType.NON_FUNCTIONAL,
            priority=RequirementPriority.CRITICAL,
            status=RequirementStatus.IMPLEMENTED,
        ),
    )

    # Filter by type
    func_reqs, count = await service.list_requirements(
        sample_project.id,
        type=RequirementType.FUNCTIONAL,
    )
    assert count == 1
    assert func_reqs[0].title == "Func High"

    # Filter by priority
    crit_reqs, count = await service.list_requirements(
        sample_project.id,
        priority=RequirementPriority.CRITICAL,
    )
    assert count == 1
    assert crit_reqs[0].title == "NonFunc Critical"


@pytest.mark.asyncio
async def test_update_requirement(db_session: AsyncSession, sample_project: Project):
    """Verify updating requirement attributes."""
    service = RequirementService(db_session)
    created = await service.create_requirement(
        sample_project.id,
        RequirementCreate(title="Original Title", description="Original Desc"),
    )

    updated = await service.update_requirement(
        sample_project.id,
        created.id,
        RequirementUpdate(
            title="Updated Title",
            status=RequirementStatus.IMPLEMENTED,
        ),
    )
    assert updated.title == "Updated Title"
    assert updated.status == RequirementStatus.IMPLEMENTED
    assert updated.description == "Original Desc"


@pytest.mark.asyncio
async def test_archive_requirement_soft_delete(
    db_session: AsyncSession,
    sample_project: Project,
):
    """Verify archiving sets is_archived=True and preserves record in database."""
    service = RequirementService(db_session)
    created = await service.create_requirement(
        sample_project.id,
        RequirementCreate(title="To Archive", description="Preserve in DB"),
    )

    archived = await service.archive_requirement(sample_project.id, created.id)
    assert archived.is_archived is True

    # By default, list_requirements excludes archived
    active_reqs, active_count = await service.list_requirements(sample_project.id)
    assert active_count == 0

    # Including archived returns the preserved requirement
    all_reqs, all_count = await service.list_requirements(
        sample_project.id,
        include_archived=True,
    )
    assert all_count == 1
    assert all_reqs[0].id == created.id
