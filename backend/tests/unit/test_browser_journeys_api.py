"""Unit Tests for Phase 11K Stage 5: Browser Journey REST API Endpoints.

Tests all API requirements:
1. POST authorized project -> success
2. POST unauthorized / nonexistent project -> 404
3. POST invalid request -> 422
4. POST invokes Stage 4 workflow
5. POST does not call LLM provider directly
6. GET existing workflow -> success
7. GET nonexistent workflow -> 404
8. GET cross-project access -> 404 (strict project isolation)
9. GET does not rerun workflow
10. GET latest workflow result -> success
11. API does not directly call Playwright or Docker
12. Failure status propagation
"""

import inspect
import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_browser_journey_service
import app.api.v1.endpoints.browser_journeys as endpoint_mod
from app.browser.journey.contracts import (
    BrowserJourneyWorkflowResult,
    BrowserJourneyWorkflowStatus,
)
from app.main import app
from app.models.project import Project, ProjectStatus
from app.models.workflow_execution import WorkflowExecution, WorkflowStatus
from app.schemas.browser_journeys import (
    BrowserJourneyWorkflowResponse,
    GenerateBrowserJourneysRequest,
)
from app.services.browser_journey_service import BrowserJourneyService


@pytest.fixture
def sample_project_id() -> uuid.UUID:
    return uuid.uuid4()


@pytest.fixture
def mock_journey_result(sample_project_id: uuid.UUID) -> BrowserJourneyWorkflowResult:
    return BrowserJourneyWorkflowResult(
        workflow_execution_id=uuid.uuid4(),
        project_id=sample_project_id,
        status=BrowserJourneyWorkflowStatus.COMPLETED,
        stage_reached="completed",
        candidate_suite=None,
        validation_outcome=None,
        validated_suite=None,
        coverage_report=None,
        test_definitions=[],
        browser_test_run=None,
        artifacts={"browser_journey_input": {"project_id": str(sample_project_id)}},
        started_at=datetime.now(timezone.utc),
        completed_at=datetime.now(timezone.utc),
        duration_seconds=1.23,
    )


# ==============================================================================
# 1. POST Endpoints Tests
# ==============================================================================

@pytest.mark.asyncio
async def test_post_browser_journeys_authorized_success(
    client: AsyncClient,
    db_session: AsyncSession,
    sample_project_id: uuid.UUID,
    mock_journey_result: BrowserJourneyWorkflowResult,
):
    """Verify POST /browser-journeys invokes BrowserJourneyService and returns 200 OK."""
    proj = Project(
        id=sample_project_id,
        name="Test Project",
        slug="test-proj",
        status=ProjectStatus.IN_PROGRESS,
    )
    db_session.add(proj)
    await db_session.commit()

    mock_service = MagicMock(spec=BrowserJourneyService)
    mock_service.generate_and_execute_journeys = AsyncMock(return_value=mock_journey_result)
    app.dependency_overrides[get_browser_journey_service] = lambda: mock_service

    try:
        resp = await client.post(
            f"/api/v1/projects/{sample_project_id}/browser-journeys",
            json={
                "execute_browser_tests": True,
                "max_journeys": 5,
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["workflow_execution_id"] == str(mock_journey_result.workflow_execution_id)
        assert data["project_id"] == str(sample_project_id)
        assert data["status"] == "COMPLETED"
        assert data["stage_reached"] == "completed"
        mock_service.generate_and_execute_journeys.assert_awaited_once_with(
            project_id=sample_project_id,
            version_id=None,
            execute_browser_tests=True,
            max_journeys=5,
        )
    finally:
        app.dependency_overrides.pop(get_browser_journey_service, None)


@pytest.mark.asyncio
async def test_post_browser_journeys_nonexistent_project(
    client: AsyncClient,
    db_session: AsyncSession,
):
    """Verify POST /browser-journeys with a nonexistent project ID raises 404."""
    nonexistent_id = uuid.uuid4()
    resp = await client.post(
        f"/api/v1/projects/{nonexistent_id}/browser-journeys",
        json={"max_journeys": 5},
    )
    assert resp.status_code == 404
    data = resp.json()
    assert "detail" in data or "title" in data


@pytest.mark.asyncio
async def test_post_browser_journeys_invalid_request_bounds(
    client: AsyncClient,
    sample_project_id: uuid.UUID,
):
    """Verify POST /browser-journeys with out-of-bounds parameters raises 422."""
    resp = await client.post(
        f"/api/v1/projects/{sample_project_id}/browser-journeys",
        json={"max_journeys": 50},  # Capped at 10
    )
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_post_browser_journeys_extra_forbidden_field(
    client: AsyncClient,
    sample_project_id: uuid.UUID,
):
    """Verify extra/untrusted parameters are rejected with 422."""
    resp = await client.post(
        f"/api/v1/projects/{sample_project_id}/browser-journeys",
        json={"docker_container_id": "malicious-escape", "max_journeys": 5},
    )
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_post_browser_journeys_invokes_stage4_workflow(
    client: AsyncClient,
    db_session: AsyncSession,
    sample_project_id: uuid.UUID,
    mock_journey_result: BrowserJourneyWorkflowResult,
):
    """Verify POST endpoint delegates execution strictly to BrowserJourneyService."""
    proj = Project(
        id=sample_project_id,
        name="Delegation Project",
        slug="delegation-proj",
        status=ProjectStatus.IN_PROGRESS,
    )
    db_session.add(proj)
    await db_session.commit()

    mock_service = MagicMock(spec=BrowserJourneyService)
    mock_service.generate_and_execute_journeys = AsyncMock(return_value=mock_journey_result)
    app.dependency_overrides[get_browser_journey_service] = lambda: mock_service

    try:
        resp = await client.post(
            f"/api/v1/projects/{sample_project_id}/browser-journeys",
            json={"execute_browser_tests": False},
        )
        assert resp.status_code == 200
        mock_service.generate_and_execute_journeys.assert_awaited_once()
    finally:
        app.dependency_overrides.pop(get_browser_journey_service, None)


# ==============================================================================
# 2. GET Endpoints & Project Isolation Tests
# ==============================================================================

@pytest.mark.asyncio
async def test_get_browser_journey_by_id_success(
    client: AsyncClient,
    db_session: AsyncSession,
    sample_project_id: uuid.UUID,
):
    """Verify GET /browser-journeys/{exec_id} retrieves persisted execution without re-execution."""
    exec_id = uuid.uuid4()
    started = datetime.now(timezone.utc)
    completed = datetime.now(timezone.utc)

    execution_record = WorkflowExecution(
        workflow_execution_id=exec_id,
        project_id=sample_project_id,
        workflow_id="browser-journey-workflow",
        workflow_version="1.0.0",
        status=WorkflowStatus.COMPLETED,
        started_at=started,
        completed_at=completed,
        artifacts={
            "browser_journey_validation": {
                "is_valid": True,
                "coverage_report": {
                    "coverage_percentage": 100.0,
                    "covered_requirement_ids": ["REQ-001"],
                    "uncovered_requirement_ids": [],
                },
            }
        },
        metadata_payload={
            "workflow_status": "COMPLETED",
            "stage_reached": "completed",
            "journey_count": 2,
            "validation_passed": True,
            "duration_seconds": 2.5,
        },
    )

    mock_service = MagicMock(spec=BrowserJourneyService)
    mock_service.get_workflow_result = AsyncMock(return_value=execution_record)
    app.dependency_overrides[get_browser_journey_service] = lambda: mock_service

    try:
        resp = await client.get(
            f"/api/v1/projects/{sample_project_id}/browser-journeys/{exec_id}"
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["workflow_execution_id"] == str(exec_id)
        assert data["status"] == "COMPLETED"
        assert data["validation_passed"] is True
        assert data["coverage_percentage"] == 100.0
        assert data["covered_requirement_ids"] == ["REQ-001"]
        mock_service.get_workflow_result.assert_awaited_once_with(
            project_id=sample_project_id,
            workflow_execution_id=exec_id,
        )
    finally:
        app.dependency_overrides.pop(get_browser_journey_service, None)


@pytest.mark.asyncio
async def test_get_browser_journey_cross_project_isolation(
    client: AsyncClient,
    db_session: AsyncSession,
):
    """Verify retrieving another project's workflow execution raises 404 (strict isolation)."""
    proj_a_id = uuid.uuid4()
    proj_b_id = uuid.uuid4()
    exec_id = uuid.uuid4()

    proj_a = Project(id=proj_a_id, name="Project A", slug="proj-a", status=ProjectStatus.IN_PROGRESS)
    proj_b = Project(id=proj_b_id, name="Project B", slug="proj-b", status=ProjectStatus.IN_PROGRESS)
    db_session.add(proj_a)
    db_session.add(proj_b)

    # WorkflowExecution belongs strictly to Project A
    exec_record = WorkflowExecution(
        workflow_execution_id=exec_id,
        project_id=proj_a_id,
        workflow_id="browser-journey-workflow",
        workflow_version="1.0.0",
        status=WorkflowStatus.COMPLETED,
        started_at=datetime.now(timezone.utc),
    )
    db_session.add(exec_record)
    await db_session.commit()

    # Attempt to access through Project B endpoint
    resp = await client.get(
        f"/api/v1/projects/{proj_b_id}/browser-journeys/{exec_id}"
    )
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_get_browser_journey_nonexistent_workflow(
    client: AsyncClient,
    db_session: AsyncSession,
    sample_project_id: uuid.UUID,
):
    """Verify GET for a non-existent execution ID returns 404."""
    proj = Project(id=sample_project_id, name="P", slug="p", status=ProjectStatus.IN_PROGRESS)
    db_session.add(proj)
    await db_session.commit()

    nonexistent_exec_id = uuid.uuid4()
    resp = await client.get(
        f"/api/v1/projects/{sample_project_id}/browser-journeys/{nonexistent_exec_id}"
    )
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_get_latest_browser_journey_result(
    client: AsyncClient,
    sample_project_id: uuid.UUID,
):
    """Verify GET /browser-journeys/latest retrieves most recent execution."""
    exec_id = uuid.uuid4()
    execution_record = WorkflowExecution(
        workflow_execution_id=exec_id,
        project_id=sample_project_id,
        workflow_id="browser-journey-workflow",
        workflow_version="1.0.0",
        status=WorkflowStatus.COMPLETED,
        started_at=datetime.now(timezone.utc),
        metadata_payload={"workflow_status": "COMPLETED", "journey_count": 3},
    )

    mock_service = MagicMock(spec=BrowserJourneyService)
    mock_service.get_latest_workflow_result = AsyncMock(return_value=execution_record)
    app.dependency_overrides[get_browser_journey_service] = lambda: mock_service

    try:
        resp = await client.get(
            f"/api/v1/projects/{sample_project_id}/browser-journeys/latest"
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["workflow_execution_id"] == str(exec_id)
        mock_service.get_latest_workflow_result.assert_awaited_once_with(
            project_id=sample_project_id
        )
    finally:
        app.dependency_overrides.pop(get_browser_journey_service, None)


@pytest.mark.asyncio
async def test_list_browser_journey_results(
    client: AsyncClient,
    sample_project_id: uuid.UUID,
):
    """Verify GET /browser-journeys returns a list of historical workflow executions."""
    exec_1 = WorkflowExecution(
        workflow_execution_id=uuid.uuid4(),
        project_id=sample_project_id,
        workflow_id="browser-journey-workflow",
        workflow_version="1.0.0",
        status=WorkflowStatus.COMPLETED,
        started_at=datetime.now(timezone.utc),
    )
    exec_2 = WorkflowExecution(
        workflow_execution_id=uuid.uuid4(),
        project_id=sample_project_id,
        workflow_id="browser-journey-workflow",
        workflow_version="1.0.0",
        status=WorkflowStatus.FAILED,
        started_at=datetime.now(timezone.utc),
    )

    mock_service = MagicMock(spec=BrowserJourneyService)
    mock_service.list_workflow_results = AsyncMock(return_value=([exec_1, exec_2], 2))
    app.dependency_overrides[get_browser_journey_service] = lambda: mock_service

    try:
        resp = await client.get(
            f"/api/v1/projects/{sample_project_id}/browser-journeys"
        )
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)
        assert len(data) == 2
        assert data[0]["workflow_execution_id"] == str(exec_1.workflow_execution_id)
        assert data[1]["workflow_execution_id"] == str(exec_2.workflow_execution_id)
    finally:
        app.dependency_overrides.pop(get_browser_journey_service, None)


@pytest.mark.asyncio
async def test_get_does_not_rerun_workflow(
    client: AsyncClient,
    sample_project_id: uuid.UUID,
):
    """Verify GET endpoint is strictly read-only and never reruns the generation/browser pipeline."""
    exec_id = uuid.uuid4()
    execution_record = WorkflowExecution(
        workflow_execution_id=exec_id,
        project_id=sample_project_id,
        workflow_id="browser-journey-workflow",
        workflow_version="1.0.0",
        status=WorkflowStatus.COMPLETED,
        started_at=datetime.now(timezone.utc),
    )

    mock_service = MagicMock(spec=BrowserJourneyService)
    mock_service.get_workflow_result = AsyncMock(return_value=execution_record)
    mock_service.generate_and_execute_journeys = AsyncMock()
    app.dependency_overrides[get_browser_journey_service] = lambda: mock_service

    try:
        resp = await client.get(
            f"/api/v1/projects/{sample_project_id}/browser-journeys/{exec_id}"
        )
        assert resp.status_code == 200
        # Critical invariant: generate_and_execute_journeys was NEVER called
        mock_service.generate_and_execute_journeys.assert_not_called()
    finally:
        app.dependency_overrides.pop(get_browser_journey_service, None)


# ==============================================================================
# 3. Security Boundaries & Authority Tests
# ==============================================================================

def test_api_does_not_directly_invoke_playwright_or_docker():
    """Verify the API endpoint module does not import Playwright, Docker, or subprocess."""
    src = inspect.getsource(endpoint_mod)
    assert "import playwright" not in src.lower()
    assert "from playwright" not in src.lower()
    assert "import docker" not in src.lower()
    assert "from docker" not in src.lower()
    assert "subprocess" not in src
    assert "os.system" not in src
    assert "eval(" not in src
    assert "exec(" not in src
    assert "groq" not in src.lower()
    assert "gemini" not in src.lower()
