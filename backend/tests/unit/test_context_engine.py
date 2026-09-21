"""Unit Tests for ProjectContextEngine, Deterministic Statistics, and Snapshots."""

import uuid
from unittest.mock import patch
import pytest
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictError, NotFoundError
from app.models.project import Project, ProjectStatus
from app.models.requirement import (
    Requirement,
    RequirementPriority,
    RequirementStatus,
    RequirementType,
)
from app.schemas.requirement import RequirementCreate
from app.services.context_engine import ProjectContextEngine
from app.services.requirement_service import RequirementService


@pytest.fixture
async def sample_project(db_session: AsyncSession) -> Project:
    """Create a project entity for context testing."""
    project = Project(
        name="FinTech Microservices Core",
        slug=f"fintech-{uuid.uuid4().hex[:8]}",
        status=ProjectStatus.IN_PROGRESS,
    )
    db_session.add(project)
    await db_session.commit()
    await db_session.refresh(project)
    return project


@pytest.mark.asyncio
async def test_empty_project_context_and_deterministic_statistics(
    db_session: AsyncSession,
    sample_project: Project,
):
    """Verify context generation and statistics for project with 0 requirements."""
    engine = ProjectContextEngine(db_session)
    context = await engine.generate_context(sample_project.id)

    assert context.project.id == sample_project.id
    assert context.project.name == "FinTech Microservices Core"
    assert len(context.requirements) == 0
    assert context.context_version == 0

    stats = context.statistics
    assert stats.total_requirements == 0
    assert stats.active_requirements == 0
    assert stats.functional_count == 0
    assert stats.non_functional_count == 0
    assert stats.constraint_count == 0
    assert stats.completion_percentage == 0.0


@pytest.mark.asyncio
async def test_inclusion_rules_and_completion_calculation(
    db_session: AsyncSession,
    sample_project: Project,
):
    """Verify Phase 2 inclusion rules and completion percentage arithmetic:
    - DRAFT = included
    - APPROVED = included
    - IMPLEMENTED = included
    - DEFERRED = excluded
    - REJECTED = excluded
    - is_archived = True is excluded
    """
    engine = ProjectContextEngine(db_session)

    # Seed 6 requirements: 3 included (1 draft, 1 approved, 1 implemented), 3 excluded (1 deferred, 1 rejected, 1 archived draft)
    reqs = [
        Requirement(
            project_id=sample_project.id,
            title="R1 Draft Functional",
            description="Desc 1",
            type=RequirementType.FUNCTIONAL,
            priority=RequirementPriority.HIGH,
            status=RequirementStatus.DRAFT,
            is_archived=False,
        ),
        Requirement(
            project_id=sample_project.id,
            title="R2 Approved Non-Functional",
            description="Desc 2",
            type=RequirementType.NON_FUNCTIONAL,
            priority=RequirementPriority.MEDIUM,
            status=RequirementStatus.APPROVED,
            is_archived=False,
        ),
        Requirement(
            project_id=sample_project.id,
            title="R3 Implemented Constraint",
            description="Desc 3",
            type=RequirementType.CONSTRAINT,
            priority=RequirementPriority.CRITICAL,
            status=RequirementStatus.IMPLEMENTED,
            is_archived=False,
        ),
        Requirement(
            project_id=sample_project.id,
            title="R4 Deferred Functional",
            description="Desc 4",
            type=RequirementType.FUNCTIONAL,
            priority=RequirementPriority.LOW,
            status=RequirementStatus.DEFERRED,
            is_archived=False,
        ),
        Requirement(
            project_id=sample_project.id,
            title="R5 Rejected Constraint",
            description="Desc 5",
            type=RequirementType.CONSTRAINT,
            priority=RequirementPriority.LOW,
            status=RequirementStatus.REJECTED,
            is_archived=False,
        ),
        Requirement(
            project_id=sample_project.id,
            title="R6 Archived Draft",
            description="Desc 6",
            type=RequirementType.FUNCTIONAL,
            priority=RequirementPriority.MEDIUM,
            status=RequirementStatus.DRAFT,
            is_archived=True,
        ),
    ]
    for r in reqs:
        db_session.add(r)
    await db_session.commit()

    context = await engine.generate_context(sample_project.id)

    # Only 3 active eligible requirements should be present in context
    assert len(context.requirements) == 3
    active_titles = [r.title for r in context.requirements]
    assert "R1 Draft Functional" in active_titles
    assert "R2 Approved Non-Functional" in active_titles
    assert "R3 Implemented Constraint" in active_titles
    assert "R4 Deferred Functional" not in active_titles
    assert "R5 Rejected Constraint" not in active_titles
    assert "R6 Archived Draft" not in active_titles

    stats = context.statistics
    assert stats.total_requirements == 6
    assert stats.active_requirements == 3
    assert stats.functional_count == 1
    assert stats.non_functional_count == 1
    assert stats.constraint_count == 1

    # Active = 3, Implemented = 1 -> completion = (1 / 3) * 100 = 33.33%
    assert stats.completion_percentage == 33.33

    # Check status breakdown includes all for complete auditability
    assert stats.by_status["DRAFT"] == 2  # 1 active + 1 archived
    assert stats.by_status["APPROVED"] == 1
    assert stats.by_status["IMPLEMENTED"] == 1
    assert stats.by_status["DEFERRED"] == 1
    assert stats.by_status["REJECTED"] == 1


@pytest.mark.asyncio
async def test_snapshot_creation_and_versioning_lifecycle(
    db_session: AsyncSession,
    sample_project: Project,
):
    """Verify creating sequential versioned snapshots (v1 -> v2) and retrieving them."""
    engine = ProjectContextEngine(db_session)
    req_service = RequirementService(db_session)

    # 1. Create requirement A and snapshot v1
    await req_service.create_requirement(
        sample_project.id,
        RequirementCreate(title="Req Alpha", description="Alpha desc"),
    )

    s1 = await engine.create_snapshot(sample_project.id, summary="Sprint 1 Baseline")
    assert s1.version == 1
    assert s1.project_id == sample_project.id
    assert s1.summary == "Sprint 1 Baseline"
    assert s1.context_data["context_version"] == 1
    assert s1.context_data["statistics"]["total_requirements"] == 1

    # 2. Add requirement B and snapshot v2
    await req_service.create_requirement(
        sample_project.id,
        RequirementCreate(title="Req Beta", description="Beta desc"),
    )

    s2 = await engine.create_snapshot(sample_project.id, summary="Sprint 2 Scope Expansion")
    assert s2.version == 2
    assert s2.context_data["context_version"] == 2
    assert s2.context_data["statistics"]["total_requirements"] == 2

    # 3. Verify snapshot immutability: retrieving v1 historical state reflects only 1 requirement
    v1_retrieved = await engine.get_snapshot_by_version(sample_project.id, version=1)
    assert v1_retrieved.version == 1
    assert v1_retrieved.context_data["statistics"]["total_requirements"] == 1

    # 4. List snapshots returns v2, then v1
    snapshots, count = await engine.list_snapshots(sample_project.id)
    assert count == 2
    assert snapshots[0].version == 2
    assert snapshots[1].version == 1


@pytest.mark.asyncio
async def test_get_snapshot_not_found(db_session: AsyncSession, sample_project: Project):
    """Verify querying non-existent snapshot version raises NotFoundError."""
    engine = ProjectContextEngine(db_session)
    with pytest.raises(NotFoundError):
        await engine.get_snapshot_by_version(sample_project.id, version=999)


@pytest.mark.asyncio
async def test_snapshot_concurrency_retry(
    db_session: AsyncSession,
    sample_project: Project,
):
    """Verify deterministic retry when version collision occurs."""
    engine = ProjectContextEngine(db_session)

    call_count = 0
    original_commit = db_session.commit

    async def mock_commit():
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            # Simulate a concurrent collision on first attempt
            raise IntegrityError("duplicate key value violates unique constraint", params={}, orig=Exception())
        return await original_commit()

    with patch.object(db_session, "commit", side_effect=mock_commit):
        snapshot = await engine.create_snapshot(sample_project.id, summary="Concurrent Test", max_retries=2)
        assert snapshot.version == 1
        assert call_count == 2
