"""Integration Tests for Testing, Multi-Tier Coverage Intelligence, and Selective Regression REST API (Phase 11L Stage 6)."""

from datetime import datetime, timezone
from unittest.mock import AsyncMock, patch
import uuid
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.project import Project, ProjectStatus
from app.models.requirement import (
    Requirement,
    RequirementPriority,
    RequirementStatus,
    RequirementType,
)
from app.testing.inventory.contracts import (
    DiscoveryProvenance,
    TestTier,
    UnifiedTestDefinition,
    UnifiedTestInventory,
)
from app.testing.regression.contracts import (
    IndividualTestResult,
    PlanSelectionReason,
    RegressionExecutionResult,
    RegressionExecutionStatus,
    RegressionPlan,
    RegressionPlanMode,
    SelectedTest,
    TestExecutionStatus,
    TierExecutionSummary,
)


@pytest.fixture
async def sample_project(db_session: AsyncSession) -> Project:
    """Create and persist a test project."""
    project = Project(
        name="Stage 6 API Testing Project",
        slug=f"stage6-api-{uuid.uuid4().hex[:8]}",
        status=ProjectStatus.IN_PROGRESS,
    )
    db_session.add(project)
    await db_session.commit()
    await db_session.refresh(project)
    return project


@pytest.fixture
async def sample_requirements(db_session: AsyncSession, sample_project: Project) -> list[Requirement]:
    """Create active requirements for coverage testing."""
    req1 = Requirement(
        project_id=sample_project.id,
        title="User Authentication",
        description="Support login with credentials",
        type=RequirementType.FUNCTIONAL,
        priority=RequirementPriority.HIGH,
        status=RequirementStatus.APPROVED,
        is_archived=False,
    )
    req2 = Requirement(
        project_id=sample_project.id,
        title="Session Persistence",
        description="Maintain authenticated session token",
        type=RequirementType.FUNCTIONAL,
        priority=RequirementPriority.MEDIUM,
        status=RequirementStatus.APPROVED,
        is_archived=False,
    )
    db_session.add_all([req1, req2])
    await db_session.commit()
    await db_session.refresh(req1)
    await db_session.refresh(req2)
    return [req1, req2]



# =============================================================================
# A. TEST INVENTORY ENDPOINT
# =============================================================================

@pytest.mark.asyncio
async def test_get_inventory_empty_project(client: AsyncClient, sample_project: Project):
    """Verify GET /projects/{project_id}/testing/inventory returns 200 with empty inventory."""
    res = await client.get(f"/api/v1/projects/{sample_project.id}/testing/inventory")
    assert res.status_code == 200
    data = res.json()
    assert data["project_id"] == str(sample_project.id).lower()
    assert data["total_tests"] == 0
    assert data["tests"] == []
    assert "tier_counts" in data


@pytest.mark.asyncio
async def test_get_inventory_nonexistent_project_returns_404(client: AsyncClient):
    """Verify non-existent project returns RFC 7807 404 Problem Details."""
    random_id = uuid.uuid4()
    res = await client.get(f"/api/v1/projects/{random_id}/testing/inventory")
    assert res.status_code == 404
    data = res.json()
    assert data["status"] == 404
    assert "not found" in data["detail"].lower()


@pytest.mark.asyncio
async def test_get_inventory_invalid_version_returns_404(client: AsyncClient, sample_project: Project):
    """Verify non-existent version_id returns 404."""
    random_ver = uuid.uuid4()
    res = await client.get(
        f"/api/v1/projects/{sample_project.id}/testing/inventory?version_id={random_ver}"
    )
    assert res.status_code == 404


# =============================================================================
# B. COVERAGE INTELLIGENCE ENDPOINT
# =============================================================================

@pytest.mark.asyncio
async def test_get_coverage_success(
    client: AsyncClient, sample_project: Project, sample_requirements: list[Requirement]
):
    """Verify GET /projects/{project_id}/testing/coverage returns 200 with UnifiedCoverageReport."""
    res = await client.get(f"/api/v1/projects/{sample_project.id}/testing/coverage")
    assert res.status_code == 200
    data = res.json()
    assert data["project_id"] == str(sample_project.id).lower()
    assert data["total_active_requirements"] == 4
    assert "combined_coverage_percentage" in data
    assert "tier_coverages" in data
    assert "requirement_traceability" in data
    assert len(data["combined_uncovered_requirement_ids"]) == 4


@pytest.mark.asyncio
async def test_get_coverage_nonexistent_project_returns_404(client: AsyncClient):
    """Verify GET /coverage on non-existent project returns 404."""
    random_id = uuid.uuid4()
    res = await client.get(f"/api/v1/projects/{random_id}/testing/coverage")
    assert res.status_code == 404


# =============================================================================
# C. COVERAGE GAPS ENDPOINT
# =============================================================================

@pytest.mark.asyncio
async def test_get_coverage_gaps_success(
    client: AsyncClient, sample_project: Project, sample_requirements: list[Requirement]
):
    """Verify GET /projects/{project_id}/testing/coverage/gaps returns 200 with gap analysis."""
    res = await client.get(f"/api/v1/projects/{sample_project.id}/testing/coverage/gaps")
    assert res.status_code == 200
    data = res.json()
    assert data["project_id"] == str(sample_project.id).lower()
    assert data["total_active_requirements"] == 4
    assert data["uncovered_count"] == 4
    assert len(data["gaps"]) == 4
    assert "tier_uncovered_summary" in data


@pytest.mark.asyncio
async def test_get_coverage_gaps_nonexistent_project_returns_404(client: AsyncClient):
    """Verify GET /coverage/gaps on non-existent project returns 404."""
    random_id = uuid.uuid4()
    res = await client.get(f"/api/v1/projects/{random_id}/testing/coverage/gaps")
    assert res.status_code == 404


# =============================================================================
# D. CHANGE IMPACT ENDPOINT
# =============================================================================

@pytest.mark.asyncio
async def test_analyze_impact_success(client: AsyncClient, sample_project: Project):
    """Verify POST /projects/{project_id}/testing/impact returns 200 with ChangeImpactReport."""
    files_map = {
        "app/service.py": "def process(): return 42\n",
        "tests/test_service.py": "def test_process(): assert process() == 42\n",
    }
    payload = {
        "changed_files": ["app/service.py"],
        "files_map": files_map,
    }
    res = await client.post(f"/api/v1/projects/{sample_project.id}/testing/impact", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["project_id"] == str(sample_project.id).lower()
    assert "changed_files" in data
    assert "all_affected_files" in data
    assert "affected_tests" in data


@pytest.mark.asyncio
async def test_analyze_impact_missing_changed_files_returns_422(
    client: AsyncClient, sample_project: Project
):
    """Verify POST /impact without changed_files or base/target versions returns 422."""
    payload = {"files_map": {"app/main.py": "x = 1\n"}}
    res = await client.post(f"/api/v1/projects/{sample_project.id}/testing/impact", json=payload)
    assert res.status_code == 422


@pytest.mark.asyncio
async def test_analyze_impact_nonexistent_project_returns_404(client: AsyncClient):
    """Verify POST /impact on non-existent project returns 404."""
    random_id = uuid.uuid4()
    payload = {"changed_files": ["app/main.py"], "files_map": {}}
    res = await client.post(f"/api/v1/projects/{random_id}/testing/impact", json=payload)
    assert res.status_code == 404


# =============================================================================
# E. REGRESSION PLAN ENDPOINT
# =============================================================================

@pytest.mark.asyncio
async def test_plan_regression_success(client: AsyncClient, sample_project: Project):
    """Verify POST /projects/{project_id}/testing/regression/plan returns 200 with RegressionPlan."""
    payload = {
        "changed_files": ["app/main.py"],
        "mode": "SELECTIVE",
        "auto_broaden": False,
    }
    res = await client.post(
        f"/api/v1/projects/{sample_project.id}/testing/regression/plan", json=payload
    )
    assert res.status_code == 200
    data = res.json()
    assert data["project_id"] == str(sample_project.id).lower()
    assert data["mode"] == "SELECTIVE"
    assert "selected_test_ids" in data
    assert "selected_tests" in data
    assert "is_execution_safe" in data


@pytest.mark.asyncio
async def test_plan_regression_modes(client: AsyncClient, sample_project: Project):
    """Verify planning supports BROAD and FULL modes."""
    for mode in ["BROAD", "FULL"]:
        payload = {"mode": mode}
        res = await client.post(
            f"/api/v1/projects/{sample_project.id}/testing/regression/plan", json=payload
        )
        assert res.status_code == 200
        assert res.json()["mode"] == mode


@pytest.mark.asyncio
async def test_plan_regression_nonexistent_project_returns_404(client: AsyncClient):
    """Verify POST /regression/plan on non-existent project returns 404."""
    random_id = uuid.uuid4()
    res = await client.post(f"/api/v1/projects/{random_id}/testing/regression/plan", json={})
    assert res.status_code == 404


# =============================================================================
# F. REGRESSION EXECUTION ENDPOINT
# =============================================================================

@pytest.mark.asyncio
async def test_execute_regression_auto_plan(client: AsyncClient, sample_project: Project):
    """Verify POST /regression/execute generates plan and returns execution result."""
    clean_proj = str(sample_project.id).lower()
    mock_result = RegressionExecutionResult(
        execution_id="exec-test-001",
        project_id=clean_proj,
        inventory_id="inv-test-001",
        mode=RegressionPlanMode.SELECTIVE,
        status=RegressionExecutionStatus.PASSED,
        duration_seconds=0.05,
    )

    with patch(
        "app.testing.regression.executor.RegressionExecutionService.execute_plan",
        new_callable=AsyncMock,
        return_value=mock_result,
    ) as mock_exec:
        payload = {"changed_files": ["app/main.py"], "mode": "SELECTIVE"}
        res = await client.post(
            f"/api/v1/projects/{sample_project.id}/testing/regression/execute", json=payload
        )
        assert res.status_code == 200
        data = res.json()
        assert data["status"] == "PASSED"
        assert data["project_id"] == clean_proj
        assert mock_exec.called


@pytest.mark.asyncio
async def test_execute_regression_rejects_cross_project_plan(
    client: AsyncClient, sample_project: Project
):
    """Verify executing a plan belonging to a different project returns 422."""
    other_project_id = str(uuid.uuid4())
    cross_project_plan = {
        "project_id": other_project_id,
        "inventory_id": "inv-cross-001",
        "mode": "SELECTIVE",
        "is_execution_safe": True,
        "selected_test_ids": [],
        "selected_tests": [],
        "selected_tests_by_tier": {},
        "selected_requirement_ids": [],
        "affected_requirement_ids": [],
        "protected_requirement_ids": [],
        "uncovered_affected_requirement_ids": [],
        "unrelated_requirement_ids": [],
        "selection_reasons_by_test": {},
        "broadening_reasons": [],
        "requires_broader_regression": False,
        "plan_warnings": [],
        "total_inventory_tests": 0,
        "unselected_test_count": 0,
        "metadata": {},
    }
    payload = {"plan": cross_project_plan}
    res = await client.post(
        f"/api/v1/projects/{sample_project.id}/testing/regression/execute", json=payload
    )
    assert res.status_code == 422
    assert "not authorized" in res.json()["detail"].lower()



@pytest.mark.asyncio
async def test_execute_regression_nonexistent_project_returns_404(client: AsyncClient):
    """Verify POST /regression/execute on non-existent project returns 404."""
    random_id = uuid.uuid4()
    res = await client.post(f"/api/v1/projects/{random_id}/testing/regression/execute", json={})
    assert res.status_code == 404
