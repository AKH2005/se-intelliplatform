"""Unit tests for Phase 13 Deployment, Promotion, and Rollback Lifecycle Execution."""

import uuid
import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError, ValidationError
from app.models.development_version import DevelopmentVersion, DevelopmentVersionStatus
from app.models.environment import (
    DeploymentOperation,
    DeploymentRecord,
    DeploymentStatus,
    Environment,
    EnvironmentStatus,
    EnvironmentType,
)
from app.models.project import Project, ProjectStatus
from app.services.deployment_target import (
    AbstractDeploymentTarget,
    DeploymentExecutionResult,
)
from app.services.environment_service import EnvironmentService


class FailingDeploymentTarget(AbstractDeploymentTarget):
    """Mock target that simulates deployment infrastructure failure."""

    async def validate_target(
        self,
        environment: Environment,
        version: DevelopmentVersion,
    ) -> tuple[bool, str | None]:
        return True, None

    async def execute_deployment(
        self,
        environment: Environment,
        version: DevelopmentVersion,
        deployment_id: uuid.UUID,
    ) -> DeploymentExecutionResult:
        return DeploymentExecutionResult(
            success=False,
            status="FAILED",
            error_message="Simulated container boot failure in deployment target",
        )

    async def verify_health(
        self,
        environment: Environment,
    ) -> bool:
        return False


@pytest.fixture
async def sample_project(db_session: AsyncSession) -> Project:
    project = Project(
        name="Deployment Lifecycle Project",
        slug="deployment-lifecycle-proj",
        status=ProjectStatus.IN_PROGRESS,
        settings={},
    )
    db_session.add(project)
    await db_session.flush()
    return project


@pytest.fixture
async def v1_version(db_session: AsyncSession, sample_project: Project) -> DevelopmentVersion:
    v1 = DevelopmentVersion(
        project_id=sample_project.id,
        version_number=1,
        artifact_key="art-v1",
        status=DevelopmentVersionStatus.VERIFIED,
        content_hash="hash-v1",
        manifest_hash="m-v1",
        file_count=2,
        total_size_bytes=100,
        source_reason="Initial v1",
        created_by="system",
        verification_summary={"verification_status": "PASSED", "is_verified": True},
    )
    db_session.add(v1)
    await db_session.flush()
    return v1


@pytest.fixture
async def v2_version(db_session: AsyncSession, sample_project: Project) -> DevelopmentVersion:
    v2 = DevelopmentVersion(
        project_id=sample_project.id,
        version_number=2,
        artifact_key="art-v2",
        status=DevelopmentVersionStatus.VERIFIED,
        content_hash="hash-v2",
        manifest_hash="m-v2",
        file_count=3,
        total_size_bytes=150,
        source_reason="Feature update v2",
        created_by="system",
        verification_summary={"verification_status": "PASSED", "is_verified": True},
    )
    db_session.add(v2)
    await db_session.flush()
    return v2


@pytest.fixture
def env_service(db_session: AsyncSession) -> EnvironmentService:
    return EnvironmentService(session=db_session)


@pytest.mark.asyncio
async def test_direct_deploy_to_development_syncs_project_settings(
    env_service: EnvironmentService,
    sample_project: Project,
    v1_version: DevelopmentVersion,
    db_session: AsyncSession,
) -> None:
    """Ensure deploying to DEVELOPMENT synchronizes backward-compatible active_version_id."""
    envs = await env_service.get_or_create_project_environments(sample_project.id)
    dev_env = next(e for e in envs if e.environment_type == EnvironmentType.DEVELOPMENT)

    record = await env_service.deploy_version(
        project_id=sample_project.id,
        env_id_or_type=dev_env.id,
        version_id=v1_version.id,
        requested_by="Dev Engineer",
        notes="Testing direct deployment",
    )

    assert record.status == DeploymentStatus.SUCCEEDED
    assert record.operation == DeploymentOperation.DEPLOYMENT
    assert dev_env.current_version_id == v1_version.id

    # Backward compatibility assertion
    await db_session.refresh(sample_project)
    assert sample_project.settings.get("active_version_id") == str(v1_version.id)


@pytest.mark.asyncio
async def test_successful_promotion_lifecycle(
    env_service: EnvironmentService,
    sample_project: Project,
    v1_version: DevelopmentVersion,
    db_session: AsyncSession,
) -> None:
    """Ensure DEV -> STAGING promotion updates staging pointer and creates record."""
    # First deploy v1 to DEV
    envs = await env_service.get_or_create_project_environments(sample_project.id)
    dev_env = next(e for e in envs if e.environment_type == EnvironmentType.DEVELOPMENT)
    staging_env = next(e for e in envs if e.environment_type == EnvironmentType.STAGING)

    await env_service.deploy_version(
        project_id=sample_project.id,
        env_id_or_type=dev_env.id,
        version_id=v1_version.id,
    )

    # Promote to STAGING
    record = await env_service.promote_version(
        project_id=sample_project.id,
        version_id=v1_version.id,
        target_env_type=EnvironmentType.STAGING,
        source_env_type=EnvironmentType.DEVELOPMENT,
        requested_by="Release Manager",
        notes="Promoting verified v1 to Staging",
    )

    assert record.status == DeploymentStatus.SUCCEEDED
    assert record.operation == DeploymentOperation.PROMOTION
    assert record.environment_id == staging_env.id
    assert record.source_environment_id == dev_env.id
    assert staging_env.current_version_id == v1_version.id
    assert dev_env.current_version_id == v1_version.id  # Source unchanged


@pytest.mark.asyncio
async def test_failed_deployment_preserves_safe_environment_state(
    sample_project: Project,
    v1_version: DevelopmentVersion,
    v2_version: DevelopmentVersion,
    db_session: AsyncSession,
) -> None:
    """Ensure a failed deployment does NOT replace previous known-good version pointer."""
    # 1. Successful deploy of v1 using normal service
    normal_service = EnvironmentService(session=db_session)
    envs = await normal_service.get_or_create_project_environments(sample_project.id)
    staging_env = next(e for e in envs if e.environment_type == EnvironmentType.STAGING)

    await normal_service.deploy_version(
        project_id=sample_project.id,
        env_id_or_type=staging_env.id,
        version_id=v1_version.id,
    )
    assert staging_env.current_version_id == v1_version.id

    # 2. Deploy v2 using a service with failing deployment target
    failing_service = EnvironmentService(
        session=db_session,
        deployment_target=FailingDeploymentTarget(),
    )

    with pytest.raises(RuntimeError) as exc_info:
        await failing_service.deploy_version(
            project_id=sample_project.id,
            env_id_or_type=staging_env.id,
            version_id=v2_version.id,
        )

    assert "Simulated container boot failure" in str(exc_info.value)

    # CRITICAL INVARIANT: The environment pointer MUST remain at v1 (known-good)
    await db_session.refresh(staging_env)
    assert staging_env.current_version_id == v1_version.id


@pytest.mark.asyncio
async def test_rollback_environment_lifecycle(
    env_service: EnvironmentService,
    sample_project: Project,
    v1_version: DevelopmentVersion,
    v2_version: DevelopmentVersion,
    db_session: AsyncSession,
) -> None:
    """Ensure non-destructive rollback safely reverts pointer with append-only audit trail."""
    envs = await env_service.get_or_create_project_environments(sample_project.id)
    prod_env = next(e for e in envs if e.environment_type == EnvironmentType.PRODUCTION)

    # 1. Deploy v1 to prod
    await env_service.deploy_version(
        project_id=sample_project.id,
        env_id_or_type=prod_env.id,
        version_id=v1_version.id,
    )

    # 2. Deploy v2 to prod
    await env_service.deploy_version(
        project_id=sample_project.id,
        env_id_or_type=prod_env.id,
        version_id=v2_version.id,
    )
    assert prod_env.current_version_id == v2_version.id

    # 3. Rollback prod to v1
    rollback_record = await env_service.rollback_environment(
        project_id=sample_project.id,
        env_id_or_type=prod_env.id,
        target_version_id=v1_version.id,
        reason="Critical regression observed in prod v2; reverting to stable v1",
        requested_by="Operations Lead",
    )

    assert rollback_record.status == DeploymentStatus.SUCCEEDED
    assert rollback_record.operation == DeploymentOperation.ROLLBACK
    assert rollback_record.version_id == v1_version.id
    assert rollback_record.previous_version_id == v2_version.id
    assert prod_env.current_version_id == v1_version.id

    # Check append-only history has at least 3 records (v1 deploy, v2 deploy, v1 rollback)
    history = await env_service.list_deployments(sample_project.id, prod_env.id)
    assert len(history) == 3
    assert history[0].operation == DeploymentOperation.ROLLBACK


@pytest.mark.asyncio
async def test_rollback_rejects_non_project_version(
    env_service: EnvironmentService,
    sample_project: Project,
    v1_version: DevelopmentVersion,
    db_session: AsyncSession,
) -> None:
    """Ensure rollback rejects versions belonging to a different project."""
    other_proj = Project(name="Other P", slug="other-p", status=ProjectStatus.IN_PROGRESS)
    db_session.add(other_proj)
    await db_session.flush()

    other_v = DevelopmentVersion(
        project_id=other_proj.id,
        version_number=1,
        artifact_key="art-other",
        status=DevelopmentVersionStatus.VERIFIED,
        content_hash="h-other",
        manifest_hash="m-other",
        file_count=1,
        total_size_bytes=10,
        source_reason="Other",
        created_by="system",
    )
    db_session.add(other_v)
    await db_session.flush()

    envs = await env_service.get_or_create_project_environments(sample_project.id)
    dev_env = next(e for e in envs if e.environment_type == EnvironmentType.DEVELOPMENT)

    with pytest.raises((ValidationError, NotFoundError)) as exc_info:
        await env_service.rollback_environment(
            project_id=sample_project.id,
            env_id_or_type=dev_env.id,
            target_version_id=other_v.id,
            reason="Trying to rollback with another project's version",
        )
    assert "not found" in str(exc_info.value).lower() or "not belong" in str(exc_info.value).lower()
