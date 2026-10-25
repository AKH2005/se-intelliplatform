"""Unit Tests for Phase 11L Stage 6 Testing Assistant Actions and Engineering Action Service."""

import uuid
from unittest.mock import AsyncMock, MagicMock
import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError, ValidationError
from app.models.project import Project, ProjectStatus
from app.models.requirement import Requirement, RequirementPriority, RequirementStatus, RequirementType
from app.schemas.assistant import (
    ActionCategory,
    ActionResult,
    ActionStatus,
)
from app.services.action_registry import (
    ACTION_REGISTRY,
    get_action_definition,
    is_confirmation_required,
    validate_action_parameters,
)
from app.services.engineering_action_service import EngineeringActionService
from app.services.requirement_service import RequirementService
from app.testing.inventory.contracts import (
    DiscoveryProvenance,
    TestTier,
    UnifiedTestDefinition,
    UnifiedTestInventory,
)
from app.testing.regression.contracts import (
    RegressionExecutionResult,
    RegressionExecutionStatus,
    RegressionPlan,
    RegressionPlanMode,
    SelectedTest,
)


# =============================================================================
# 1. ACTION REGISTRY INTEGRITY FOR TESTING ACTIONS
# =============================================================================

def test_testing_actions_registered_in_registry():
    """Verify all 6 Stage 6 actions are present in ACTION_REGISTRY with correct metadata."""
    expected_actions = {
        "GET_TEST_INVENTORY": (ActionCategory.READ_ONLY, False),
        "GET_COVERAGE_REPORT": (ActionCategory.READ_ONLY, False),
        "ANALYZE_COVERAGE_GAPS": (ActionCategory.ANALYSIS, False),
        "ANALYZE_REGRESSION_IMPACT": (ActionCategory.ANALYSIS, False),
        "PLAN_REGRESSION": (ActionCategory.GENERATION, False),
        "EXECUTE_REGRESSION": (ActionCategory.EXECUTION, False),
    }

    for action_id, (expected_category, expected_confirmation) in expected_actions.items():
        assert action_id in ACTION_REGISTRY
        defn = get_action_definition(action_id)
        assert defn.action_id == action_id
        assert defn.category == expected_category
        assert defn.requires_confirmation == expected_confirmation
        assert is_confirmation_required(action_id) == expected_confirmation


def test_testing_action_parameter_validation_and_forbid_extra():
    """Verify parameter validation accepts valid parameters and forbids extra unknown fields."""
    # GET_TEST_INVENTORY
    assert validate_action_parameters("GET_TEST_INVENTORY", {}) is not None
    assert validate_action_parameters("GET_TEST_INVENTORY", {"strict": True}) is not None
    with pytest.raises(ValidationError):
        validate_action_parameters("GET_TEST_INVENTORY", {"unknown_param": 123})

    # GET_COVERAGE_REPORT
    assert validate_action_parameters("GET_COVERAGE_REPORT", {}) is not None
    with pytest.raises(ValidationError):
        validate_action_parameters("GET_COVERAGE_REPORT", {"bad_field": True})

    # ANALYZE_COVERAGE_GAPS
    assert validate_action_parameters("ANALYZE_COVERAGE_GAPS", {}) is not None
    with pytest.raises(ValidationError):
        validate_action_parameters("ANALYZE_COVERAGE_GAPS", {"extra": "value"})

    # ANALYZE_REGRESSION_IMPACT
    assert validate_action_parameters(
        "ANALYZE_REGRESSION_IMPACT", {"changed_files": ["app/main.py"]}
    ) is not None
    with pytest.raises(ValidationError):
        validate_action_parameters(
            "ANALYZE_REGRESSION_IMPACT", {"changed_files": ["app/main.py"], "foo": "bar"}
        )

    # PLAN_REGRESSION
    assert validate_action_parameters(
        "PLAN_REGRESSION", {"mode": "SELECTIVE", "auto_broaden": False}
    ) is not None
    with pytest.raises(ValidationError):
        validate_action_parameters(
            "PLAN_REGRESSION", {"mode": "SELECTIVE", "invalid_option": 1}
        )

    # EXECUTE_REGRESSION
    assert validate_action_parameters("EXECUTE_REGRESSION", {"mode": "FULL"}) is not None
    with pytest.raises(ValidationError):
        validate_action_parameters("EXECUTE_REGRESSION", {"unauthorized_flag": True})


# =============================================================================
# 2. DISPATCH DELEGATION TESTS VIA ENGINEERING ACTION SERVICE
# =============================================================================

@pytest.fixture
async def sample_project(db_session: AsyncSession) -> Project:
    """Create test project."""
    project = Project(
        name="Assistant Testing Project",
        slug=f"assistant-proj-{uuid.uuid4().hex[:8]}",
        status=ProjectStatus.IN_PROGRESS,
    )
    db_session.add(project)
    await db_session.commit()
    await db_session.refresh(project)
    return project


@pytest.fixture
async def sample_requirements(db_session: AsyncSession, sample_project: Project) -> list[Requirement]:
    """Create active requirements."""
    req = Requirement(
        project_id=sample_project.id,
        title="Auth Feature",
        description="User Login",
        type=RequirementType.FUNCTIONAL,
        priority=RequirementPriority.HIGH,
        status=RequirementStatus.APPROVED,
        is_archived=False,
    )
    db_session.add(req)
    await db_session.commit()
    await db_session.refresh(req)
    return [req]


def make_action_service(
    session: AsyncSession,
    inventory_service: any = None,
    impact_service: any = None,
    regression_planner: any = None,
    regression_executor: any = None,
) -> EngineeringActionService:
    """Helper to construct EngineeringActionService with standard mocks."""
    version_svc = MagicMock()
    version_svc.get_active_version = AsyncMock(return_value=None)
    version_svc.get_version = AsyncMock(return_value=None)
    version_svc._resolve_version_files_map = AsyncMock(return_value={})

    wf_svc = MagicMock()
    wf_svc.list_executions = AsyncMock(return_value=[])

    req_svc = RequirementService(session)

    return EngineeringActionService(
        session=session,
        version_service=version_svc,
        verification_service=MagicMock(),
        requirement_service=req_svc,
        context_engine=MagicMock(),
        workflow_service=wf_svc,
        inventory_service=inventory_service,
        impact_service=impact_service,
        regression_planner=regression_planner,
        regression_executor=regression_executor,
    )


@pytest.mark.asyncio
async def test_dispatch_get_test_inventory(
    db_session: AsyncSession, sample_project: Project
):
    """Verify GET_TEST_INVENTORY dispatches to UnifiedTestInventoryService and returns ActionResult."""
    mock_inv_svc = MagicMock()
    clean_proj = str(sample_project.id).lower()
    mock_inventory = UnifiedTestInventory(
        inventory_id="inv-mock-001",
        project_id=clean_proj,
        total_tests=0,
        tests=[],
    )
    mock_inv_svc.build_inventory.return_value = mock_inventory

    service = make_action_service(
        session=db_session,
        inventory_service=mock_inv_svc,
    )

    result = await service.execute_action(
        action_id="GET_TEST_INVENTORY",
        parameters={},
        project_id=sample_project.id,
    )

    assert result.status == ActionStatus.SUCCESS
    assert result.action_id == "GET_TEST_INVENTORY"
    assert result.data["project_id"] == clean_proj
    assert "inventory_id" in result.data
    assert mock_inv_svc.build_inventory.called


@pytest.mark.asyncio
async def test_dispatch_get_coverage_report(
    db_session: AsyncSession, sample_project: Project, sample_requirements: list[Requirement]
):
    """Verify GET_COVERAGE_REPORT dispatches through UnifiedCoverageEngine."""
    service = make_action_service(session=db_session)

    result = await service.execute_action(
        action_id="GET_COVERAGE_REPORT",
        parameters={},
        project_id=sample_project.id,
    )

    assert result.status == ActionStatus.SUCCESS
    assert result.action_id == "GET_COVERAGE_REPORT"
    assert result.data["project_id"] == str(sample_project.id).lower()
    assert result.data["combined_coverage_percentage"] == 0.0


@pytest.mark.asyncio
async def test_dispatch_analyze_coverage_gaps(
    db_session: AsyncSession, sample_project: Project, sample_requirements: list[Requirement]
):
    """Verify ANALYZE_COVERAGE_GAPS returns structured gaps derived from coverage report."""
    service = make_action_service(session=db_session)

    result = await service.execute_action(
        action_id="ANALYZE_COVERAGE_GAPS",
        parameters={},
        project_id=sample_project.id,
    )

    assert result.status == ActionStatus.SUCCESS
    assert result.action_id == "ANALYZE_COVERAGE_GAPS"
    assert "gaps" in result.data
    assert "uncovered_count" in result.data
    assert result.data["uncovered_count"] > 0


@pytest.mark.asyncio
async def test_dispatch_analyze_regression_impact(
    db_session: AsyncSession, sample_project: Project
):
    """Verify ANALYZE_REGRESSION_IMPACT dispatches to ChangeImpactService."""
    service = make_action_service(session=db_session)

    result = await service.execute_action(
        action_id="ANALYZE_REGRESSION_IMPACT",
        parameters={"changed_files": ["app/main.py"]},
        project_id=sample_project.id,
    )

    assert result.status == ActionStatus.SUCCESS
    assert result.action_id == "ANALYZE_REGRESSION_IMPACT"
    assert result.data["project_id"] == str(sample_project.id).lower()
    assert "all_affected_files" in result.data


@pytest.mark.asyncio
async def test_dispatch_plan_regression(
    db_session: AsyncSession, sample_project: Project
):
    """Verify PLAN_REGRESSION dispatches to SelectiveRegressionPlanner."""
    service = make_action_service(session=db_session)

    result = await service.execute_action(
        action_id="PLAN_REGRESSION",
        parameters={"mode": "SELECTIVE", "changed_files": ["app/main.py"]},
        project_id=sample_project.id,
    )

    assert result.status == ActionStatus.SUCCESS
    assert result.action_id == "PLAN_REGRESSION"
    assert result.data["project_id"] == str(sample_project.id).lower()
    assert result.data["mode"] == "SELECTIVE"
    assert "selected_test_ids" in result.data


@pytest.mark.asyncio
async def test_dispatch_execute_regression(
    db_session: AsyncSession, sample_project: Project
):
    """Verify EXECUTE_REGRESSION dispatches to RegressionExecutionService."""
    clean_proj = str(sample_project.id).lower()
    mock_executor = AsyncMock()
    mock_result = RegressionExecutionResult(
        execution_id="exec-assistant-001",
        project_id=clean_proj,
        inventory_id="inv-assistant-001",
        mode=RegressionPlanMode.SELECTIVE,
        status=RegressionExecutionStatus.PASSED,
        duration_seconds=0.04,
    )
    mock_executor.execute_plan.return_value = mock_result

    service = make_action_service(
        session=db_session,
        regression_executor=mock_executor,
    )

    result = await service.execute_action(
        action_id="EXECUTE_REGRESSION",
        parameters={"mode": "SELECTIVE", "changed_files": ["app/main.py"]},
        project_id=sample_project.id,
    )

    assert result.status == ActionStatus.SUCCESS
    assert result.action_id == "EXECUTE_REGRESSION"
    assert result.data["status"] == "PASSED"
    assert result.data["project_id"] == clean_proj
    assert mock_executor.execute_plan.called


@pytest.mark.asyncio
async def test_project_isolation_in_testing_actions(
    db_session: AsyncSession, sample_project: Project
):
    """Verify cross-project version reference is rejected by _authorize_target."""
    other_version_id = uuid.uuid4()
    service = make_action_service(session=db_session)

    # Calling with a non-existent / cross-project version_id should raise NotFoundError
    with pytest.raises(NotFoundError):
        await service.execute_action(
            action_id="GET_TEST_INVENTORY",
            parameters={"version_id": str(other_version_id)},
            project_id=sample_project.id,
        )
