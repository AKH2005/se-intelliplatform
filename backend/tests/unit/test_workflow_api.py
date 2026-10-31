"""Integration and Unit Tests for Workflow REST API Endpoints."""

import uuid
import pytest
from httpx import AsyncClient

from app.agents.registry import register_default_agents
from app.workflows.contracts import WorkflowStatus
from app.workflows.pipelines import (
    WORKFLOW_COMPREHENSIVE_AUDIT_ID,
    WORKFLOW_PROJECT_ESTIMATION_ID,
    WORKFLOW_SOFTWARE_DESIGN_ID,
)


@pytest.fixture(autouse=True)
def ensure_default_agents():
    """Ensure all default framework agents are registered before running tests."""
    register_default_agents()



DEFAULT_API_PROJECT_SETTINGS = {
    "ml_risk_inputs": {
        "project_size": "Medium",
        "team_experience_level": "High",
        "estimated_effort_hours": 950.0,
        "complexity_level": "High",
        "requirement_stability": "Moderate",
    },
    "ml_timeline_inputs": {
        "afp": 480.0,
        "input_count": 55.0,
        "output_count": 40.0,
        "enquiry_count": 30.0,
        "file_count": 25.0,
        "interface_count": 15.0,
        "resource_level": 2,
    },
    "ml_bug_inputs": {
        "loc": 45.0,
        "v(g)": 7.0,
        "ev(g)": 3.0,
        "iv(g)": 4.0,
        "n": 120.0,
        "v": 650.0,
        "l": 0.05,
        "d": 20.0,
        "i": 32.5,
        "e": 13000.0,
        "b": 0.22,
        "t": 722.0,
        "lOCode": 35.0,
        "lOComment": 5.0,
        "lOBlank": 5.0,
        "locCodeAndComment": 2.0,
        "uniq_Op": 15.0,
        "uniq_Opnd": 25.0,
        "total_Op": 60.0,
        "total_Opnd": 40.0,
        "branchCount": 12.0,
    },
}


@pytest.fixture
async def sample_project_id(client: AsyncClient) -> str:
    """Create a project and return its UUID string."""
    res = await client.post(
        "/api/v1/projects",
        json={
            "name": "API Workflow Project",
            "slug": f"api-wf-{uuid.uuid4().hex[:8]}",
            "settings": DEFAULT_API_PROJECT_SETTINGS,
        },
    )
    assert res.status_code == 201
    return res.json()["id"]



@pytest.fixture
async def sample_project_with_reqs(client: AsyncClient, sample_project_id: str) -> str:
    """Create a project populated with valid requirements."""
    await client.post(
        f"/api/v1/projects/{sample_project_id}/requirements",
        json={
            "title": "User Authentication",
            "description": "System shall authenticate users securely with JWT tokens.",
            "type": "FUNCTIONAL",
            "priority": "HIGH",
            "status": "APPROVED",
        },
    )
    await client.post(
        f"/api/v1/projects/{sample_project_id}/requirements",
        json={
            "title": "Low Latency API",
            "description": "API responses must be returned in under 200 milliseconds.",
            "type": "NON_FUNCTIONAL",
            "priority": "MEDIUM",
            "status": "APPROVED",
        },
    )
    return sample_project_id


# ==============================================================================
# 1. Workflow Discovery API Tests
# ==============================================================================

@pytest.mark.asyncio
async def test_get_workflows_discovery_list(client: AsyncClient):
    """Verify GET /api/v1/workflows returns metadata for all predefined pipelines."""
    res = await client.get("/api/v1/workflows")
    assert res.status_code == 200
    data = res.json()
    assert isinstance(data, list)
    assert len(data) >= 3

    ids = {item["workflow_id"] for item in data}
    assert WORKFLOW_SOFTWARE_DESIGN_ID in ids
    assert WORKFLOW_PROJECT_ESTIMATION_ID in ids
    assert WORKFLOW_COMPREHENSIVE_AUDIT_ID in ids

    # Validate safe declarative structure
    item = next(w for w in data if w["workflow_id"] == WORKFLOW_SOFTWARE_DESIGN_ID)
    assert item["name"] == "Software Design Workflow"
    assert item["step_count"] == 3
    assert "project_id" in item["required_inputs"]
    assert "snapshot_id" in item["optional_inputs"]
    assert len(item["steps"]) == 3
    assert item["steps"][0]["step_id"] == "requirement-analysis"
    assert item["steps"][0]["required"] is True


@pytest.mark.asyncio
async def test_get_workflow_by_id_success(client: AsyncClient):
    """Verify GET /api/v1/workflows/{workflow_id} returns single workflow details."""
    res = await client.get(f"/api/v1/workflows/{WORKFLOW_PROJECT_ESTIMATION_ID}")
    assert res.status_code == 200
    data = res.json()
    assert data["workflow_id"] == WORKFLOW_PROJECT_ESTIMATION_ID
    assert data["step_count"] == 3
    assert len(data["steps"]) == 3


@pytest.mark.asyncio
async def test_get_workflow_by_id_not_found(client: AsyncClient):
    """Verify GET /api/v1/workflows/{unknown} returns 404 RFC 7807 Problem Details."""
    res = await client.get("/api/v1/workflows/non-existent-workflow")
    assert res.status_code == 404
    data = res.json()
    assert data["status"] == 404
    assert data["title"] == "Resource Not Found"
    assert "trace_id" in data


# ==============================================================================
# 2. Workflow Execution API Tests
# ==============================================================================

@pytest.mark.asyncio
async def test_execute_workflow_live_context_success(
    client: AsyncClient,
    sample_project_with_reqs: str,
):
    """Verify POST /api/v1/workflows/{id}/execute returns 200 OK with WorkflowResultResponse."""
    payload = {
        "project_id": sample_project_with_reqs,
        "options": {"fail_fast": False},
    }

    res = await client.post(
        f"/api/v1/workflows/{WORKFLOW_PROJECT_ESTIMATION_ID}/execute",
        json=payload,
    )
    assert res.status_code == 200
    data = res.json()

    assert data["workflow_id"] == WORKFLOW_PROJECT_ESTIMATION_ID
    assert data["status"] in (WorkflowStatus.COMPLETED.value, WorkflowStatus.PARTIAL_SUCCESS.value)
    assert "workflow_execution_id" in data
    assert len(data["step_results"]) == 3
    assert "artifacts" in data
    assert "metadata" in data
    assert data["metadata"]["project_id"] == sample_project_with_reqs

    # Correlation verification
    assert "X-Correlation-ID" in res.headers
    assert res.headers["X-Correlation-ID"] != data["workflow_execution_id"]


@pytest.mark.asyncio
async def test_execute_software_design_workflow(
    client: AsyncClient,
    sample_project_with_reqs: str,
):
    """Verify Software Design Workflow executes sequentially with artifact enrichment."""
    payload = {
        "project_id": sample_project_with_reqs,
    }

    res = await client.post(
        f"/api/v1/workflows/{WORKFLOW_SOFTWARE_DESIGN_ID}/execute",
        json=payload,
    )
    assert res.status_code == 200
    data = res.json()

    assert data["workflow_id"] == WORKFLOW_SOFTWARE_DESIGN_ID
    assert data["status"] in (WorkflowStatus.COMPLETED.value, WorkflowStatus.PARTIAL_SUCCESS.value)
    assert len(data["step_results"]) == 3
    # Step results contain execution IDs
    assert data["step_results"][0]["step_id"] == "requirement-analysis"


@pytest.mark.asyncio
async def test_execute_comprehensive_audit_with_code_review(
    client: AsyncClient,
    sample_project_with_reqs: str,
):
    """Verify Comprehensive Audit executes with CodeReviewInput and Explainability options."""
    payload = {
        "project_id": sample_project_with_reqs,
        "code_review_input": {
            "files": [
                {
                    "file_path": "app/main.py",
                    "language": "python",
                    "content": "def run():\n    return 42\n",
                }
            ],
            "review_scope": "Architecture review",
        },
        "explainability_target_scope": "Design decisions",
        "explainability_user_query": "Explain database schema choices",
    }

    res = await client.post(
        f"/api/v1/workflows/{WORKFLOW_COMPREHENSIVE_AUDIT_ID}/execute",
        json=payload,
    )
    assert res.status_code == 200
    data = res.json()

    assert data["workflow_id"] == WORKFLOW_COMPREHENSIVE_AUDIT_ID
    assert len(data["step_results"]) == 9
    assert data["status"] in (WorkflowStatus.COMPLETED.value, WorkflowStatus.PARTIAL_SUCCESS.value)


@pytest.mark.asyncio
async def test_execute_workflow_snapshot_by_version(
    client: AsyncClient,
    sample_project_with_reqs: str,
):
    """Verify execution against snapshot version."""
    # Create snapshot
    snap_res = await client.post(
        f"/api/v1/projects/{sample_project_with_reqs}/context/snapshots",
        json={"summary": "API milestone 1"},
    )
    assert snap_res.status_code == 201
    version = snap_res.json()["version"]

    payload = {
        "project_id": sample_project_with_reqs,
        "snapshot_version": version,
    }

    res = await client.post(
        f"/api/v1/workflows/{WORKFLOW_PROJECT_ESTIMATION_ID}/execute",
        json=payload,
    )
    assert res.status_code == 200
    data = res.json()
    assert data["status"] in (WorkflowStatus.COMPLETED.value, WorkflowStatus.PARTIAL_SUCCESS.value)


@pytest.mark.asyncio
async def test_execute_workflow_snapshot_by_id(
    client: AsyncClient,
    sample_project_with_reqs: str,
):
    """Verify execution against snapshot UUID."""
    snap_res = await client.post(
        f"/api/v1/projects/{sample_project_with_reqs}/context/snapshots",
        json={"summary": "API milestone 2"},
    )
    assert snap_res.status_code == 201
    snap_id = snap_res.json()["id"]

    payload = {
        "project_id": sample_project_with_reqs,
        "snapshot_id": snap_id,
    }

    res = await client.post(
        f"/api/v1/workflows/{WORKFLOW_PROJECT_ESTIMATION_ID}/execute",
        json=payload,
    )
    assert res.status_code == 200
    data = res.json()
    assert data["status"] in (WorkflowStatus.COMPLETED.value, WorkflowStatus.PARTIAL_SUCCESS.value)


# ==============================================================================
# 3. Error Handling and Security Invariant Tests
# ==============================================================================

@pytest.mark.asyncio
async def test_execute_unknown_workflow_returns_404(
    client: AsyncClient,
    sample_project_id: str,
):
    """Verify executing an unknown workflow returns 404 Problem Details."""
    res = await client.post(
        "/api/v1/workflows/invalid-workflow-name/execute",
        json={"project_id": sample_project_id},
    )
    assert res.status_code == 404
    data = res.json()
    assert data["title"] == "Resource Not Found"
    assert "trace_id" in data


@pytest.mark.asyncio
async def test_execute_nonexistent_project_returns_404(client: AsyncClient):
    """Verify executing against non-existent project returns 404 Problem Details."""
    res = await client.post(
        f"/api/v1/workflows/{WORKFLOW_PROJECT_ESTIMATION_ID}/execute",
        json={"project_id": str(uuid.uuid4())},
    )
    assert res.status_code == 404
    data = res.json()
    assert data["title"] == "Resource Not Found"


@pytest.mark.asyncio
async def test_execute_nonexistent_snapshot_returns_404(
    client: AsyncClient,
    sample_project_id: str,
):
    """Verify executing against non-existent snapshot returns 404 Problem Details."""
    res = await client.post(
        f"/api/v1/workflows/{WORKFLOW_PROJECT_ESTIMATION_ID}/execute",
        json={
            "project_id": sample_project_id,
            "snapshot_id": str(uuid.uuid4()),
        },
    )
    assert res.status_code == 404
    data = res.json()
    assert data["title"] == "Resource Not Found"


@pytest.mark.asyncio
async def test_execute_ambiguous_snapshots_returns_422(
    client: AsyncClient,
    sample_project_id: str,
):
    """Verify providing both snapshot_id and snapshot_version returns 422 Validation Error."""
    res = await client.post(
        f"/api/v1/workflows/{WORKFLOW_PROJECT_ESTIMATION_ID}/execute",
        json={
            "project_id": sample_project_id,
            "snapshot_id": str(uuid.uuid4()),
            "snapshot_version": 1,
        },
    )
    assert res.status_code == 422
    data = res.json()
    assert data["title"] == "Validation Error"


@pytest.mark.asyncio
async def test_execute_extra_forbidden_fields_returns_422(
    client: AsyncClient,
    sample_project_id: str,
):
    """Verify submitting arbitrary unknown fields returns 422."""
    res = await client.post(
        f"/api/v1/workflows/{WORKFLOW_PROJECT_ESTIMATION_ID}/execute",
        json={
            "project_id": sample_project_id,
            "arbitrary_injected_field": "exploit",
        },
    )
    assert res.status_code == 422


@pytest.mark.asyncio
async def test_execute_code_review_security_traversal_returns_422(
    client: AsyncClient,
    sample_project_id: str,
):
    """Verify path traversal in code review payload returns 422."""
    res = await client.post(
        f"/api/v1/workflows/{WORKFLOW_COMPREHENSIVE_AUDIT_ID}/execute",
        json={
            "project_id": sample_project_id,
            "code_review_input": {
                "files": [
                    {
                        "file_path": "../../../etc/shadow",
                        "language": "python",
                        "content": "malicious",
                    }
                ]
            },
        },
    )
    assert res.status_code == 422
    data = res.json()
    assert data["title"] == "Validation Error"


@pytest.mark.asyncio
async def test_execute_code_review_exceeds_max_files_returns_422(
    client: AsyncClient,
    sample_project_id: str,
):
    """Verify exceeding MAX_FILES (10) returns 422."""
    files = [
        {"file_path": f"app/file_{i}.py", "language": "python", "content": "x = 1\n"}
        for i in range(11)
    ]
    res = await client.post(
        f"/api/v1/workflows/{WORKFLOW_COMPREHENSIVE_AUDIT_ID}/execute",
        json={
            "project_id": sample_project_id,
            "code_review_input": {"files": files},
        },
    )
    assert res.status_code == 422


@pytest.mark.asyncio
async def test_execute_unsupported_options_returns_422(
    client: AsyncClient,
    sample_project_id: str,
):
    """Verify unsupported options returns 422."""
    res = await client.post(
        f"/api/v1/workflows/{WORKFLOW_PROJECT_ESTIMATION_ID}/execute",
        json={
            "project_id": sample_project_id,
            "options": {"unauthorized_flag": True},
        },
    )
    assert res.status_code == 422


@pytest.mark.asyncio
async def test_arbitrary_agent_execution_still_prohibited(client: AsyncClient):
    """Verify security constraint: arbitrary single agent execution is NOT exposed."""
    res = await client.post("/api/v1/agents/execute", json={})
    assert res.status_code in (404, 405)
