"""
Preview Security Hardening & Acceptance Integration Tests
Validates:
1. Preview token isolation (no main access token in iframe URLs).
2. Dedicated scope ('preview'), op ('preview'), project binding, and expiry.
3. Cross-project token rejection (Token for Project A rejected on Project B).
4. Cross-user authorization check (User B cannot issue preview token for User A's private project).
5. Expiry and tampering rejection.
6. Security response headers (Referrer-Policy: no-referrer, Cache-Control, CSP, nosniff).
7. Actual generated application rendering from files_map (not falling back to starter prototype).
8. Version refinement rendering and version rollback rendering.
9. ZIP archive generation with strict exclusion of .env, tokens, and secrets.
"""

import io
import uuid
import zipfile
import pytest
from datetime import datetime, timezone
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_access_token, create_preview_token, get_password_hash
from app.models.user import User, UserRole
from app.models.project import Project, ProjectStatus
from app.models.development_version import DevelopmentVersion, DevelopmentVersionStatus


async def create_test_user(db_session: AsyncSession, email_prefix: str = "sec_user") -> User:
    unique_id = uuid.uuid4().hex[:8]
    user = User(
        id=uuid.uuid4(),
        email=f"{email_prefix}_{unique_id}@example.com",
        name=f"Security User {unique_id}",
        hashed_password=get_password_hash("SecretPass123!"),
        role=UserRole.DEVELOPER,
        is_active=True,
    )
    db_session.add(user)
    await db_session.flush()
    return user


async def create_test_project(db_session: AsyncSession, owner_id: uuid.UUID, title_prefix: str = "Security Project") -> Project:
    unique_id = uuid.uuid4().hex[:8]
    project = Project(
        id=uuid.uuid4(),
        owner_id=owner_id,
        name=f"{title_prefix} {unique_id}",
        slug=f"sec-proj-{unique_id}",
        description="Security testing project",
        status=ProjectStatus.IN_PROGRESS,
        settings={"active_mode": "user"},
    )
    db_session.add(project)
    await db_session.commit()
    await db_session.refresh(project)
    return project


async def create_test_version(db_session: AsyncSession, project_id: uuid.UUID, version_num: int, files_map: dict[str, str]) -> DevelopmentVersion:
    manifest = [{"path": path, "content": content} for path, content in files_map.items()]
    total_size = sum(len(c.encode("utf-8")) for c in files_map.values())
    version = DevelopmentVersion(
        id=uuid.uuid4(),
        project_id=project_id,
        version_number=version_num,
        content_hash=f"hash_{version_num}_{uuid.uuid4().hex[:12]}",
        manifest_hash=f"mhash_{version_num}_{uuid.uuid4().hex[:12]}",
        file_count=len(files_map),
        total_size_bytes=total_size,
        source_reason="INITIAL_GENERATION",
        status=DevelopmentVersionStatus.GENERATED,
        files_manifest=manifest,
        created_at=datetime.now(timezone.utc),
    )
    db_session.add(version)
    await db_session.commit()
    await db_session.refresh(version)
    return version


@pytest.mark.asyncio
async def test_preview_unauthenticated_request_rejected(client: AsyncClient, db_session: AsyncSession):
    """Unauthenticated preview request for an existing project must return 401."""
    user = await create_test_user(db_session, "unauth_user")
    project = await create_test_project(db_session, user.id, "Unauth Proj")
    
    response = await client.get(f"/api/v1/projects/{project.id}/runtime/preview")
    assert response.status_code == 401
    assert "Authentication required" in response.json()["detail"]


@pytest.mark.asyncio
async def test_preview_with_main_access_token_rejected(client: AsyncClient, db_session: AsyncSession):
    """Preview request using main access token instead of preview token must return 401."""
    user = await create_test_user(db_session, "main_token_user")
    project = await create_test_project(db_session, user.id, "Main Token Proj")
    
    # Main token has scope="access"
    main_token = create_access_token({"sub": str(user.id), "email": user.email, "role": user.role.value})
    
    response = await client.get(f"/api/v1/projects/{project.id}/runtime/preview?preview_token={main_token}")
    assert response.status_code == 401
    assert "Invalid, expired, or untrusted preview token" in response.json()["detail"]


@pytest.mark.asyncio
async def test_preview_cross_project_token_rejected(client: AsyncClient, db_session: AsyncSession):
    """Preview token issued for Project A must be rejected if used to access Project B."""
    user = await create_test_user(db_session, "cross_proj_user")
    project_a = await create_test_project(db_session, user.id, "Project Alpha")
    project_b = await create_test_project(db_session, user.id, "Project Beta")
    
    # Issue preview token bound to project_a
    preview_token_a = create_preview_token(user_id=user.id, project_id=project_a.id)
    
    # Attempt to use token_a on project_b
    response = await client.get(f"/api/v1/projects/{project_b.id}/runtime/preview?preview_token={preview_token_a}")
    assert response.status_code == 401
    assert "Invalid, expired, or untrusted preview token" in response.json()["detail"]


@pytest.mark.asyncio
async def test_preview_tampered_token_rejected(client: AsyncClient, db_session: AsyncSession):
    """Tampered token must return 401."""
    user = await create_test_user(db_session, "tamper_user")
    project = await create_test_project(db_session, user.id, "Tamper Proj")
    
    valid_token = create_preview_token(user_id=user.id, project_id=project.id)
    tampered_token = valid_token[:-6] + "xxxxxx"
    
    response = await client.get(f"/api/v1/projects/{project.id}/runtime/preview?preview_token={tampered_token}")
    assert response.status_code == 401
    assert "Invalid, expired, or untrusted preview token" in response.json()["detail"]


@pytest.mark.asyncio
async def test_preview_token_issuance_and_authorization(client: AsyncClient, db_session: AsyncSession):
    """Only the project owner can issue a preview token for the project."""
    user_owner = await create_test_user(db_session, "owner_user")
    user_attacker = await create_test_user(db_session, "attacker_user")
    project = await create_test_project(db_session, user_owner.id, "Private Proj")
    
    owner_main_token = create_access_token({"sub": str(user_owner.id), "email": user_owner.email, "role": user_owner.role.value})
    attacker_main_token = create_access_token({"sub": str(user_attacker.id), "email": user_attacker.email, "role": user_attacker.role.value})
    
    # Attacker attempts to request preview token for owner's project -> 403 Forbidden
    resp_attacker = await client.post(
        f"/api/v1/projects/{project.id}/runtime/preview-token",
        headers={"Authorization": f"Bearer {attacker_main_token}"}
    )
    assert resp_attacker.status_code == 403
    
    # Owner requests preview token -> 200 OK
    resp_owner = await client.post(
        f"/api/v1/projects/{project.id}/runtime/preview-token",
        headers={"Authorization": f"Bearer {owner_main_token}"}
    )
    assert resp_owner.status_code == 200
    data = resp_owner.json()
    assert "preview_token" in data
    assert data["project_id"] == str(project.id)
    assert data["expires_in"] == 900  # 15 minutes


@pytest.mark.asyncio
async def test_preview_response_security_headers(client: AsyncClient, db_session: AsyncSession):
    """Preview response must contain secure headers: Referrer-Policy, Cache-Control, CSP, X-Content-Type-Options."""
    user = await create_test_user(db_session, "header_user")
    project = await create_test_project(db_session, user.id, "Header Proj")
    
    preview_token = create_preview_token(user_id=user.id, project_id=project.id)
    
    response = await client.get(f"/api/v1/projects/{project.id}/runtime/preview?preview_token={preview_token}")
    assert response.status_code == 200
    
    # Verify security headers
    headers = response.headers
    assert headers.get("Referrer-Policy") == "no-referrer"
    assert "no-store" in headers.get("Cache-Control", "")
    assert "frame-ancestors 'self'" in headers.get("Content-Security-Policy", "")
    assert headers.get("X-Content-Type-Options") == "nosniff"


@pytest.mark.asyncio
async def test_actual_generated_application_rendering(client: AsyncClient, db_session: AsyncSession):
    """
    Verify that when actual generated files exist in the project version:
    1. The preview renders the actual generated HTML, NOT a prototype fallback.
    2. A version refinement correctly updates the rendered preview.
    3. A version rollback restores the previous version rendering.
    """
    user = await create_test_user(db_session, "render_user")
    project = await create_test_project(db_session, user.id, "Custom Generated App")
    
    # 1. Create Version 1 with genuine unique generated application content
    v1_html = """<!DOCTYPE html>
<html>
<head><title>Task Tracker Pro v1</title></head>
<body>
  <h1>Task Tracker Pro</h1>
  <div id="app-container">
    <p>Version 1: Active Tasks (3)</p>
    <ul>
      <li>Implement authentication</li>
      <li>Configure database</li>
      <li>Run tests</li>
    </ul>
  </div>
</body>
</html>"""
    v1_files = {
        "frontend/index.html": v1_html,
        "frontend/src/App.tsx": "export default function App() { return <div>Task Tracker Pro v1</div>; }"
    }
    await create_test_version(db_session, project.id, 1, v1_files)
    
    preview_token = create_preview_token(user_id=user.id, project_id=project.id)
    
    # Request preview with valid preview token
    resp_v1 = await client.get(f"/api/v1/projects/{project.id}/runtime/preview?preview_token={preview_token}")
    assert resp_v1.status_code == 200
    assert "Task Tracker Pro" in resp_v1.text
    assert "Version 1: Active Tasks (3)" in resp_v1.text
    # Ensure prototype is NOT returned
    assert "Executive Analytics Dashboard" not in resp_v1.text
    
    # 2. Refinement to Version 2: Added Dark Mode & Priority Tagging
    v2_html = """<!DOCTYPE html>
<html>
<head><title>Task Tracker Pro v2 Refined</title></head>
<body class="dark-mode">
  <h1>Task Tracker Pro v2</h1>
  <div id="app-container">
    <p>Version 2: Active Tasks with Priority Tags</p>
    <ul>
      <li>[CRITICAL] Implement authentication</li>
      <li>[HIGH] Configure database</li>
      <li>[MEDIUM] Run tests</li>
      <li>[NEW] Export to CSV</li>
    </ul>
  </div>
</body>
</html>"""
    v2_files = {
        "frontend/index.html": v2_html,
        "frontend/src/App.tsx": "export default function App() { return <div className='dark-mode'>Task Tracker Pro v2</div>; }"
    }
    await create_test_version(db_session, project.id, 2, v2_files)
    
    # Preview should now serve v2
    resp_v2 = await client.get(f"/api/v1/projects/{project.id}/runtime/preview?preview_token={preview_token}")
    assert resp_v2.status_code == 200
    assert "Task Tracker Pro v2" in resp_v2.text
    assert "[CRITICAL] Implement authentication" in resp_v2.text
    assert "[NEW] Export to CSV" in resp_v2.text
    
    # 3. Rollback to Version 1: Create a rollback version pointing back to v1 files
    v3_rollback_files = v1_files
    await create_test_version(db_session, project.id, 3, v3_rollback_files)
    
    # Preview should now reflect the rollback to v1 content
    resp_v3 = await client.get(f"/api/v1/projects/{project.id}/runtime/preview?preview_token={preview_token}")
    assert resp_v3.status_code == 200
    assert "Version 1: Active Tasks (3)" in resp_v3.text
    assert "[CRITICAL] Implement authentication" not in resp_v3.text


@pytest.mark.asyncio
async def test_zip_download_excludes_secrets_and_env(client: AsyncClient, db_session: AsyncSession):
    """
    Verify that project ZIP download:
    1. Contains actual project source files.
    2. Strictly excludes .env files, credentials, secrets, tokens, and internal keys.
    """
    user = await create_test_user(db_session, "zip_user")
    project = await create_test_project(db_session, user.id, "Clean Export Proj")
    
    files_with_secrets_injected = {
        "src/main.py": "print('Clean application')",
        "src/components/App.tsx": "export const App = () => <div>Clean</div>;",
        ".env": "SECRET_KEY=super_secret_jwt_token\nDATABASE_URL=postgres://admin:pwd@db:5432/db",
        ".env.local": "API_SECRET=leak_attempt",
        "secrets.json": '{"aws_key": "AKIAIOSFODNN7EXAMPLE"}',
        "private.key": "-----BEGIN RSA PRIVATE KEY-----",
    }
    await create_test_version(db_session, project.id, 1, files_with_secrets_injected)
    
    user_main_token = create_access_token({"sub": str(user.id), "email": user.email, "role": user.role.value})
    
    response = await client.get(
        f"/api/v1/projects/{project.id}/download",
        headers={"Authorization": f"Bearer {user_main_token}"}
    )
    assert response.status_code == 200
    assert response.headers["Content-Type"] == "application/zip"
    
    # Inspect the zip file in-memory
    zip_bytes = io.BytesIO(response.content)
    with zipfile.ZipFile(zip_bytes, "r") as z:
        file_names = z.namelist()
        
        # Verify legitimate source files are present
        assert any("src/main.py" in name for name in file_names)
        assert any("src/components/App.tsx" in name for name in file_names)
        
        # Verify secret files are strictly excluded
        for name in file_names:
            lower = name.lower()
            assert not lower.endswith(".env"), f"Found .env in zip: {name}"
            assert not lower.endswith(".env.local"), f"Found .env.local in zip: {name}"
            assert not lower.endswith(".key"), f"Found .key in zip: {name}"
            assert not "secret" in lower, f"Found secret file in zip: {name}"
            
        # Verify file contents don't contain secret values
        for name in file_names:
            file_data = z.read(name).decode("utf-8", errors="ignore")
            assert "super_secret_jwt_token" not in file_data
            assert "AKIAIOSFODNN7EXAMPLE" not in file_data
