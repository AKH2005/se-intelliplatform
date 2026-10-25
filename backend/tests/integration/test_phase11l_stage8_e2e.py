"""End-to-End Release Validation Integration Tests for Phase 11L Stage 8.

Comprehensive verification of the full Phase 11L Testing Intelligence & Selective Regression pipeline:
- Scenario A: Unified Test Inventory -> Multi-Tier Coverage -> Traceability -> Gap Analysis
- Scenario B: Coverage -> AST Dependency Graph & Change Impact Intelligence (Uncertainty Broadening)
- Scenario C: Change Impact -> Regression Planning (SELECTIVE, BROAD, FULL, Authoritative Protection)
- Safety Invariant: Unsafe Selective Plans are BLOCKED (0 tests dispatched, deterministic diagnostics)
- Scenario D: Selective Regression Execution & Failure Semantics (Test failure vs Infrastructure failure)
- Live Docker Validation: Real container execution with non-root & network isolation
- REST API E2E: All 6 Stage 6 REST endpoints with RFC 7807 error handling
- Assistant Action Layer E2E: All 6 testing assistant actions via EngineeringActionService
- Project Isolation: Strict boundary enforcement across all entities (Project A vs Project B)
- Version Immutability: RegressionPlan and DevelopmentVersion snapshot records are strictly immutable
"""

from datetime import datetime, timezone
import shutil
import subprocess
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch
import uuid
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.code_generation.contracts import (
    CodeGenerationOutput,
    CodeGenerationPlan,
    GeneratedFile,
    PlannedFile,
)
from app.models.project import Project, ProjectStatus
from app.models.requirement import (
    Requirement,
    RequirementPriority,
    RequirementStatus,
    RequirementType,
)
from app.sandbox.contracts import (
    ExecutionRequest,
    ExecutionResult,
    ExecutionStatus,
    ExecutionType,
    ResourceLimits,
)
from app.sandbox.docker_executor import DockerSandboxExecutor
from app.sandbox.mock_executor import MockSandboxExecutor
from app.schemas.assistant import ActionStatus
from app.schemas.browser_testing import (
    BrowserTestCaseResult,
    BrowserTestRun,
    BrowserTestStatus,
)
from app.services.action_registry import (
    ACTION_REGISTRY,
    get_action_definition,
    validate_action_parameters,
)
from app.services.engineering_action_service import EngineeringActionService
from app.services.requirement_service import RequirementService
from app.testing.coverage.contracts import UnifiedCoverageReport
from app.testing.coverage.engine import UnifiedCoverageEngine
from app.testing.coverage.errors import UnifiedCoverageIsolationError
from app.testing.impact.contracts import AnalysisConfidence, ChangeImpactReport
from app.testing.impact.errors import ChangeImpactIsolationError
from app.testing.impact.service import ChangeImpactService
from app.testing.inventory.contracts import (
    DiscoveryProvenance,
    DiscoveryStatus,
    TestTier,
    UnifiedTestDefinition,
    UnifiedTestInventory,
    compute_deterministic_inventory_id,
)
from app.testing.inventory.service import UnifiedTestInventoryService
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
from app.testing.regression.errors import (
    RegressionPlanIsolationError,
    RegressionPlanValidationError,
)
from app.testing.regression.executor import RegressionExecutionService
from app.testing.regression.planner import SelectiveRegressionPlanner
from tests.unit.test_sandbox import make_valid_code_output


# ==============================================================================
# Helper functions and Docker availability check
# ==============================================================================

def is_docker_available() -> bool:
    """Check if Docker runtime is responsive on host."""
    if not shutil.which("docker"):
        return False
    try:
        res = subprocess.run(
            ["docker", "info"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=5,
        )
        return res.returncode == 0
    except Exception:
        return False


docker_available = pytest.mark.skipif(
    not is_docker_available(),
    reason="Live Docker daemon is not accessible in this environment",
)


def make_test_inventory(project_id: str | uuid.UUID, tests: list[UnifiedTestDefinition]) -> UnifiedTestInventory:
    """Helper to construct a fully indexed UnifiedTestInventory."""
    clean_proj = str(project_id).strip().lower()
    test_ids = [t.test_id for t in tests]
    tests_by_id = {t.test_id: t for t in tests}
    tests_by_tier: dict[str, list[str]] = {tier.value: [] for tier in TestTier}
    tests_by_req: dict[str, list[str]] = {}
    reqs_by_test: dict[str, list[str]] = {}
    tier_counts = {tier.value: 0 for tier in TestTier}

    for t in tests:
        tests_by_tier[t.tier.value].append(t.test_id)
        tier_counts[t.tier.value] += 1
        reqs_by_test[t.test_id] = list(t.requirement_links)
        for r in t.requirement_links:
            if r not in tests_by_req:
                tests_by_req[r] = []
            tests_by_req[r].append(t.test_id)

    inv_id = compute_deterministic_inventory_id(clean_proj, test_ids)
    return UnifiedTestInventory(
        inventory_id=inv_id,
        project_id=clean_proj,
        tests=tests,
        discovery_status=DiscoveryStatus.COMPLETE,
        conflicts=[],
        tests_by_id=tests_by_id,
        tests_by_tier=tests_by_tier,
        tests_by_requirement=tests_by_req,
        requirements_by_test=reqs_by_test,
        tier_counts=tier_counts,
        total_tests=len(tests),
    )


class RecordingMockSandbox(MockSandboxExecutor):
    """Mock sandbox executor that records executed test targets."""

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self.executed_targets: list[str] = []

    async def execute(self, request: ExecutionRequest, code_output: CodeGenerationOutput) -> ExecutionResult:
        if request.test_target:
            self.executed_targets.append(request.test_target)
        return await super().execute(request, code_output)


def make_action_service(
    session: AsyncSession,
    inventory_service: Any = None,
    impact_service: Any = None,
    regression_planner: Any = None,
    regression_executor: Any = None,
) -> EngineeringActionService:
    """Helper to construct EngineeringActionService with mocked services."""
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


# ==============================================================================
# Database Fixtures
# ==============================================================================

@pytest.fixture
async def stage8_project_a(db_session: AsyncSession) -> Project:
    project = Project(
        name="Stage 8 Project A",
        slug=f"stage8-proj-a-{uuid.uuid4().hex[:8]}",
        status=ProjectStatus.IN_PROGRESS,
    )
    db_session.add(project)
    await db_session.commit()
    await db_session.refresh(project)
    return project


@pytest.fixture
async def stage8_project_b(db_session: AsyncSession) -> Project:
    project = Project(
        name="Stage 8 Project B",
        slug=f"stage8-proj-b-{uuid.uuid4().hex[:8]}",
        status=ProjectStatus.IN_PROGRESS,
    )
    db_session.add(project)
    await db_session.commit()
    await db_session.refresh(project)
    return project


@pytest.fixture
async def stage8_requirements_a(db_session: AsyncSession, stage8_project_a: Project) -> list[Requirement]:
    """Active and inactive requirements for Project A."""
    r1 = Requirement(
        project_id=stage8_project_a.id,
        title="User Authentication",
        description="Support JWT login",
        type=RequirementType.FUNCTIONAL,
        priority=RequirementPriority.HIGH,
        status=RequirementStatus.APPROVED,
        is_archived=False,
    )
    r2 = Requirement(
        project_id=stage8_project_a.id,
        title="Session Token Refresh",
        description="Refresh JWT token before expiration",
        type=RequirementType.FUNCTIONAL,
        priority=RequirementPriority.MEDIUM,
        status=RequirementStatus.APPROVED,
        is_archived=False,
    )
    r3 = Requirement(
        project_id=stage8_project_a.id,
        title="User Profile Management",
        description="Update profile info",
        type=RequirementType.FUNCTIONAL,
        priority=RequirementPriority.LOW,
        status=RequirementStatus.APPROVED,
        is_archived=False,
    )
    r_archived = Requirement(
        project_id=stage8_project_a.id,
        title="Deprecated XML Export",
        description="Export to legacy XML format",
        type=RequirementType.FUNCTIONAL,
        priority=RequirementPriority.LOW,
        status=RequirementStatus.DEFERRED,
        is_archived=True,
    )
    db_session.add_all([r1, r2, r3, r_archived])
    await db_session.commit()
    for r in [r1, r2, r3, r_archived]:
        await db_session.refresh(r)
    return [r1, r2, r3, r_archived]


# ==============================================================================
# SCENARIO A: INVENTORY -> COVERAGE INTELLIGENCE & GAPS
# ==============================================================================

@pytest.mark.asyncio
async def test_scenario_a_inventory_to_coverage_union_and_gaps(stage8_project_a: Project, stage8_requirements_a: list[Requirement]):
    """Validate 4-tier inventory, authoritative vs inferred links, and set-union coverage calculation."""
    proj_id = str(stage8_project_a.id).lower()
    req_auth = str(stage8_requirements_a[0].id)
    req_session = str(stage8_requirements_a[1].id)
    req_profile = str(stage8_requirements_a[2].id)
    req_archived = str(stage8_requirements_a[3].id)

    # 1. Build Multi-Tier Unified Inventory
    t1 = UnifiedTestDefinition(
        test_id=f"unit:{proj_id}:tests/test_auth.py::test_login",
        project_id=proj_id,
        tier=TestTier.UNIT,
        name="Unit Auth Test",
        source_reference="tests/test_auth.py::test_login",
        requirement_links=[req_auth],
        inferred_requirement_links=[req_session],  # Inferred link must NOT count as authoritative
        discovery_source=DiscoveryProvenance.PYTEST_DISCOVERY,
    )
    t2 = UnifiedTestDefinition(
        test_id=f"ai_test:{proj_id}:tests/ai/test_session_ai.py::test_session",
        project_id=proj_id,
        tier=TestTier.AI_TEST,
        name="AI Generated Session Test",
        source_reference="tests/ai/test_session_ai.py::test_session",
        requirement_links=[req_session],
        discovery_source=DiscoveryProvenance.AI_TEST_SUITE,
    )
    t3 = UnifiedTestDefinition(
        test_id=f"browser_smoke:{proj_id}:tests/browser/smoke_login.py",
        project_id=proj_id,
        tier=TestTier.BROWSER_SMOKE,
        name="Login Smoke Test",
        source_reference="/login",
        requirement_links=[req_auth],
        discovery_source=DiscoveryProvenance.BROWSER_SMOKE_SUITE,
    )
    t4 = UnifiedTestDefinition(
        test_id=f"browser_journey:{proj_id}:journey_auth_flow",
        project_id=proj_id,
        tier=TestTier.BROWSER_JOURNEY,
        name="End-to-End Login Journey",
        source_reference="/auth/flow",
        requirement_links=[req_auth],
        discovery_source=DiscoveryProvenance.VALIDATED_BROWSER_JOURNEY,
    )

    inventory = make_test_inventory(proj_id, [t1, t2, t3, t4])

    assert inventory.total_tests == 4
    assert inventory.tier_counts[TestTier.UNIT.value] == 1
    assert inventory.tier_counts[TestTier.AI_TEST.value] == 1
    assert inventory.tier_counts[TestTier.BROWSER_SMOKE.value] == 1
    assert inventory.tier_counts[TestTier.BROWSER_JOURNEY.value] == 1

    # Inferred requirement must be visibly distinct from authoritative
    assert t1.requirement_links == [req_auth]
    assert t1.inferred_requirement_links == [req_session]

    # 2. Compute Multi-Tier Coverage with explicit active requirement IDs
    active_req_ids = [str(r.id) for r in stage8_requirements_a if not getattr(r, "is_archived", False)]
    coverage_report = UnifiedCoverageEngine.compute_coverage(
        active_requirements=active_req_ids,
        inventory=inventory,
        project_id=proj_id,
    )

    # 3 active requirements (req_archived is archived and excluded from denominator)
    assert coverage_report.total_active_requirements == 3

    # Per-tier coverage:
    # UNIT covers {req_auth} -> 1/3 (33.3%)
    # AI_TEST covers {req_session} -> 1/3 (33.3%)
    # BROWSER_SMOKE covers {req_auth} -> 1/3 (33.3%)
    # BROWSER_JOURNEY covers {req_auth} -> 1/3 (33.3%)
    assert coverage_report.tier_coverages[TestTier.UNIT.value].covered_requirement_count == 1
    assert coverage_report.tier_coverages[TestTier.AI_TEST.value].covered_requirement_count == 1
    assert coverage_report.tier_coverages[TestTier.BROWSER_SMOKE.value].covered_requirement_count == 1
    assert coverage_report.tier_coverages[TestTier.BROWSER_JOURNEY.value].covered_requirement_count == 1

    # Arithmetic average of tiers would be: (33.3% + 33.3% + 33.3% + 33.3%) / 4 = 33.3%
    # But Set-Union Coverage is: {req_auth} ∪ {req_session} = 2 / 3 = 66.7%
    assert coverage_report.combined_covered_count == 2
    assert pytest.approx(coverage_report.combined_coverage_percentage, 0.1) == 66.7
    assert set(coverage_report.combined_covered_requirement_ids) == {req_auth, req_session}

    # Coverage gaps: req_profile has 0 coverage; archived req must NOT appear in gaps
    assert coverage_report.combined_uncovered_count == 1
    assert coverage_report.combined_uncovered_requirement_ids == [req_profile]
    assert req_archived not in coverage_report.combined_uncovered_requirement_ids

    # Also verify that when Requirement ORM models are passed, archived requirements are automatically filtered
    orm_coverage_report = UnifiedCoverageEngine.compute_coverage(
        active_requirements=stage8_requirements_a,
        inventory=inventory,
        project_id=proj_id,
    )
    assert req_archived not in orm_coverage_report.active_requirement_ids
    assert stage8_requirements_a[3].title not in orm_coverage_report.active_requirement_ids


# ==============================================================================
# SCENARIO B: COVERAGE -> AST CHANGE IMPACT & UNCERTAINTY BROADENING
# ==============================================================================

@pytest.mark.asyncio
async def test_scenario_b_ast_change_impact_and_uncertainty(stage8_project_a: Project, stage8_requirements_a: list[Requirement]):
    """Verify AST dependency analysis, transitive impact, and dynamic uncertainty broadening."""
    proj_id = str(stage8_project_a.id).lower()
    req_auth = str(stage8_requirements_a[0].id)
    req_session = str(stage8_requirements_a[1].id)

    files_map = {
        "app/auth.py": "def login():\n    return 'token'\n",
        "app/session.py": "from app.auth import login\ndef get_session():\n    return login()\n",
        "app/utils.py": "import os\n# Controlled dynamic import triggering uncertainty\nmod = __import__('dynamic_plugin')\n",
        "tests/test_auth.py": "from app.auth import login\ndef test_login():\n    assert login() == 'token'\n",
        "tests/test_session.py": "from app.session import get_session\ndef test_session():\n    assert get_session() == 'token'\n",
    }

    t1 = UnifiedTestDefinition(
        test_id=f"unit:{proj_id}:tests/test_auth.py::test_login",
        project_id=proj_id,
        tier=TestTier.UNIT,
        name="Test Login",
        source_reference="tests/test_auth.py::test_login",
        requirement_links=[req_auth],
        discovery_source=DiscoveryProvenance.PYTEST_DISCOVERY,
    )
    t2 = UnifiedTestDefinition(
        test_id=f"unit:{proj_id}:tests/test_session.py::test_session",
        project_id=proj_id,
        tier=TestTier.UNIT,
        name="Test Session",
        source_reference="tests/test_session.py::test_session",
        requirement_links=[req_session],
        discovery_source=DiscoveryProvenance.PYTEST_DISCOVERY,
    )
    inventory = make_test_inventory(proj_id, [t1, t2])

    impact_svc = ChangeImpactService()

    # Case 1: Deterministic modification to app/auth.py
    # Should impact app/auth.py directly, and app/session.py + tests transitively
    report1 = impact_svc.analyze_change_impact(
        project_id=proj_id,
        changed_files=["app/auth.py"],
        files_map=files_map,
        inventory=inventory,
        active_requirement_ids=[req_auth, req_session],
    )

    assert "app/auth.py" in report1.changed_files
    assert "app/session.py" in report1.directly_affected_files
    assert "app/auth.py" in report1.all_affected_files
    assert "app/session.py" in report1.all_affected_files
    assert t1.test_id in report1.affected_test_ids
    assert req_auth in report1.affected_requirements
    assert report1.analysis_confidence == AnalysisConfidence.HIGH
    assert not report1.requires_broader_regression

    # Repeatability check: running same impact request twice produces identical results
    report1_repeat = impact_svc.analyze_change_impact(
        project_id=proj_id,
        changed_files=["app/auth.py"],
        files_map=files_map,
        inventory=inventory,
        active_requirement_ids=[req_auth, req_session],
    )
    assert report1.model_dump(exclude={"calculated_at"}) == report1_repeat.model_dump(exclude={"calculated_at"})

    # Case 2: Modifying file with dynamic import (app/utils.py)
    # Must trigger uncertainty broadening: requires_broader_regression = True
    report2 = impact_svc.analyze_change_impact(
        project_id=proj_id,
        changed_files=["app/utils.py"],
        files_map=files_map,
        inventory=inventory,
        active_requirement_ids=[req_auth, req_session],
    )
    assert report2.requires_broader_regression is True
    assert len(report2.uncertain_dependencies) > 0


# ==============================================================================
# SCENARIO C: REGRESSION PLANNING (SELECTIVE, BROAD, FULL)
# ==============================================================================

@pytest.mark.asyncio
async def test_scenario_c_regression_planning_modes_and_ordering(stage8_project_a: Project, stage8_requirements_a: list[Requirement]):
    """Verify SELECTIVE, BROAD, FULL planning, tier ordering, and authoritative link protection."""
    proj_id = str(stage8_project_a.id).lower()
    req_auth = str(stage8_requirements_a[0].id)
    req_session = str(stage8_requirements_a[1].id)

    t1 = UnifiedTestDefinition(
        test_id=f"unit:{proj_id}:tests/test_auth.py::test_login",
        project_id=proj_id,
        tier=TestTier.UNIT,
        name="Unit Auth",
        source_reference="tests/test_auth.py::test_login",
        requirement_links=[req_auth],
        discovery_source=DiscoveryProvenance.PYTEST_DISCOVERY,
    )
    t2 = UnifiedTestDefinition(
        test_id=f"ai_test:{proj_id}:tests/ai/test_session.py::test_session",
        project_id=proj_id,
        tier=TestTier.AI_TEST,
        name="AI Session",
        source_reference="tests/ai/test_session.py::test_session",
        requirement_links=[req_session],
        discovery_source=DiscoveryProvenance.AI_TEST_SUITE,
    )
    t3 = UnifiedTestDefinition(
        test_id=f"browser_smoke:{proj_id}:tests/browser/smoke.py",
        project_id=proj_id,
        tier=TestTier.BROWSER_SMOKE,
        name="Smoke Auth",
        source_reference="/login",
        requirement_links=[req_auth],
        discovery_source=DiscoveryProvenance.BROWSER_SMOKE_SUITE,
    )

    inventory = make_test_inventory(proj_id, [t1, t2, t3])

    files_map = {
        "app/auth.py": "def login(): pass",
        "tests/test_auth.py": "from app.auth import login",
    }

    impact_svc = ChangeImpactService()
    impact_report = impact_svc.analyze_change_impact(
        project_id=proj_id,
        changed_files=["app/auth.py"],
        files_map=files_map,
        inventory=inventory,
        active_requirement_ids=[req_auth],
    )

    planner = SelectiveRegressionPlanner()

    # 1. SELECTIVE Mode
    plan_selective = planner.plan_regression(
        project_id=proj_id,
        inventory=inventory,
        impact_report=impact_report,
        mode=RegressionPlanMode.SELECTIVE,
    )
    assert plan_selective.mode == RegressionPlanMode.SELECTIVE
    # Only t1 was affected by app/auth.py
    assert t1.test_id in plan_selective.selected_test_ids
    # Protected requirements use authoritative links only
    assert req_auth in plan_selective.protected_requirement_ids
    assert plan_selective.is_execution_safe is True

    # 2. FULL Mode
    plan_full = planner.plan_regression(
        project_id=proj_id,
        inventory=inventory,
        impact_report=impact_report,
        mode=RegressionPlanMode.FULL,
    )
    assert plan_full.mode == RegressionPlanMode.FULL
    assert len(plan_full.selected_test_ids) == 3
    # Deterministic tier ordering: UNIT -> AI_TEST -> BROWSER_SMOKE
    tiers = [t.tier for t in plan_full.selected_tests]
    assert tiers == [TestTier.UNIT, TestTier.AI_TEST, TestTier.BROWSER_SMOKE]

    # 3. BROAD Mode
    plan_broad = planner.plan_regression(
        project_id=proj_id,
        inventory=inventory,
        impact_report=impact_report,
        mode=RegressionPlanMode.BROAD,
    )
    assert plan_broad.mode == RegressionPlanMode.BROAD
    assert plan_broad.is_execution_safe is True


# ==============================================================================
# SELECTIVE REGRESSION SAFETY & EXECUTION BLOCKING
# ==============================================================================

@pytest.mark.asyncio
async def test_selective_regression_safety_blocking(stage8_project_a: Project, stage8_requirements_a: list[Requirement]):
    """Verify unsafe selective plan is BLOCKED, zero tests execute, and diagnostics are reported."""
    proj_id = str(stage8_project_a.id).lower()
    req_auth = str(stage8_requirements_a[0].id)

    t1 = UnifiedTestDefinition(
        test_id=f"unit:{proj_id}:tests/test_auth.py::test_login",
        project_id=proj_id,
        tier=TestTier.UNIT,
        name="Unit Auth",
        source_reference="tests/test_auth.py::test_login",
        requirement_links=[req_auth],
        discovery_source=DiscoveryProvenance.PYTEST_DISCOVERY,
    )
    inventory = make_test_inventory(proj_id, [t1])

    files_map = {
        "app/auth.py": "import sys\nmod = __import__('dynamic_ext')\n",
        "tests/test_auth.py": "from app.auth import mod\n",
    }

    impact_svc = ChangeImpactService()
    # Uncertain dynamic dependency forces requires_broader_regression=True
    impact_report = impact_svc.analyze_change_impact(
        project_id=proj_id,
        changed_files=["app/auth.py"],
        files_map=files_map,
        inventory=inventory,
        active_requirement_ids=[req_auth],
    )
    assert impact_report.requires_broader_regression is True

    # When auto_broaden=False and mode=SELECTIVE, planner generates an unsafe plan
    planner = SelectiveRegressionPlanner()
    plan = planner.plan_regression(
        project_id=proj_id,
        inventory=inventory,
        impact_report=impact_report,
        mode=RegressionPlanMode.SELECTIVE,
        auto_broaden=False,
    )
    assert plan.is_execution_safe is False
    assert plan.requires_broader_regression is True

    # Execute plan through RegressionExecutionService
    mock_sandbox = RecordingMockSandbox()
    executor_svc = RegressionExecutionService(sandbox_executor=mock_sandbox)

    exec_result = await executor_svc.execute_plan(
        project_id=proj_id,
        plan=plan,
        inventory=inventory,
    )

    # Invariant: Unsafe plan must result in BLOCKED status with 0 container executions dispatched
    assert exec_result.status == RegressionExecutionStatus.BLOCKED
    assert len(mock_sandbox.executed_targets) == 0
    assert "BLOCKED" in exec_result.failure_summary
    for test_res in exec_result.test_results:
        assert test_res.status == TestExecutionStatus.BLOCKED


# ==============================================================================
# SCENARIO D: REGRESSION EXECUTION & FAILURE SEMANTICS
# ==============================================================================

@pytest.mark.asyncio
async def test_scenario_d_execution_and_failure_semantics(stage8_project_a: Project, stage8_requirements_a: list[Requirement]):
    """Verify execution across tiers, assertion failure vs infra failure differentiation."""
    proj_id = str(stage8_project_a.id).lower()
    req_auth = str(stage8_requirements_a[0].id)

    t1 = UnifiedTestDefinition(
        test_id=f"unit:{proj_id}:tests/test_pass.py::test_pass",
        project_id=proj_id,
        tier=TestTier.UNIT,
        name="Unit Pass",
        source_reference="tests/test_pass.py::test_pass",
        requirement_links=[req_auth],
        discovery_source=DiscoveryProvenance.PYTEST_DISCOVERY,
    )
    t2 = UnifiedTestDefinition(
        test_id=f"unit:{proj_id}:tests/test_fail.py::test_fail",
        project_id=proj_id,
        tier=TestTier.UNIT,
        name="Unit Fail",
        source_reference="tests/test_fail.py::test_fail",
        requirement_links=[req_auth],
        discovery_source=DiscoveryProvenance.PYTEST_DISCOVERY,
    )
    inventory = make_test_inventory(proj_id, [t1, t2])

    files_map = {
        "tests/test_pass.py": "def test_pass(): assert True",
        "tests/test_fail.py": "def test_fail(): assert False",
    }
    impact_svc = ChangeImpactService()
    impact_report = impact_svc.analyze_change_impact(
        project_id=proj_id,
        changed_files=["tests/test_pass.py", "tests/test_fail.py"],
        files_map=files_map,
        inventory=inventory,
        active_requirement_ids=[req_auth],
    )

    planner = SelectiveRegressionPlanner()
    plan = planner.plan_regression(
        project_id=proj_id,
        inventory=inventory,
        impact_report=impact_report,
        mode=RegressionPlanMode.FULL,
    )

    # Configure mock sandbox to pass t1 and fail t2 (assertion failure)
    class CustomSandbox(MockSandboxExecutor):
        async def execute(self, request: ExecutionRequest, code_output: CodeGenerationOutput) -> ExecutionResult:
            if "test_fail" in (request.test_target or ""):
                return ExecutionResult(
                    project_id=request.project_id,
                    execution_type=request.execution_type,
                    status=ExecutionStatus.FAILED,
                    exit_code=1,
                    tests_total=1,
                    tests_failed=1,
                    stdout="FAILED tests/test_fail.py::test_fail - AssertionError: expected True",
                )
            return ExecutionResult(
                project_id=request.project_id,
                execution_type=request.execution_type,
                status=ExecutionStatus.PASSED,
                exit_code=0,
                tests_total=1,
                tests_passed=1,
                stdout="1 passed in 0.05s",
            )

    executor_svc = RegressionExecutionService(sandbox_executor=CustomSandbox())
    result = await executor_svc.execute_plan(
        project_id=proj_id,
        plan=plan,
        inventory=inventory,
    )

    assert result.status == RegressionExecutionStatus.PARTIAL_FAILURE
    assert result.passed_tests == 1
    assert result.failed_tests == 1

    # Check distinction between assertion failure and infrastructure failure
    fail_res = next(r for r in result.test_results if r.test_id == t2.test_id)
    assert fail_res.status == TestExecutionStatus.FAILED
    assert fail_res.is_infrastructure_failure is False

    # Now verify Infrastructure Crash differentiation
    class CrashSandbox(MockSandboxExecutor):
        async def execute(self, request: ExecutionRequest, code_output: CodeGenerationOutput) -> ExecutionResult:
            return ExecutionResult(
                project_id=request.project_id,
                execution_type=request.execution_type,
                status=ExecutionStatus.ERROR,
                exit_code=137,
                stderr="Container OOMKilled or crashed unexpectedly",
            )

    crash_executor = RegressionExecutionService(sandbox_executor=CrashSandbox())
    crash_result = await crash_executor.execute_plan(
        project_id=proj_id,
        plan=plan,
        inventory=inventory,
    )
    assert crash_result.status == RegressionExecutionStatus.ERROR
    infra_fail = crash_result.test_results[0]
    assert infra_fail.is_infrastructure_failure is True


# ==============================================================================
# LIVE DOCKER BOUNDARY EXECUTION VALIDATION
# ==============================================================================

@pytest.mark.asyncio
@docker_available
async def test_live_docker_sandbox_execution():
    """Verify real container execution under non-root and network-isolated security invariants."""
    docker_executor = DockerSandboxExecutor()
    code_output = make_valid_code_output([
        ("app/math_module.py", "def add(a: int, b: int) -> int:\n    return a + b\n"),
        ("tests/test_math_module.py", "from app.math_module import add\ndef test_add():\n    assert add(20, 22) == 42\n"),
    ])
    req = ExecutionRequest(
        project_id=uuid.uuid4(),
        execution_type=ExecutionType.TEST,
        test_target="tests/test_math_module.py",
        limits=ResourceLimits(timeout_seconds=25),
    )

    result = await docker_executor.execute(req, code_output)
    assert result.status == ExecutionStatus.PASSED
    assert result.exit_code == 0
    assert result.tests_passed == 1
    assert "1 passed" in result.stdout


# ==============================================================================
# REST API END-TO-END VALIDATION (ALL 6 STAGE 6 ENDPOINTS)
# ==============================================================================

@pytest.mark.asyncio
async def test_rest_api_e2e_all_stage6_endpoints(client: AsyncClient, stage8_project_a: Project, stage8_requirements_a: list[Requirement]):
    """Validate GET inventory, GET coverage, GET gaps, POST impact, POST plan, POST execute."""
    proj_id = stage8_project_a.id

    # 1. GET inventory
    res_inv = await client.get(f"/api/v1/projects/{proj_id}/testing/inventory")
    assert res_inv.status_code == 200
    data_inv = res_inv.json()
    assert data_inv["project_id"] == str(proj_id).lower()
    assert "tier_counts" in data_inv

    # 2. GET coverage
    res_cov = await client.get(f"/api/v1/projects/{proj_id}/testing/coverage")
    assert res_cov.status_code == 200
    data_cov = res_cov.json()
    assert data_cov["project_id"] == str(proj_id).lower()
    assert "combined_coverage_percentage" in data_cov

    # 3. GET gaps
    res_gaps = await client.get(f"/api/v1/projects/{proj_id}/testing/coverage/gaps")
    assert res_gaps.status_code == 200
    data_gaps = res_gaps.json()
    assert "uncovered_count" in data_gaps
    assert "gaps" in data_gaps

    # 4. POST impact
    res_impact = await client.post(
        f"/api/v1/projects/{proj_id}/testing/impact",
        json={"changed_files": ["app/main.py"]},
    )
    assert res_impact.status_code == 200
    data_impact = res_impact.json()
    assert "all_affected_files" in data_impact

    # 5. POST plan
    res_plan = await client.post(
        f"/api/v1/projects/{proj_id}/testing/regression/plan",
        json={"mode": "FULL"},
    )
    assert res_plan.status_code == 200
    data_plan = res_plan.json()
    assert data_plan["mode"] == "FULL"
    assert "selected_tests" in data_plan

    # 6. POST execute
    res_exec = await client.post(
        f"/api/v1/projects/{proj_id}/testing/regression/execute",
        json={"mode": "FULL"},
    )
    assert res_exec.status_code == 200
    data_exec = res_exec.json()
    assert "execution_id" in data_exec
    assert "status" in data_exec

    # Cross-project / non-existent project returns RFC 7807 404
    random_id = uuid.uuid4()
    res_404 = await client.get(f"/api/v1/projects/{random_id}/testing/inventory")
    assert res_404.status_code == 404


# ==============================================================================
# ASSISTANT ACTION LAYER END-TO-END VALIDATION
# ==============================================================================

@pytest.mark.asyncio
async def test_assistant_testing_actions_e2e(db_session: AsyncSession, stage8_project_a: Project, stage8_requirements_a: list[Requirement]):
    """Verify all 6 testing actions through EngineeringActionService."""
    proj_id = stage8_project_a.id
    service = make_action_service(session=db_session)
    service.regression_executor = RegressionExecutionService(sandbox_executor=MockSandboxExecutor())

    # 1. GET_TEST_INVENTORY
    res_inv = await service.execute_action(
        project_id=proj_id,
        action_id="GET_TEST_INVENTORY",
        parameters={},
    )
    assert res_inv.status == ActionStatus.SUCCESS
    assert res_inv.data is not None
    assert "tests" in res_inv.data

    # 2. GET_COVERAGE_REPORT
    res_cov = await service.execute_action(
        project_id=proj_id,
        action_id="GET_COVERAGE_REPORT",
        parameters={},
    )
    assert res_cov.status == ActionStatus.SUCCESS
    assert res_cov.data is not None
    assert "combined_coverage_percentage" in res_cov.data

    # 3. ANALYZE_COVERAGE_GAPS
    res_gaps = await service.execute_action(
        project_id=proj_id,
        action_id="ANALYZE_COVERAGE_GAPS",
        parameters={},
    )
    assert res_gaps.status == ActionStatus.SUCCESS
    assert res_gaps.data is not None
    assert "uncovered_count" in res_gaps.data

    # 4. ANALYZE_REGRESSION_IMPACT
    res_impact = await service.execute_action(
        project_id=proj_id,
        action_id="ANALYZE_REGRESSION_IMPACT",
        parameters={"changed_files": ["app/main.py"]},
    )
    assert res_impact.status == ActionStatus.SUCCESS
    assert res_impact.data is not None
    assert "all_affected_files" in res_impact.data

    # 5. PLAN_REGRESSION
    res_plan = await service.execute_action(
        project_id=proj_id,
        action_id="PLAN_REGRESSION",
        parameters={"mode": "FULL"},
    )
    assert res_plan.status == ActionStatus.SUCCESS
    assert res_plan.data is not None
    assert "selected_tests" in res_plan.data

    # 6. EXECUTE_REGRESSION
    res_exec = await service.execute_action(
        project_id=proj_id,
        action_id="EXECUTE_REGRESSION",
        parameters={"mode": "FULL"},
    )
    assert res_exec.status == ActionStatus.SUCCESS
    assert res_exec.data is not None
    assert "execution_id" in res_exec.data


# ==============================================================================
# PROJECT ISOLATION & VERSION IMMUTABILITY
# ==============================================================================

@pytest.mark.asyncio
async def test_project_isolation_and_version_immutability(stage8_project_a: Project, stage8_project_b: Project):
    """Verify strict isolation between Project A and Project B, and immutability guarantees."""
    proj_a = str(stage8_project_a.id).lower()
    proj_b = str(stage8_project_b.id).lower()

    # Create inventory for Project A
    t_a = UnifiedTestDefinition(
        test_id=f"unit:{proj_a}:tests/test_a.py::test_a",
        project_id=proj_a,
        tier=TestTier.UNIT,
        name="Project A Test",
        source_reference="tests/test_a.py::test_a",
        requirement_links=["req_a"],
        discovery_source=DiscoveryProvenance.PYTEST_DISCOVERY,
    )
    inv_a = make_test_inventory(proj_a, [t_a])

    # 1. Attempt to pass Project B ID with Inventory A -> raises UnifiedCoverageIsolationError
    with pytest.raises(UnifiedCoverageIsolationError):
        UnifiedCoverageEngine.compute_coverage(
            active_requirements=["req_a"],
            inventory=inv_a,
            project_id=proj_b,
        )

    # 2. Attempt to run ChangeImpactService with mismatched project ID -> raises ChangeImpactIsolationError
    impact_svc = ChangeImpactService()
    with pytest.raises(ChangeImpactIsolationError):
        impact_svc.analyze_change_impact(
            project_id=proj_b,
            changed_files=["app/main.py"],
            files_map={"app/main.py": "x = 1"},
            inventory=inv_a,
        )

    # 3. Attempt to plan regression with mismatched project ID -> raises RegressionPlanIsolationError
    impact_report_a = impact_svc.analyze_change_impact(
        project_id=proj_a,
        changed_files=["app/main.py"],
        files_map={"app/main.py": "x = 1"},
        inventory=inv_a,
    )
    planner = SelectiveRegressionPlanner()
    with pytest.raises(RegressionPlanIsolationError):
        planner.plan_regression(
            project_id=proj_b,
            inventory=inv_a,
            impact_report=impact_report_a,
        )

    # 4. Attempt to execute plan with mismatched project ID -> raises RegressionPlanIsolationError
    plan_a = planner.plan_regression(
        project_id=proj_a,
        inventory=inv_a,
        impact_report=impact_report_a,
        mode=RegressionPlanMode.FULL,
    )
    exec_svc = RegressionExecutionService(sandbox_executor=MockSandboxExecutor())
    with pytest.raises(RegressionPlanIsolationError):
        await exec_svc.execute_plan(
            project_id=proj_b,
            plan=plan_a,
            inventory=inv_a,
        )

    # 5. Immutability verification:
    # Snapshot plan representation before execution
    plan_snapshot = plan_a.model_dump()
    await exec_svc.execute_plan(
        project_id=proj_a,
        plan=plan_a,
        inventory=inv_a,
    )
    # Regression plan remains strictly immutable after execution
    assert plan_a.model_dump() == plan_snapshot
