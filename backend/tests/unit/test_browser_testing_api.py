"""Unit tests for Phase 11J Stage 5 Browser Testing REST API."""

import uuid
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch
import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_browser_testing_service
from app.browser.browser_testing_service import BrowserTestingService
from app.core.exceptions import ValidationError
from app.main import app
from app.models.development_version import DevelopmentVersion, DevelopmentVersionStatus
from app.models.project import Project, ProjectStatus
from app.models.workflow_execution import WorkflowExecution, WorkflowStatus
from app.schemas.browser_testing import BrowserTestRun, BrowserTestStatus


@pytest.mark.asyncio
async def test_run_browser_tests_endpoint_success(client: AsyncClient, db_session: AsyncSession):
    """Verify POST /browser/tests/run invokes BrowserTestingService and returns BrowserTestRun."""
    project_id = uuid.uuid4()
    version_id = uuid.uuid4()

    proj = Project(
        id=project_id,
        name="Browser Test Project",
        slug="browser-test-project",
        status=ProjectStatus.IN_PROGRESS,
    )
    db_session.add(proj)
    ver = DevelopmentVersion(
        id=version_id,
        project_id=project_id,
        version_number=1,
        content_hash="contenthash123",
        manifest_hash="manifesthash123",
        status=DevelopmentVersionStatus.GENERATED,
    )
    db_session.add(ver)
    await db_session.commit()

    mock_run = BrowserTestRun(
        run_id=uuid.uuid4(),
        project_id=project_id,
        version_id=version_id,
        status=BrowserTestStatus.PASSED,
        tests_total=2,
        tests_passed=2,
        tests_failed=0,
        summary="2/2 browser smoke tests passed.",
    )

    mock_svc = MagicMock()
    mock_svc.execute_browser_tests = AsyncMock(return_value=mock_run)
    app.dependency_overrides[get_browser_testing_service] = lambda: mock_svc

    try:
        resp = await client.post(
            f"/api/v1/projects/{project_id}/browser/tests/run",
            json={"development_version_id": str(version_id)},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "PASSED"
        assert data["tests_total"] == 2
        assert data["tests_passed"] == 2
        assert data["tests_failed"] == 0
        mock_svc.execute_browser_tests.assert_called_once_with(
            project_id=project_id,
            version_id=version_id,
        )
    finally:
        app.dependency_overrides.pop(get_browser_testing_service, None)


@pytest.mark.asyncio
async def test_run_browser_tests_defaults_to_active_version(client: AsyncClient, db_session: AsyncSession):
    """Verify omitting development_version_id automatically resolves active version."""
    project_id = uuid.uuid4()
    active_version_id = uuid.uuid4()

    proj = Project(
        id=project_id,
        name="Active Version Test",
        slug="active-ver-test",
        status=ProjectStatus.IN_PROGRESS,
        settings={"active_version_id": str(active_version_id)},
    )
    db_session.add(proj)
    ver = DevelopmentVersion(
        id=active_version_id,
        project_id=project_id,
        version_number=2,
        content_hash="hashactive",
        manifest_hash="manactive",
        status=DevelopmentVersionStatus.VERIFIED,
    )
    db_session.add(ver)
    await db_session.commit()

    mock_run = BrowserTestRun(
        run_id=uuid.uuid4(),
        project_id=project_id,
        version_id=active_version_id,
        status=BrowserTestStatus.PASSED,
        tests_total=1,
        tests_passed=1,
        tests_failed=0,
        summary="1/1 smoke tests passed.",
    )

    mock_svc = MagicMock()
    mock_svc.execute_browser_tests = AsyncMock(return_value=mock_run)
    app.dependency_overrides[get_browser_testing_service] = lambda: mock_svc

    try:
        resp = await client.post(
            f"/api/v1/projects/{project_id}/browser/tests/run",
            json={},
        )
        assert resp.status_code == 200
        mock_svc.execute_browser_tests.assert_called_once_with(
            project_id=project_id,
            version_id=active_version_id,
        )
    finally:
        app.dependency_overrides.pop(get_browser_testing_service, None)


@pytest.mark.asyncio
async def test_run_browser_tests_rejects_arbitrary_untrusted_parameters(client: AsyncClient, db_session: AsyncSession):
    """Verify request with untrusted Docker/command parameters is strictly rejected with 422."""
    project_id = uuid.uuid4()
    version_id = uuid.uuid4()

    proj = Project(id=project_id, name="Security Test", slug="sec-test", status=ProjectStatus.IN_PROGRESS)
    db_session.add(proj)
    await db_session.commit()

    # Client tries to pass arbitrary container command, image, or URL
    malicious_payload = {
        "development_version_id": str(version_id),
        "docker_command": "sh -c 'cat /etc/passwd'",
        "image": "evil/attacker:latest",
        "arbitrary_url": "http://evil.com",
    }

    resp = await client.post(
        f"/api/v1/projects/{project_id}/browser/tests/run",
        json=malicious_payload,
    )
    # Extra fields are forbidden by Pydantic ConfigDict(extra="forbid")
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_run_browser_tests_cross_project_version_rejection(client: AsyncClient, db_session: AsyncSession):
    """Verify version belonging to Project B is rejected when requested under Project A."""
    proj_a = Project(id=uuid.uuid4(), name="Project A", slug="proj-a", status=ProjectStatus.IN_PROGRESS)
    proj_b = Project(id=uuid.uuid4(), name="Project B", slug="proj-b", status=ProjectStatus.IN_PROGRESS)
    ver_b = DevelopmentVersion(
        id=uuid.uuid4(),
        project_id=proj_b.id,
        version_number=1,
        content_hash="hashb",
        manifest_hash="manb",
        status=DevelopmentVersionStatus.GENERATED,
    )
    db_session.add_all([proj_a, proj_b, ver_b])
    await db_session.commit()

    resp = await client.post(
        f"/api/v1/projects/{proj_a.id}/browser/tests/run",
        json={"development_version_id": str(ver_b.id)},
    )
    assert resp.status_code == 404
    data = resp.json()
    assert "DevelopmentVersion" in (data.get("detail") or data.get("title") or "")


@pytest.mark.asyncio
async def test_run_browser_tests_nonexistent_project_returns_404(client: AsyncClient, db_session: AsyncSession):
    """Verify nonexistent project returns 404."""
    random_project_id = uuid.uuid4()
    resp = await client.post(
        f"/api/v1/projects/{random_project_id}/browser/tests/run",
        json={},
    )
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_get_latest_browser_test_run_success(client: AsyncClient, db_session: AsyncSession):
    """Verify GET /browser/tests/latest returns the most recent test run."""
    project_id = uuid.uuid4()
    proj = Project(id=project_id, name="Latest Test", slug="latest-test", status=ProjectStatus.IN_PROGRESS)
    db_session.add(proj)
    await db_session.commit()

    mock_run = BrowserTestRun(
        run_id=uuid.uuid4(),
        project_id=project_id,
        version_id=uuid.uuid4(),
        status=BrowserTestStatus.PASSED,
        tests_total=1,
        tests_passed=1,
        tests_failed=0,
        summary="1/1 smoke tests passed.",
    )

    mock_svc = MagicMock()
    mock_svc.get_latest_browser_test_run = AsyncMock(return_value=mock_run)
    app.dependency_overrides[get_browser_testing_service] = lambda: mock_svc

    try:
        resp = await client.get(f"/api/v1/projects/{project_id}/browser/tests/latest")
        assert resp.status_code == 200
        data = resp.json()
        assert data["run_id"] == str(mock_run.run_id)
        assert data["status"] == "PASSED"
    finally:
        app.dependency_overrides.pop(get_browser_testing_service, None)


@pytest.mark.asyncio
async def test_get_browser_test_run_by_id_success(client: AsyncClient, db_session: AsyncSession):
    """Verify GET /browser/tests/{run_id} returns specific test run."""
    project_id = uuid.uuid4()
    run_id = uuid.uuid4()
    proj = Project(id=project_id, name="ID Test", slug="id-test", status=ProjectStatus.IN_PROGRESS)
    db_session.add(proj)
    await db_session.commit()

    mock_run = BrowserTestRun(
        run_id=run_id,
        project_id=project_id,
        version_id=uuid.uuid4(),
        status=BrowserTestStatus.FAILED,
        tests_total=2,
        tests_passed=1,
        tests_failed=1,
        summary="1/2 passed.",
        failure_reason="Root route timeout",
    )

    mock_svc = MagicMock()
    mock_svc.get_browser_test_run = AsyncMock(return_value=mock_run)
    app.dependency_overrides[get_browser_testing_service] = lambda: mock_svc

    try:
        resp = await client.get(f"/api/v1/projects/{project_id}/browser/tests/{run_id}")
        assert resp.status_code == 200
        data = resp.json()
        assert data["run_id"] == str(run_id)
        assert data["status"] == "FAILED"
        assert data["tests_failed"] == 1
    finally:
        app.dependency_overrides.pop(get_browser_testing_service, None)


@pytest.mark.asyncio
async def test_get_browser_screenshot_path_traversal_prevention(client: AsyncClient, db_session: AsyncSession):
    """Verify screenshot endpoint strictly rejects path traversal attempts."""
    project_id = uuid.uuid4()
    run_id = uuid.uuid4()
    proj = Project(id=project_id, name="Screenshot Sec Test", slug="sec-shot", status=ProjectStatus.IN_PROGRESS)
    db_session.add(proj)
    await db_session.commit()

    # Traversal filename attempt
    resp = await client.get(
        f"/api/v1/projects/{project_id}/browser/tests/{run_id}/screenshots/..%2F..%2Fetc%2Fpasswd.png"
    )
    # Must fail (400 or 404 or 422) - traversal strictly blocked
    assert resp.status_code in (400, 404, 422)

    # Disallowed file extension attempt
    resp_ext = await client.get(
        f"/api/v1/projects/{project_id}/browser/tests/{run_id}/screenshots/malicious.sh"
    )
    assert resp_ext.status_code in (400, 404, 422)


@pytest.mark.asyncio
async def test_development_version_immutability_preserved_during_browser_test_persistence(db_session: AsyncSession):
    """CRITICAL IMMUTABILITY REGRESSION TEST:
    Proves that executing browser tests does NOT mutate DevelopmentVersion.metadata_payload,
    DevelopmentVersion.status, or DevelopmentVersion.verification_summary.
    Results are persisted strictly through WorkflowExecution.artifacts['browser_test_run'].
    """
    project_id = uuid.uuid4()
    version_id = uuid.uuid4()
    wf_id = uuid.uuid4()

    proj = Project(
        id=project_id,
        name="Immutability Project",
        slug="immutability-proj",
        status=ProjectStatus.IN_PROGRESS,
    )
    db_session.add(proj)

    initial_metadata = {"summary": "Generated v1 code", "author": "system"}
    initial_ver_summary = {"is_verified": True, "verification_status": "PASSED"}

    wf = WorkflowExecution(
        workflow_execution_id=wf_id,
        project_id=project_id,
        workflow_id="code-generation",
        workflow_version="1.0.0",
        status=WorkflowStatus.COMPLETED,
        artifacts={"code-generation": {"total_files": 1, "summary": "Initial"}},
    )
    db_session.add(wf)

    ver = DevelopmentVersion(
        id=version_id,
        project_id=project_id,
        version_number=1,
        workflow_execution_id=wf_id,
        status=DevelopmentVersionStatus.VERIFIED,
        content_hash="contenthash123",
        manifest_hash="manifesthash123",
        metadata_payload=dict(initial_metadata),
        verification_summary=dict(initial_ver_summary),
    )
    db_session.add(ver)
    await db_session.commit()

    # Create browser test run result
    run_result = BrowserTestRun(
        run_id=uuid.uuid4(),
        project_id=project_id,
        version_id=version_id,
        status=BrowserTestStatus.PASSED,
        tests_total=3,
        tests_passed=3,
        tests_failed=0,
        summary="3/3 browser smoke tests passed.",
    )

    # Persist via BrowserTestingService
    service = BrowserTestingService(session=db_session)
    await service._persist_browser_test_results(project_id, version_id, run_result)

    # 1. Verify DevelopmentVersion historical record is 100% UNTOUCHED
    stmt_ver = select(DevelopmentVersion).where(DevelopmentVersion.id == version_id)
    res_ver = await db_session.execute(stmt_ver)
    reloaded_ver = res_ver.scalar_one()

    assert reloaded_ver.metadata_payload == initial_metadata, "DevelopmentVersion.metadata_payload was mutated!"
    assert reloaded_ver.status == DevelopmentVersionStatus.VERIFIED, "DevelopmentVersion.status was mutated!"
    assert reloaded_ver.verification_summary == initial_ver_summary, "DevelopmentVersion.verification_summary was mutated!"

    # 2. Verify results are stored inside WorkflowExecution.artifacts
    stmt_wf = select(WorkflowExecution).where(WorkflowExecution.workflow_execution_id == wf_id)
    res_wf = await db_session.execute(stmt_wf)
    reloaded_wf = res_wf.scalar_one()

    assert "browser_test_run" in reloaded_wf.artifacts
    assert reloaded_wf.artifacts["browser_test_run"]["run_id"] == str(run_result.run_id)
    assert reloaded_wf.artifacts["browser_test_run"]["status"] == "PASSED"

    # 3. Verify retrieval accesses WorkflowExecution.artifacts
    retrieved_run = await service.get_latest_browser_test_run(project_id, version_id)
    assert retrieved_run is not None
    assert retrieved_run.run_id == run_result.run_id
    assert retrieved_run.status == BrowserTestStatus.PASSED


@pytest.mark.asyncio
async def test_get_latest_browser_test_run_cross_project_rejection(client: AsyncClient, db_session: AsyncSession):
    """Verify GET /tests/latest with version belonging to another project returns 404."""
    proj_a = Project(id=uuid.uuid4(), name="Project Alpha", slug="proj-alpha", status=ProjectStatus.IN_PROGRESS)
    proj_b = Project(id=uuid.uuid4(), name="Project Beta", slug="proj-beta", status=ProjectStatus.IN_PROGRESS)
    ver_b = DevelopmentVersion(
        id=uuid.uuid4(),
        project_id=proj_b.id,
        version_number=1,
        content_hash="h1",
        manifest_hash="m1",
        status=DevelopmentVersionStatus.VERIFIED,
    )
    db_session.add_all([proj_a, proj_b, ver_b])
    await db_session.commit()

    resp = await client.get(
        f"/api/v1/projects/{proj_a.id}/browser/tests/latest?version_id={ver_b.id}"
    )
    assert resp.status_code == 404


def test_screenshot_path_traversal_rejection_vectors(tmp_path):
    """Verify get_screenshot_path strictly rejects varied path traversal attack vectors."""
    service = BrowserTestingService(artifacts_base_dir=tmp_path)
    pid = uuid.uuid4()
    rid = uuid.uuid4()

    malicious_filenames = [
        "../secret.png",
        "../../etc/passwd.png",
        "C:\\Windows\\System32\\cmd.exe",
        "/etc/shadow.png",
        "nested/path/image.png",
        "malicious.exe",
        "hack.sh",
        "script.py",
        "payload.js",
        "..%2Ftest.png",
    ]

    for fname in malicious_filenames:
        with pytest.raises(ValidationError):
            service.get_screenshot_path(pid, rid, fname)

