"""Unit tests for Phase 13 Promotion Eligibility & Deterministic Policy Service."""

import uuid
import pytest
from sqlalchemy.ext.asyncio import AsyncSession

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
from app.services.environment_service import EnvironmentService


@pytest.fixture
async def sample_project(db_session: AsyncSession) -> Project:
    project = Project(
        name="Promotion Policy Project",
        slug="promotion-policy-proj",
        status=ProjectStatus.IN_PROGRESS,
    )
    db_session.add(project)
    await db_session.flush()
    return project


@pytest.fixture
async def other_project(db_session: AsyncSession) -> Project:
    project = Project(
        name="Other Project",
        slug="other-project",
        status=ProjectStatus.IN_PROGRESS,
    )
    db_session.add(project)
    await db_session.flush()
    return project


@pytest.fixture
def env_service(db_session: AsyncSession) -> EnvironmentService:
    return EnvironmentService(session=db_session)


@pytest.mark.asyncio
async def test_eligibility_missing_version(
    env_service: EnvironmentService,
    sample_project: Project,
) -> None:
    """Ensure ineligibility when candidate version does not exist."""
    fake_id = uuid.uuid4()
    result = await env_service.check_promotion_eligibility(
        project_id=sample_project.id,
        version_id=fake_id,
        target_environment=EnvironmentType.STAGING,
        source_environment=EnvironmentType.DEVELOPMENT,
    )
    assert result.eligible is False
    assert any("does not exist" in reason for reason in result.reasons)
    assert "version_exists" in result.failed_checks


@pytest.mark.asyncio
async def test_eligibility_cross_project_version_isolation(
    env_service: EnvironmentService,
    sample_project: Project,
    other_project: Project,
    db_session: AsyncSession,
) -> None:
    """Ensure ineligibility when candidate version belongs to a different project."""
    other_version = DevelopmentVersion(
        project_id=other_project.id,
        version_number=1,
        artifact_key="art-other",
        status=DevelopmentVersionStatus.VERIFIED,
        content_hash="hash-other",
        manifest_hash="m-other",
        file_count=1,
        total_size_bytes=10,
        source_reason="Initial",
        created_by="system",
        verification_summary={"verification_status": "PASSED", "is_verified": True},
    )
    db_session.add(other_version)
    await db_session.flush()

    result = await env_service.check_promotion_eligibility(
        project_id=sample_project.id,
        version_id=other_version.id,
        target_environment=EnvironmentType.STAGING,
        source_environment=EnvironmentType.DEVELOPMENT,
    )
    assert result.eligible is False
    assert any("does not exist or does not belong to project" in r for r in result.reasons)


@pytest.mark.asyncio
async def test_eligibility_blocks_direct_dev_to_prod_promotion(
    env_service: EnvironmentService,
    sample_project: Project,
    db_session: AsyncSession,
) -> None:
    """Ensure promotion directly from DEVELOPMENT to PRODUCTION is strictly blocked."""
    version = DevelopmentVersion(
        project_id=sample_project.id,
        version_number=1,
        artifact_key="art-dev-prod",
        status=DevelopmentVersionStatus.VERIFIED,
        content_hash="hash-1",
        manifest_hash="m-1",
        file_count=2,
        total_size_bytes=100,
        source_reason="Initial",
        created_by="system",
        verification_summary={"verification_status": "PASSED", "is_verified": True},
    )
    db_session.add(version)
    await db_session.flush()

    result = await env_service.check_promotion_eligibility(
        project_id=sample_project.id,
        version_id=version.id,
        target_environment=EnvironmentType.PRODUCTION,
        source_environment=EnvironmentType.DEVELOPMENT,
    )
    assert result.eligible is False
    assert any("Direct promotion from DEVELOPMENT to PRODUCTION is disallowed" in r for r in result.reasons)


@pytest.mark.asyncio
async def test_eligibility_unverified_version_blocked(
    env_service: EnvironmentService,
    sample_project: Project,
    db_session: AsyncSession,
) -> None:
    """Ensure unverified or failed-verification versions cannot be promoted."""
    unverified_ver = DevelopmentVersion(
        project_id=sample_project.id,
        version_number=2,
        artifact_key="art-unverified",
        status=DevelopmentVersionStatus.GENERATED,
        content_hash="hash-2",
        manifest_hash="m-2",
        file_count=2,
        total_size_bytes=100,
        source_reason="Unverified commit",
        created_by="system",
        verification_summary={"verification_status": "FAILED", "is_verified": False},
    )
    db_session.add(unverified_ver)
    await db_session.flush()

    result = await env_service.check_promotion_eligibility(
        project_id=sample_project.id,
        version_id=unverified_ver.id,
        target_environment=EnvironmentType.STAGING,
        source_environment=EnvironmentType.DEVELOPMENT,
    )
    assert result.eligible is False
    assert any("Verification status is GENERATED" in r for r in result.reasons)
    assert any("Candidate version must be in VERIFIED status" in f for f in result.failed_checks)


@pytest.mark.asyncio
async def test_eligibility_dev_to_staging_success(
    env_service: EnvironmentService,
    sample_project: Project,
    db_session: AsyncSession,
) -> None:
    """Ensure verified version is eligible for DEV -> STAGING promotion."""
    verified_ver = DevelopmentVersion(
        project_id=sample_project.id,
        version_number=3,
        artifact_key="art-verified",
        status=DevelopmentVersionStatus.VERIFIED,
        content_hash="hash-3",
        manifest_hash="m-3",
        file_count=3,
        total_size_bytes=200,
        source_reason="Clean pass",
        created_by="system",
        verification_summary={"verification_status": "PASSED", "is_verified": True},
    )
    db_session.add(verified_ver)
    await db_session.flush()

    result = await env_service.check_promotion_eligibility(
        project_id=sample_project.id,
        version_id=verified_ver.id,
        target_environment=EnvironmentType.STAGING,
        source_environment=EnvironmentType.DEVELOPMENT,
    )
    assert result.eligible is True
    assert result.version_number == 3
    assert len(result.failed_checks) == 0
    assert any("Candidate version exists and belongs to project" in p for p in result.passed_checks)
    assert any("Verification status is VERIFIED" in p for p in result.passed_checks)


@pytest.mark.asyncio
async def test_eligibility_staging_to_prod_requires_staging_deployment(
    env_service: EnvironmentService,
    sample_project: Project,
    db_session: AsyncSession,
) -> None:
    """Ensure STAGING -> PRODUCTION requires prior successful deployment to STAGING."""
    envs = await env_service.get_or_create_project_environments(sample_project.id)
    staging_env = next(e for e in envs if e.environment_type == EnvironmentType.STAGING)

    version = DevelopmentVersion(
        project_id=sample_project.id,
        version_number=4,
        artifact_key="art-4",
        status=DevelopmentVersionStatus.VERIFIED,
        content_hash="hash-4",
        manifest_hash="m-4",
        file_count=2,
        total_size_bytes=150,
        source_reason="Sprint 4",
        created_by="system",
        verification_summary={"verification_status": "PASSED", "is_verified": True},
    )
    db_session.add(version)
    await db_session.flush()

    # Case A: Never deployed to staging -> ineligible
    result_a = await env_service.check_promotion_eligibility(
        project_id=sample_project.id,
        version_id=version.id,
        target_environment=EnvironmentType.PRODUCTION,
        source_environment=EnvironmentType.STAGING,
    )
    assert result_a.eligible is False
    assert any("has not been verified in the STAGING environment" in r for r in result_a.reasons)

    # Case B: Deployed to staging -> eligible
    staging_record = DeploymentRecord(
        project_id=sample_project.id,
        environment_id=staging_env.id,
        version_id=version.id,
        operation=DeploymentOperation.PROMOTION,
        status=DeploymentStatus.SUCCEEDED,
        requested_by="CI",
    )
    db_session.add(staging_record)
    await db_session.flush()

    result_b = await env_service.check_promotion_eligibility(
        project_id=sample_project.id,
        version_id=version.id,
        target_environment=EnvironmentType.PRODUCTION,
        source_environment=EnvironmentType.STAGING,
    )
    assert result_b.eligible is True
    assert any("previously deployed to STAGING" in p for p in result_b.passed_checks)
    assert result_b.requires_confirmation is True
