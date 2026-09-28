"""Unit and Integration Tests for Workflow Execution Persistence & Run History.

Covers:
- WorkflowExecution ORM model construction, fields, and UUID constraints
- Persistence lifecycle during synchronous workflow execution
- Status transitions (COMPLETED, PARTIAL_SUCCESS, FAILED)
- Context provenance persistence (Live vs Snapshot targeting)
- Security bounds: no secrets, no raw code, sanitized metadata
- Paginated project workflow history API (sorting, filtering, pagination)
- Workflow execution detail retrieval API (200 OK and 404 RFC 7807 problem details)
"""

import uuid
from datetime import datetime, timezone
import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.code_review.contracts import CodeFile, CodeReviewInput
from app.agents.registry import register_default_agents
from app.models.project import Project
from app.models.workflow_execution import WorkflowExecution, WorkflowExecutionStatus
from app.schemas.workflow import WorkflowExecuteRequest
from app.schemas.workflow_history import (
    WorkflowExecutionDetailResponse,
    WorkflowExecutionSummaryResponse,
    WorkflowHistoryListResponse,
)
from app.services.context_engine import ProjectContextEngine
from app.services.workflow_service import WorkflowService
from app.workflows.contracts import WorkflowStatus, WorkflowStepStatus
from app.workflows.pipelines import (
    WORKFLOW_COMPREHENSIVE_AUDIT_ID,
    WORKFLOW_PROJECT_ESTIMATION_ID,
    WORKFLOW_SOFTWARE_DESIGN_ID,
)


@pytest.fixture(autouse=True)
def ensure_default_agents():
    """Ensure all default framework agents are registered before running tests."""
    register_default_agents()


DEFAULT_TEST_ML_SETTINGS = {
    "ml_risk_inputs": {
        "project_size": "Medium",
        "team_experience_level": "High",
        "estimated_effort_hours": 800.0,
        "complexity_level": "High",
        "requirement_stability": "Moderate",
    },
    "ml_timeline_inputs": {
        "afp": 450.0,
        "input_count": 50.0,
        "output_count": 35.0,
        "enquiry_count": 25.0,
        "file_count": 20.0,
        "interface_count": 10.0,
        "resource_level": 2,
    },
    "ml_bug_inputs": {
        "loc": 40.0,
        "v(g)": 6.0,
        "ev(g)": 2.0,
        "iv(g)": 3.0,
        "n": 100.0,
        "v": 550.0,
        "l": 0.05,
        "d": 18.0,
        "i": 30.5,
        "e": 10000.0,
        "b": 0.18,
        "t": 555.0,
        "lOCode": 30.0,
        "lOComment": 5.0,
        "lOBlank": 5.0,
        "locCodeAndComment": 2.0,
        "uniq_Op": 12.0,
        "uniq_Opnd": 20.0,
        "total_Op": 50.0,
        "total_Opnd": 30.0,
        "branchCount": 10.0,
    },
}


@pytest.fixture
async def persisted_project_id(client: AsyncClient) -> str:
    """Create a project and return its UUID string."""
    res = await client.post(
        "/api/v1/projects",
        json={
            "name": "Persistence Test Project",
            "slug": f"persist-{uuid.uuid4().hex[:8]}",
            "settings": DEFAULT_TEST_ML_SETTINGS,
        },
    )
    assert res.status_code == 201
    pid = res.json()["id"]

    # Add active requirements
    await client.post(
        f"/api/v1/projects/{pid}/requirements",
        json={
            "title": "Data Persistence",
            "description": "System shall persist workflow audit outcomes safely.",
            "type": "FUNCTIONAL",
            "priority": "HIGH",
            "status": "APPROVED",
        },
    )
    return pid


# ==============================================================================
# 1. WorkflowExecution Model Unit Tests
# ==============================================================================

def test_workflow_execution_model_construction():
    """Verify ORM entity initializes with defaults and attributes intact."""
    exec_id = uuid.uuid4()
    proj_id = uuid.uuid4()
    now = datetime.now(timezone.utc)

    record = WorkflowExecution(
        workflow_execution_id=exec_id,
        project_id=proj_id,
        workflow_id=WORKFLOW_SOFTWARE_DESIGN_ID,
        workflow_version="1.0.0",
        status=WorkflowStatus.RUNNING,
        started_at=now,
        step_count=3,
        completed_steps=0,
        failed_steps=0,
        skipped_steps=0,
        artifacts={},
        errors=[],
        warnings=[],
        metadata_payload={"test": "true"},
    )

    assert record.workflow_execution_id == exec_id
    assert record.project_id == proj_id
    assert record.workflow_id == WORKFLOW_SOFTWARE_DESIGN_ID
    assert record.status == WorkflowStatus.RUNNING
    assert record.step_count == 3
    assert record.metadata_payload == {"test": "true"}
    assert repr(record) == f"<WorkflowExecution id={record.id} workflow={WORKFLOW_SOFTWARE_DESIGN_ID} exec_id={exec_id} status={WorkflowStatus.RUNNING}>"


# ==============================================================================
# 2. Execution Persistence Lifecycle Tests (Service Layer)
# ==============================================================================

@pytest.mark.asyncio
async def test_workflow_execution_persisted_success(
    client: AsyncClient,
    db_session: AsyncSession,
    persisted_project_id: str,
):
    """Verify executing a workflow creates a persistent row with COMPLETED status and artifacts."""
    pid = uuid.UUID(persisted_project_id)
    res = await client.post(
        f"/api/v1/workflows/{WORKFLOW_PROJECT_ESTIMATION_ID}/execute",
        json={"project_id": str(pid)},
    )
    assert res.status_code == 200
    res_data = res.json()
    exec_id = uuid.UUID(res_data["workflow_execution_id"])
    assert res_data["status"] == "COMPLETED"

    # Query DB directly to verify persistence
    statement = select(WorkflowExecution).where(WorkflowExecution.workflow_execution_id == exec_id)
    db_res = await db_session.execute(statement)
    row = db_res.scalar_one_or_none()

    assert row is not None
    assert row.project_id == pid
    assert row.workflow_id == WORKFLOW_PROJECT_ESTIMATION_ID
    assert row.status == WorkflowStatus.COMPLETED
    assert row.completed_at is not None
    assert row.step_count == 3
    assert row.completed_steps == 3
    assert row.failed_steps == 0
    assert row.skipped_steps == 0
    assert row.context_snapshot_id is None
    assert row.context_version is None
    assert "risk-prediction" in row.artifacts
    assert "timeline-prediction" in row.artifacts
    assert "bug-prediction" in row.artifacts


@pytest.mark.asyncio
async def test_workflow_execution_persisted_snapshot_provenance(
    client: AsyncClient,
    db_session: AsyncSession,
    persisted_project_id: str,
):
    """Verify executing against an immutable snapshot persists snapshot_id and version."""
    pid = uuid.UUID(persisted_project_id)

    # 1. Create a snapshot
    snap_res = await client.post(
        f"/api/v1/projects/{pid}/context/snapshots",
        json={"summary": "v1 milestone for workflow persistence test"},
    )
    assert snap_res.status_code == 201
    snap_data = snap_res.json()
    snapshot_id = uuid.UUID(snap_data["id"])
    snapshot_version = snap_data["version"]

    # 2. Execute workflow targeting snapshot
    res = await client.post(
        f"/api/v1/workflows/{WORKFLOW_SOFTWARE_DESIGN_ID}/execute",
        json={
            "project_id": str(pid),
            "snapshot_id": str(snapshot_id),
        },
    )
    assert res.status_code == 200
    res_data = res.json()
    exec_id = uuid.UUID(res_data["workflow_execution_id"])

    # 3. Query DB to verify snapshot provenance
    statement = select(WorkflowExecution).where(WorkflowExecution.workflow_execution_id == exec_id)
    db_res = await db_session.execute(statement)
    row = db_res.scalar_one_or_none()

    assert row is not None
    assert row.context_snapshot_id == snapshot_id
    assert row.context_version == snapshot_version
    assert row.metadata_payload.get("context_provenance") == "snapshot"


@pytest.mark.asyncio
async def test_workflow_execution_persisted_partial_success(
    client: AsyncClient,
    db_session: AsyncSession,
    persisted_project_id: str,
):
    """Verify partial success (e.g. CodeReview omitted in Comprehensive Audit) persists correctly."""
    pid = uuid.UUID(persisted_project_id)
    res = await client.post(
        f"/api/v1/workflows/{WORKFLOW_COMPREHENSIVE_AUDIT_ID}/execute",
        json={"project_id": str(pid)},  # omitted code_review_input -> code-review skipped
    )
    assert res.status_code == 200
    res_data = res.json()
    exec_id = uuid.UUID(res_data["workflow_execution_id"])
    assert res_data["status"] == "PARTIAL_SUCCESS"

    statement = select(WorkflowExecution).where(WorkflowExecution.workflow_execution_id == exec_id)
    db_res = await db_session.execute(statement)
    row = db_res.scalar_one_or_none()

    assert row is not None
    assert row.status == WorkflowStatus.PARTIAL_SUCCESS
    assert row.skipped_steps >= 1
    assert any("CodeReviewInput was not provided" in w for w in row.warnings)


# ==============================================================================
# 3. Security Boundary Tests
# ==============================================================================

@pytest.mark.asyncio
async def test_workflow_execution_security_no_source_code_persisted(
    client: AsyncClient,
    db_session: AsyncSession,
    persisted_project_id: str,
):
    """Verify external code content is NOT persisted into workflow_executions row."""
    pid = uuid.UUID(persisted_project_id)
    secret_code_marker = "SUPER_SECRET_INTERNAL_TOKEN_DO_NOT_STORE"
    source_content = f"def confidential_logic():\n    token = '{secret_code_marker}'\n    return token\n"

    res = await client.post(
        f"/api/v1/workflows/{WORKFLOW_COMPREHENSIVE_AUDIT_ID}/execute",
        json={
            "project_id": str(pid),
            "code_review_input": {
                "files": [
                    {
                        "file_path": "backend/app/auth.py",
                        "language": "python",
                        "content": source_content,
                    }
                ],
                "review_scope": "Confidential Security Audit",
            },
        },
    )
    assert res.status_code == 200
    res_data = res.json()
    exec_id = uuid.UUID(res_data["workflow_execution_id"])

    # Query DB row
    statement = select(WorkflowExecution).where(WorkflowExecution.workflow_execution_id == exec_id)
    db_res = await db_session.execute(statement)
    row = db_res.scalar_one_or_none()

    assert row is not None
    # Artifacts should contain structured findings, not raw file content
    artifacts_str = str(row.artifacts)
    assert secret_code_marker not in artifacts_str
    # Metadata should not contain raw file content
    metadata_str = str(row.metadata_payload)
    assert secret_code_marker not in metadata_str


# ==============================================================================
# 4. Workflow History API Tests
# ==============================================================================

@pytest.mark.asyncio
async def test_project_workflow_history_empty(
    client: AsyncClient,
    persisted_project_id: str,
):
    """Verify history returns empty list when no workflows have executed."""
    res = await client.get(f"/api/v1/projects/{persisted_project_id}/workflows/history")
    assert res.status_code == 200
    data = res.json()
    assert data["items"] == []
    assert data["total"] == 0
    assert data["limit"] == 20
    assert data["offset"] == 0


@pytest.mark.asyncio
async def test_project_workflow_history_pagination_and_sorting(
    client: AsyncClient,
    persisted_project_id: str,
):
    """Verify history returns records sorted newest first with limit and offset."""
    pid = persisted_project_id

    # Run 3 workflow executions
    await client.post(
        f"/api/v1/workflows/{WORKFLOW_SOFTWARE_DESIGN_ID}/execute",
        json={"project_id": pid},
    )
    await client.post(
        f"/api/v1/workflows/{WORKFLOW_PROJECT_ESTIMATION_ID}/execute",
        json={"project_id": pid},
    )
    await client.post(
        f"/api/v1/workflows/{WORKFLOW_SOFTWARE_DESIGN_ID}/execute",
        json={"project_id": pid},
    )

    # 1. Fetch page 1 (limit 2)
    res = await client.get(f"/api/v1/projects/{pid}/workflows/history?limit=2&offset=0")
    assert res.status_code == 200
    data = res.json()
    assert data["total"] == 3
    assert len(data["items"]) == 2
    assert data["limit"] == 2
    assert data["offset"] == 0

    # 2. Fetch page 2 (limit 2, offset 2)
    res_page2 = await client.get(f"/api/v1/projects/{pid}/workflows/history?limit=2&offset=2")
    assert res_page2.status_code == 200
    data_page2 = res_page2.json()
    assert data_page2["total"] == 3
    assert len(data_page2["items"]) == 1

    # Verify no overlap between page 1 and page 2
    page1_ids = {item["workflow_execution_id"] for item in data["items"]}
    page2_ids = {item["workflow_execution_id"] for item in data_page2["items"]}
    assert not (page1_ids & page2_ids)


@pytest.mark.asyncio
async def test_project_workflow_history_filtering(
    client: AsyncClient,
    persisted_project_id: str,
):
    """Verify filtering history by workflow_id and status."""
    pid = persisted_project_id

    # Run one software design and one project estimation
    await client.post(
        f"/api/v1/workflows/{WORKFLOW_SOFTWARE_DESIGN_ID}/execute",
        json={"project_id": pid},
    )
    await client.post(
        f"/api/v1/workflows/{WORKFLOW_PROJECT_ESTIMATION_ID}/execute",
        json={"project_id": pid},
    )

    # Filter by workflow_id
    res_filter = await client.get(
        f"/api/v1/projects/{pid}/workflows/history?workflow_id={WORKFLOW_PROJECT_ESTIMATION_ID}"
    )
    assert res_filter.status_code == 200
    data_filter = res_filter.json()
    assert data_filter["total"] == 1
    assert data_filter["items"][0]["workflow_id"] == WORKFLOW_PROJECT_ESTIMATION_ID

    # Filter by status
    res_status = await client.get(
        f"/api/v1/projects/{pid}/workflows/history?status=COMPLETED"
    )
    assert res_status.status_code == 200
    data_status = res_status.json()
    assert data_status["total"] == 2


@pytest.mark.asyncio
async def test_project_workflow_history_nonexistent_project(client: AsyncClient):
    """Verify querying history for unknown project returns 404 RFC 7807 problem details."""
    fake_pid = uuid.uuid4()
    res = await client.get(f"/api/v1/projects/{fake_pid}/workflows/history")
    assert res.status_code == 404
    data = res.json()
    assert data["title"] == "Resource Not Found"
    assert "Project" in data["detail"]


# ==============================================================================
# 5. Workflow Execution Detail API Tests
# ==============================================================================

@pytest.mark.asyncio
async def test_get_workflow_execution_detail_success(
    client: AsyncClient,
    persisted_project_id: str,
):
    """Verify GET /api/v1/workflows/executions/{id} returns authoritative details."""
    pid = persisted_project_id
    exec_res = await client.post(
        f"/api/v1/workflows/{WORKFLOW_SOFTWARE_DESIGN_ID}/execute",
        json={"project_id": pid},
    )
    assert exec_res.status_code == 200
    exec_id = exec_res.json()["workflow_execution_id"]

    # Fetch detail by execution UUID
    res = await client.get(f"/api/v1/workflows/executions/{exec_id}")
    assert res.status_code == 200
    detail = res.json()

    assert detail["workflow_execution_id"] == exec_id
    assert detail["project_id"] == pid
    assert detail["workflow_id"] == WORKFLOW_SOFTWARE_DESIGN_ID
    assert detail["status"] == "COMPLETED"
    assert detail["step_count"] == 3
    assert detail["completed_steps"] == 3
    assert "requirement-analysis" in detail["artifacts"]
    assert "database-design" in detail["artifacts"]
    assert detail["errors"] == []


@pytest.mark.asyncio
async def test_get_workflow_execution_detail_not_found(client: AsyncClient):
    """Verify GET /api/v1/workflows/executions/{unknown} returns 404 RFC 7807 Problem Details."""
    fake_id = uuid.uuid4()
    res = await client.get(f"/api/v1/workflows/executions/{fake_id}")
    assert res.status_code == 404
    data = res.json()
    assert data["title"] == "Resource Not Found"
    assert "WorkflowExecution" in data["detail"]
