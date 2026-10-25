"""Integration tests for Phase 13 Multi-Environment & Deployment REST API."""

import uuid
import pytest
from httpx import AsyncClient
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


async def _create_test_project_and_versions(db_session: AsyncSession) -> tuple[Project, DevelopmentVersion, DevelopmentVersion]:
    project = Project(
        name="Integration Environments Project",
        slug=f"integ-env-proj-{uuid.uuid4().hex[:8]}",
        status=ProjectStatus.IN_PROGRESS,
        settings={},
    )
    db_session.add(project)
    await db_session.flush()

    v1 = DevelopmentVersion(
        project_id=project.id,
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
    v2 = DevelopmentVersion(
        project_id=project.id,
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
    db_session.add_all([v1, v2])
    await db_session.commit()
    return project, v1, v2


@pytest.mark.asyncio
async def test_list_environments_provisions_defaults(
    client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    """GET /api/v1/projects/{project_id}/environments provisions DEV, STAGING, PROD idempotently."""
    project, v1, _ = await _create_test_project_and_versions(db_session)

    resp = await client.get(f"/api/v1/projects/{project.id}/environments")
    assert resp.status_code == 200
    data = resp.json()

    assert isinstance(data, list)
    assert len(data) == 3

    types = {e["environment_type"] for e in data}
    assert types == {"DEVELOPMENT", "STAGING", "PRODUCTION"}

    for env in data:
        assert env["project_id"] == str(project.id)
        assert env["status"] == "HEALTHY"


@pytest.mark.asyncio
async def test_get_environment_by_type_and_id(
    client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    """GET /api/v1/projects/{project_id}/environments/{env_id_or_type}."""
    project, _, _ = await _create_test_project_and_versions(db_session)

    # By type string
    resp = await client.get(f"/api/v1/projects/{project.id}/environments/staging")
    assert resp.status_code == 200
    env_data = resp.json()
    assert env_data["environment_type"] == "STAGING"

    # By UUID
    env_id = env_data["id"]
    resp2 = await client.get(f"/api/v1/projects/{project.id}/environments/{env_id}")
    assert resp2.status_code == 200
    assert resp2.json()["id"] == env_id


@pytest.mark.asyncio
async def test_check_promotion_eligibility_endpoint(
    client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    """GET /api/v1/projects/{project_id}/environments/eligibility."""
    project, v1, _ = await _create_test_project_and_versions(db_session)

    resp = await client.get(
        f"/api/v1/projects/{project.id}/environments/eligibility",
        params={
            "version_id": str(v1.id),
            "target_environment": "STAGING",
            "source_environment": "DEVELOPMENT",
        },
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["eligible"] is True
    assert data["version_number"] == 1
    assert "version_id" in data


@pytest.mark.asyncio
async def test_direct_deploy_and_rollback_endpoint(
    client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    """POST .../deploy followed by POST .../rollback."""
    project, v1, v2 = await _create_test_project_and_versions(db_session)

    # 1. Direct deploy v1 to development
    resp_deploy1 = await client.post(
        f"/api/v1/projects/{project.id}/environments/development/deploy",
        json={"version_id": str(v1.id), "notes": "Initial deploy v1"},
    )
    assert resp_deploy1.status_code in (200, 201)
    assert resp_deploy1.json()["status"] == "SUCCEEDED"

    # 2. Direct deploy v2 to development
    resp_deploy2 = await client.post(
        f"/api/v1/projects/{project.id}/environments/development/deploy",
        json={"version_id": str(v2.id), "notes": "Upgrade to v2"},
    )
    assert resp_deploy2.status_code in (200, 201)
    assert resp_deploy2.json()["status"] == "SUCCEEDED"

    # Verify active version in development is v2
    env_resp = await client.get(f"/api/v1/projects/{project.id}/environments/development")
    assert env_resp.json()["current_version_id"] == str(v2.id)

    # 3. Rollback development to v1
    resp_rollback = await client.post(
        f"/api/v1/projects/{project.id}/environments/development/rollback",
        json={
            "target_version_id": str(v1.id),
            "reason": "Bug found in v2; rolling back to stable v1",
        },
    )
    assert resp_rollback.status_code == 200
    rb_data = resp_rollback.json()
    assert rb_data["operation"] == "ROLLBACK"
    assert rb_data["status"] == "SUCCEEDED"
    assert rb_data["version_id"] == str(v1.id)

    # Verify pointer reverted to v1
    env_resp2 = await client.get(f"/api/v1/projects/{project.id}/environments/development")
    assert env_resp2.json()["current_version_id"] == str(v1.id)


@pytest.mark.asyncio
async def test_promotion_endpoint(
    client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    """POST /api/v1/projects/{project_id}/environments/promote."""
    project, v1, _ = await _create_test_project_and_versions(db_session)

    # Deploy v1 to DEV first
    await client.post(
        f"/api/v1/projects/{project.id}/environments/development/deploy",
        json={"version_id": str(v1.id)},
    )

    # Promote to STAGING
    resp = await client.post(
        f"/api/v1/projects/{project.id}/environments/promote",
        json={
            "version_id": str(v1.id),
            "target_environment": "STAGING",
            "source_environment": "DEVELOPMENT",
            "notes": "Promoting v1 to staging for verification",
        },
    )
    assert resp.status_code in (200, 201)
    data = resp.json()
    assert data["operation"] == "PROMOTION"
    assert data["status"] == "SUCCEEDED"
    assert data["environment_type"] == "STAGING"

    # Verify STAGING environment pointer updated
    staging_resp = await client.get(f"/api/v1/projects/{project.id}/environments/staging")
    assert staging_resp.json()["current_version_id"] == str(v1.id)


@pytest.mark.asyncio
async def test_deployment_history_endpoints(
    client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    """GET .../deployments/all and GET .../{env}/deployments."""
    project, v1, _ = await _create_test_project_and_versions(db_session)

    # Perform deployment
    await client.post(
        f"/api/v1/projects/{project.id}/environments/development/deploy",
        json={"version_id": str(v1.id), "notes": "History test deploy"},
    )

    # 1. All deployments for project
    all_resp = await client.get(f"/api/v1/projects/{project.id}/environments/deployments/all")
    assert all_resp.status_code == 200
    all_data = all_resp.json()
    assert len(all_data) >= 1
    assert all_data[0]["version_id"] == str(v1.id)

    # 2. Deployments for specific environment
    dev_hist_resp = await client.get(f"/api/v1/projects/{project.id}/environments/development/deployments")
    assert dev_hist_resp.status_code == 200
    dev_data = dev_hist_resp.json()
    assert len(dev_data) >= 1


@pytest.mark.asyncio
async def test_project_isolation_security(
    client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    """Ensure Project A cannot access or deploy to Project B's environments."""
    proj_a, v1_a, _ = await _create_test_project_and_versions(db_session)
    proj_b, v1_b, _ = await _create_test_project_and_versions(db_session)

    # Get Project B's dev environment id
    resp_b = await client.get(f"/api/v1/projects/{proj_b.id}/environments/development")
    env_b_id = resp_b.json()["id"]

    # 1. Project A queries Project B's environment ID -> 404 (isolation)
    cross_get = await client.get(f"/api/v1/projects/{proj_a.id}/environments/{env_b_id}")
    assert cross_get.status_code == 404

    # 2. Project A tries to deploy Project B's version to Project A's environment -> 404
    cross_deploy = await client.post(
        f"/api/v1/projects/{proj_a.id}/environments/development/deploy",
        json={"version_id": str(v1_b.id)},
    )
    assert cross_deploy.status_code == 404
