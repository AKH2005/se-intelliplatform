"""Unit tests for Phase 13 Multi-Environment models and constraints."""

import uuid
import pytest
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.environment import (
    DeploymentOperation,
    DeploymentRecord,
    DeploymentStatus,
    Environment,
    EnvironmentStatus,
    EnvironmentType,
)
from app.models.project import Project, ProjectStatus


@pytest.mark.asyncio
async def test_environment_model_creation(db_session: AsyncSession) -> None:
    """Verify Environment entity attributes and default states."""
    project = Project(
        name="Test Env Project",
        slug="test-env-project",
        description="Project for environment testing",
        status=ProjectStatus.IN_PROGRESS,
    )
    db_session.add(project)
    await db_session.flush()

    env = Environment(
        project_id=project.id,
        environment_type=EnvironmentType.DEVELOPMENT,
        name="Development",
        status=EnvironmentStatus.HEALTHY,
        is_production=False,
    )
    db_session.add(env)
    await db_session.flush()

    assert env.id is not None
    assert env.project_id == project.id
    assert env.environment_type == EnvironmentType.DEVELOPMENT
    assert env.name == "Development"
    assert env.status == EnvironmentStatus.HEALTHY
    assert env.is_production is False
    assert env.current_version_id is None
    assert env.created_at is not None
    assert env.updated_at is not None


@pytest.mark.asyncio
async def test_environment_type_uniqueness_per_project(db_session: AsyncSession) -> None:
    """Ensure a project cannot have two environments of the same type."""
    project = Project(
        name="Uniqueness Project",
        slug="uniqueness-project",
        status=ProjectStatus.IN_PROGRESS,
    )
    db_session.add(project)
    await db_session.flush()

    env1 = Environment(
        project_id=project.id,
        environment_type=EnvironmentType.STAGING,
        name="Staging 1",
    )
    db_session.add(env1)
    await db_session.flush()

    env2 = Environment(
        project_id=project.id,
        environment_type=EnvironmentType.STAGING,
        name="Staging 2",
    )
    db_session.add(env2)

    with pytest.raises(IntegrityError):
        await db_session.flush()
    await db_session.rollback()


@pytest.mark.asyncio
async def test_deployment_record_creation(db_session: AsyncSession) -> None:
    """Verify append-only DeploymentRecord creation with provenance fields."""
    project = Project(
        name="Deployment History Project",
        slug="deployment-history-project",
        status=ProjectStatus.IN_PROGRESS,
    )
    db_session.add(project)
    await db_session.flush()

    env = Environment(
        project_id=project.id,
        environment_type=EnvironmentType.PRODUCTION,
        name="Production",
        is_production=True,
    )
    db_session.add(env)
    await db_session.flush()

    fake_version_id = uuid.uuid4()
    deployment = DeploymentRecord(
        project_id=project.id,
        environment_id=env.id,
        version_id=fake_version_id,
        operation=DeploymentOperation.PROMOTION,
        source_environment_id=None,
        status=DeploymentStatus.SUCCEEDED,
        requested_by="Lead Engineer",
        verification_summary={"checks_passed": 5},
        metadata_payload={"notes": "Initial release"},
    )
    db_session.add(deployment)
    await db_session.flush()

    assert deployment.id is not None
    assert deployment.project_id == project.id
    assert deployment.environment_id == env.id
    assert deployment.version_id == fake_version_id
    assert deployment.operation == DeploymentOperation.PROMOTION
    assert deployment.status == DeploymentStatus.SUCCEEDED
    assert deployment.requested_by == "Lead Engineer"
    assert deployment.verification_summary["checks_passed"] == 5
    assert deployment.started_at is not None
