"""Integration tests for Project ZIP download endpoint."""

import io
import uuid
import zipfile
import pytest
from httpx import AsyncClient

from app.core.security import create_access_token, get_password_hash
from app.models.project import Project, ProjectStatus
from app.models.user import User, UserRole


@pytest.mark.asyncio
async def test_download_project_zip_success(client: AsyncClient, db_session):
    """Verify an authenticated authorized user can download a project as ZIP."""
    user = User(
        name="Download User",
        email="downloader@test.com",
        hashed_password=get_password_hash("DownloadPass123!"),
        role=UserRole.DEVELOPER,
        is_active=True,
    )
    db_session.add(user)
    await db_session.flush()

    project = Project(
        name="Downloadable Web App",
        slug="downloadable-web-app",
        description="A demonstrable web application for capstone.",
        status=ProjectStatus.IN_PROGRESS,
        owner_id=user.id,
    )
    db_session.add(project)
    await db_session.commit()

    token = create_access_token(data={"sub": str(user.id), "email": user.email, "role": user.role.value})

    resp = await client.get(
        f"/api/v1/projects/{project.id}/download",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    assert resp.headers["content-type"] == "application/zip"
    assert 'filename="downloadable-web-app.zip"' in resp.headers["content-disposition"]

    # Verify ZIP archive contents
    zip_buf = io.BytesIO(resp.content)
    with zipfile.ZipFile(zip_buf, "r") as zf:
        files = zf.namelist()
        assert "README.md" in files
        readme_text = zf.read("README.md").decode("utf-8")
        assert "Downloadable Web App" in readme_text


@pytest.mark.asyncio
async def test_download_project_zip_unauthorized_and_forbidden(client: AsyncClient, db_session):
    """Verify unauthorized or unpermitted users cannot download other users' projects."""
    owner = User(
        name="Owner User",
        email="owner_priv@test.com",
        hashed_password=get_password_hash("OwnerPass123!"),
        role=UserRole.DEVELOPER,
        is_active=True,
    )
    other_user = User(
        name="Attacker User",
        email="attacker@test.com",
        hashed_password=get_password_hash("AttackerPass123!"),
        role=UserRole.DEVELOPER,
        is_active=True,
    )
    db_session.add_all([owner, other_user])
    await db_session.flush()

    project = Project(
        name="Private Vault App",
        slug="private-vault-app",
        status=ProjectStatus.IN_PROGRESS,
        owner_id=owner.id,
    )
    db_session.add(project)
    await db_session.commit()

    # Unauthenticated request -> 401
    anon_resp = await client.get(f"/api/v1/projects/{project.id}/download")
    assert anon_resp.status_code == 401

    # Other user's request -> 403 Forbidden
    other_token = create_access_token(data={"sub": str(other_user.id), "email": other_user.email, "role": other_user.role.value})
    other_resp = await client.get(
        f"/api/v1/projects/{project.id}/download",
        headers={"Authorization": f"Bearer {other_token}"},
    )
    assert other_resp.status_code == 403


@pytest.mark.asyncio
async def test_download_missing_project_returns_404(client: AsyncClient):
    """Verify non-existent project UUID returns 404."""
    random_id = uuid.uuid4()
    resp = await client.get(f"/api/v1/projects/{random_id}/download")
    assert resp.status_code == 404
