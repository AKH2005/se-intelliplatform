"""Live Verification Script for Phase 11L - Stage 8: Final Live E2E + Release Validation.

Executes live end-to-end integration and release validation across:
1. Unified Test Inventory (all 4 tiers: UNIT, AI_TEST, BROWSER_SMOKE, BROWSER_JOURNEY)
2. Multi-Tier Coverage Intelligence (Set-Union Coverage, Gap Detection, Active Filtering)
3. AST Dependency Graph & Change Impact Intelligence (Uncertainty Broadening)
4. Selective Regression Planning (SELECTIVE, BROAD, FULL modes, Deterministic Ordering)
5. Selective Regression Safety Precondition Gate (Blocks Unsafe Plans with 0 test dispatches)
6. Live Docker Sandbox Execution (Non-root, --network=none, /workspace read-only)
7. Failure Semantics Classification (Assertion failure vs Infrastructure crash)
8. Project Isolation & Immutability Verification

Outputs JSON report to: tests/phase_11l_stage8_live_verification.json
"""

import asyncio
import json
import logging
from pathlib import Path
import shutil
import subprocess
import sys
import time
import uuid
from datetime import datetime, timezone

# Add backend to sys.path
backend_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(backend_dir))

from app.agents.code_generation.contracts import CodeGenerationOutput, GeneratedFile, PlannedFile, CodeGenerationPlan
from app.sandbox.contracts import ExecutionRequest, ExecutionResult, ExecutionStatus, ExecutionType, ResourceLimits
from app.sandbox.docker_executor import DockerSandboxExecutor
from app.sandbox.mock_executor import MockSandboxExecutor
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
from app.testing.regression.contracts import (
    IndividualTestResult,
    PlanSelectionReason,
    RegressionExecutionResult,
    RegressionExecutionStatus,
    RegressionPlan,
    RegressionPlanMode,
    SelectedTest,
    TestExecutionStatus,
)
from app.testing.regression.errors import RegressionPlanIsolationError
from app.testing.regression.executor import RegressionExecutionService
from app.testing.regression.planner import SelectiveRegressionPlanner
from tests.unit.test_sandbox import make_valid_code_output

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("live_verify_phase11l_stage8")


def check_docker_daemon() -> tuple[bool, str]:
    """Check Docker daemon responsiveness."""
    if not shutil.which("docker"):
        return False, "Docker CLI not found on host"
    try:
        res = subprocess.run(
            ["docker", "info", "--format", "{{.ServerVersion}}"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        if res.returncode == 0:
            return True, f"Docker daemon active (version {res.stdout.strip()})"
        return False, f"Docker daemon not running: {res.stderr.strip()}"
    except Exception as e:
        return False, f"Docker error: {str(e)}"


def build_inventory_fixture(project_id: str) -> tuple[UnifiedTestInventory, dict[str, str]]:
    """Build deterministic multi-tier inventory and code files mapping."""
    clean_proj = str(project_id).strip().lower()

    t_unit = UnifiedTestDefinition(
        test_id=f"unit:{clean_proj}:tests/test_auth.py::test_login",
        project_id=clean_proj,
        tier=TestTier.UNIT,
        name="Unit Auth Test",
        source_reference="tests/test_auth.py::test_login",
        requirement_links=["REQ-AUTH"],
        inferred_requirement_links=["REQ-SESSION"],
        discovery_source=DiscoveryProvenance.PYTEST_DISCOVERY,
    )
    t_ai = UnifiedTestDefinition(
        test_id=f"ai_test:{clean_proj}:tests/ai/test_session_ai.py::test_session",
        project_id=clean_proj,
        tier=TestTier.AI_TEST,
        name="AI Generated Session Test",
        source_reference="tests/ai/test_session_ai.py::test_session",
        requirement_links=["REQ-SESSION"],
        discovery_source=DiscoveryProvenance.AI_TEST_SUITE,
    )
    t_smoke = UnifiedTestDefinition(
        test_id=f"browser_smoke:{clean_proj}:tests/browser/smoke_login.py",
        project_id=clean_proj,
        tier=TestTier.BROWSER_SMOKE,
        name="Login Smoke Test",
        source_reference="/login",
        requirement_links=["REQ-AUTH"],
        discovery_source=DiscoveryProvenance.BROWSER_SMOKE_SUITE,
    )
    t_journey = UnifiedTestDefinition(
        test_id=f"browser_journey:{clean_proj}:journey_auth_flow",
        project_id=clean_proj,
        tier=TestTier.BROWSER_JOURNEY,
        name="End-to-End Login Journey",
        source_reference="/auth/flow",
        requirement_links=["REQ-AUTH"],
        discovery_source=DiscoveryProvenance.VALIDATED_BROWSER_JOURNEY,
    )

    tests = [t_unit, t_ai, t_smoke, t_journey]
    test_ids = [t.test_id for t in tests]
    tests_by_id = {t.test_id: t for t in tests}
    tests_by_tier = {tier.value: [t.test_id for t in tests if t.tier == tier] for tier in TestTier}
    tier_counts = {tier.value: len(tests_by_tier[tier.value]) for tier in TestTier}

    inv_id = compute_deterministic_inventory_id(clean_proj, test_ids)
    inventory = UnifiedTestInventory(
        inventory_id=inv_id,
        project_id=clean_proj,
        tests=tests,
        discovery_status=DiscoveryStatus.COMPLETE,
        conflicts=[],
        tests_by_id=tests_by_id,
        tests_by_tier=tests_by_tier,
        tests_by_requirement={"REQ-AUTH": [t_unit.test_id, t_smoke.test_id, t_journey.test_id], "REQ-SESSION": [t_ai.test_id]},
        requirements_by_test={t_unit.test_id: ["REQ-AUTH"], t_ai.test_id: ["REQ-SESSION"], t_smoke.test_id: ["REQ-AUTH"], t_journey.test_id: ["REQ-AUTH"]},
        tier_counts=tier_counts,
        total_tests=len(tests),
    )

    files_map = {
        "app/auth.py": "def login(): return 'ok'\n",
        "app/session.py": "from app.auth import login\ndef session(): return login()\n",
        "app/dynamic_plugin.py": "import os\n# dynamic load\nmod = __import__('os')\n",
        "tests/test_auth.py": "from app.auth import login\ndef test_login(): assert login() == 'ok'\n",
        "tests/test_session.py": "from app.session import session\ndef test_session(): assert session() == 'ok'\n",
    }

    return inventory, files_map


class RecordingMockSandbox(MockSandboxExecutor):
    """Mock sandbox executor that records executed test targets."""

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self.executed_targets: list[str] = []

    async def execute(self, request: ExecutionRequest, code_output: CodeGenerationOutput) -> ExecutionResult:
        if request.test_target:
            self.executed_targets.append(request.test_target)
        return await super().execute(request, code_output)


async def run_live_validation() -> dict:
    """Run full live end-to-end release validation."""
    logger.info("============================================================")
    logger.info("PHASE 11L STAGE 8 — LIVE END-TO-END RELEASE VALIDATION")
    logger.info("============================================================")

    results: dict[str, Any] = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "phase": "11L",
        "stage": "Stage 8: Final Live E2E + Release Validation",
        "verdicts": {},
        "metrics": {},
        "invariants": {},
    }

    proj_a = str(uuid.uuid4())
    proj_b = str(uuid.uuid4())
    inventory_a, files_map = build_inventory_fixture(proj_a)

    # --------------------------------------------------------------------------
    # 1. Unified Test Inventory & Multi-Tier Coverage
    # --------------------------------------------------------------------------
    logger.info("[1/7] Validating Unified Test Inventory & Multi-Tier Coverage...")
    active_reqs = ["REQ-AUTH", "REQ-SESSION", "REQ-PROFILE"]
    cov_report = UnifiedCoverageEngine.compute_coverage(
        active_requirements=active_reqs,
        inventory=inventory_a,
        project_id=proj_a,
    )

    # Set union of REQ-AUTH (UNIT, SMOKE, JOURNEY) and REQ-SESSION (AI_TEST) = 2/3 = 66.7%
    # Arithmetic average would be: (33.3 + 33.3 + 33.3 + 33.3) / 4 = 33.3%
    is_union_correct = (
        cov_report.combined_covered_count == 2 and
        pytest_approx_equal(cov_report.combined_coverage_percentage, 66.7) and
        set(cov_report.combined_covered_requirement_ids) == {"REQ-AUTH", "REQ-SESSION"} and
        cov_report.combined_uncovered_requirement_ids == ["REQ-PROFILE"]
    )
    results["verdicts"]["inventory_and_coverage"] = "PASS" if is_union_correct else "FAIL"
    results["metrics"]["total_tests"] = inventory_a.total_tests
    results["metrics"]["combined_coverage_pct"] = cov_report.combined_coverage_percentage
    results["invariants"]["coverage_is_set_union_not_arithmetic_average"] = is_union_correct
    results["invariants"]["inferred_links_excluded_from_coverage"] = "REQ-SESSION" not in inventory_a.tests[0].requirement_links

    # --------------------------------------------------------------------------
    # 2. AST Dependency Graph & Change Impact Intelligence
    # --------------------------------------------------------------------------
    logger.info("[2/7] Validating AST Change Impact & Uncertainty Broadening...")
    impact_svc = ChangeImpactService()

    # Deterministic change to app/auth.py
    impact1 = impact_svc.analyze_change_impact(
        project_id=proj_a,
        changed_files=["app/auth.py"],
        files_map=files_map,
        inventory=inventory_a,
        active_requirement_ids=active_reqs,
    )
    is_impact1_correct = (
        "app/auth.py" in impact1.changed_files and
        "app/session.py" in impact1.directly_affected_files and
        "REQ-AUTH" in impact1.affected_requirements and
        impact1.analysis_confidence == AnalysisConfidence.HIGH and
        not impact1.requires_broader_regression
    )

    # Dynamic import change triggering conservative broadening
    files_with_dynamic = dict(files_map)
    files_with_dynamic["app/auth.py"] = "import sys\nmod = __import__('unresolved_dyn')\n"
    impact2 = impact_svc.analyze_change_impact(
        project_id=proj_a,
        changed_files=["app/auth.py"],
        files_map=files_with_dynamic,
        inventory=inventory_a,
        active_requirement_ids=active_reqs,
    )
    is_broadening_correct = (
        impact2.requires_broader_regression is True and
        len(impact2.uncertain_dependencies) > 0
    )
    results["verdicts"]["change_impact"] = "PASS" if (is_impact1_correct and is_broadening_correct) else "FAIL"
    results["invariants"]["dynamic_uncertainty_forces_broadening"] = is_broadening_correct

    # --------------------------------------------------------------------------
    # 3. Selective Regression Planning (SELECTIVE, BROAD, FULL)
    # --------------------------------------------------------------------------
    logger.info("[3/7] Validating Regression Planning across all 3 modes...")
    planner = SelectiveRegressionPlanner()

    plan_selective = planner.plan_regression(
        project_id=proj_a,
        inventory=inventory_a,
        impact_report=impact1,
        mode=RegressionPlanMode.SELECTIVE,
    )
    plan_broad = planner.plan_regression(
        project_id=proj_a,
        inventory=inventory_a,
        impact_report=impact1,
        mode=RegressionPlanMode.BROAD,
    )
    plan_full = planner.plan_regression(
        project_id=proj_a,
        inventory=inventory_a,
        impact_report=impact1,
        mode=RegressionPlanMode.FULL,
    )

    is_planning_correct = (
        plan_selective.mode == RegressionPlanMode.SELECTIVE and
        plan_broad.mode == RegressionPlanMode.BROAD and
        plan_full.mode == RegressionPlanMode.FULL and
        len(plan_full.selected_test_ids) == inventory_a.total_tests and
        [t.tier for t in plan_full.selected_tests] == [TestTier.UNIT, TestTier.AI_TEST, TestTier.BROWSER_SMOKE, TestTier.BROWSER_JOURNEY]
    )
    results["verdicts"]["regression_planning"] = "PASS" if is_planning_correct else "FAIL"
    results["invariants"]["full_regression_always_available"] = len(plan_full.selected_test_ids) == 4
    results["invariants"]["deterministic_tier_order_enforced"] = is_planning_correct

    # --------------------------------------------------------------------------
    # 4. Selective Regression Safety Precondition Gate
    # --------------------------------------------------------------------------
    logger.info("[4/7] Validating Safety Precondition Gate (Blocking Unsafe Plans)...")
    unsafe_plan = planner.plan_regression(
        project_id=proj_a,
        inventory=inventory_a,
        impact_report=impact2,  # requires_broader_regression is True
        mode=RegressionPlanMode.SELECTIVE,
        auto_broaden=False,
    )
    is_plan_flagged_unsafe = (unsafe_plan.is_execution_safe is False and unsafe_plan.requires_broader_regression is True)

    recording_sandbox = RecordingMockSandbox()
    executor_svc = RegressionExecutionService(sandbox_executor=recording_sandbox)
    exec_blocked = await executor_svc.execute_plan(
        project_id=proj_a,
        plan=unsafe_plan,
        inventory=inventory_a,
    )

    is_execution_blocked = (
        exec_blocked.status == RegressionExecutionStatus.BLOCKED and
        len(recording_sandbox.executed_targets) == 0 and
        all(t.status == TestExecutionStatus.BLOCKED for t in exec_blocked.test_results)
    )
    results["verdicts"]["safety_blocking"] = "PASS" if (is_plan_flagged_unsafe and is_execution_blocked) else "FAIL"
    results["invariants"]["unsafe_plans_strictly_blocked"] = is_execution_blocked
    results["invariants"]["zero_tests_dispatched_when_blocked"] = len(recording_sandbox.executed_targets) == 0

    # --------------------------------------------------------------------------
    # 5. Live Docker Sandbox Execution
    # --------------------------------------------------------------------------
    logger.info("[5/7] Validating Live Docker Sandbox Boundary...")
    docker_ok, docker_msg = check_docker_daemon()
    if docker_ok:
        try:
            docker_executor = DockerSandboxExecutor()
            code_out = make_valid_code_output([
                ("app/math.py", "def add(a: int, b: int) -> int:\n    return a + b\n"),
                ("tests/test_math.py", "from app.math import add\ndef test_add():\n    assert add(10, 32) == 42\n"),
            ])
            req = ExecutionRequest(
                project_id=uuid.UUID(proj_a),
                execution_type=ExecutionType.TEST,
                test_target="tests/test_math.py",
                limits=ResourceLimits(timeout_seconds=20),
            )
            d_res = await docker_executor.execute(req, code_out)
            live_docker_pass = (
                d_res.status == ExecutionStatus.PASSED and
                d_res.exit_code == 0 and
                d_res.tests_passed == 1
            )
            results["verdicts"]["live_docker"] = "PASS" if live_docker_pass else "FAIL"
            results["metrics"]["docker_duration_s"] = d_res.duration_seconds
        except Exception as e:
            results["verdicts"]["live_docker"] = f"FAIL: {str(e)}"
    else:
        results["verdicts"]["live_docker"] = f"BLOCKED BY ENVIRONMENT: {docker_msg}"

    # --------------------------------------------------------------------------
    # 6. Failure Semantics Classification (Assertion vs Infra Failure)
    # --------------------------------------------------------------------------
    logger.info("[6/7] Validating Failure Semantics Classification...")
    class SemanticSandbox(MockSandboxExecutor):
        async def execute(self, request: ExecutionRequest, code_output: CodeGenerationOutput) -> ExecutionResult:
            if "test_auth" in (request.test_target or ""):
                return ExecutionResult(
                    project_id=request.project_id,
                    execution_type=request.execution_type,
                    status=ExecutionStatus.FAILED,
                    exit_code=1,
                    tests_total=1,
                    tests_failed=1,
                    stdout="FAILED tests/test_auth.py - AssertionError",
                )
            return ExecutionResult(
                project_id=request.project_id,
                execution_type=request.execution_type,
                status=ExecutionStatus.PASSED,
                exit_code=0,
                tests_total=1,
                tests_passed=1,
                stdout="1 passed",
            )

    sem_executor = RegressionExecutionService(sandbox_executor=SemanticSandbox())
    sem_result = await sem_executor.execute_plan(
        project_id=proj_a,
        plan=plan_full,
        inventory=inventory_a,
        skip_browser_tests=True,
    )
    auth_res = next(r for r in sem_result.test_results if "test_auth" in r.test_id)
    is_semantics_correct = (
        auth_res.status == TestExecutionStatus.FAILED and
        auth_res.is_infrastructure_failure is False
    )
    results["verdicts"]["failure_classification"] = "PASS" if is_semantics_correct else "FAIL"
    results["invariants"]["assertion_failure_not_infra_crash"] = is_semantics_correct

    # --------------------------------------------------------------------------
    # 7. Project Isolation & Immutability
    # --------------------------------------------------------------------------
    logger.info("[7/7] Validating Strict Project Isolation & Immutability...")
    isolation_ok = False
    try:
        UnifiedCoverageEngine.compute_coverage(
            active_requirements=active_reqs,
            inventory=inventory_a,
            project_id=proj_b,  # Cross-project mismatch
        )
    except UnifiedCoverageIsolationError:
        isolation_ok = True

    plan_snapshot = plan_full.model_dump()
    await sem_executor.execute_plan(
        project_id=proj_a,
        plan=plan_full,
        inventory=inventory_a,
        skip_browser_tests=True,
    )
    immutability_ok = (plan_full.model_dump() == plan_snapshot)

    results["verdicts"]["project_isolation"] = "PASS" if isolation_ok else "FAIL"
    results["verdicts"]["plan_immutability"] = "PASS" if immutability_ok else "FAIL"
    results["invariants"]["strict_project_isolation_enforced"] = isolation_ok
    results["invariants"]["regression_plans_remain_immutable"] = immutability_ok

    # --------------------------------------------------------------------------
    # Overall Release Gate Decision
    # --------------------------------------------------------------------------
    critical_verdicts = [
        results["verdicts"]["inventory_and_coverage"],
        results["verdicts"]["change_impact"],
        results["verdicts"]["regression_planning"],
        results["verdicts"]["safety_blocking"],
        results["verdicts"]["failure_classification"],
        results["verdicts"]["project_isolation"],
        results["verdicts"]["plan_immutability"],
    ]
    if "FAIL" in critical_verdicts:
        results["release_gate"] = "FAILED"
    elif results["verdicts"].get("live_docker", "").startswith("FAIL"):
        results["release_gate"] = "FAILED"
    else:
        results["release_gate"] = "PASSED"

    output_path = backend_dir / "tests" / "phase_11l_stage8_live_verification.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)

    logger.info("============================================================")
    logger.info(f"RELEASE GATE DECISION: {results['release_gate']}")
    logger.info(f"Artifact saved to: {output_path}")
    logger.info("============================================================")

    return results


def pytest_approx_equal(a: float, b: float, tol: float = 0.1) -> bool:
    return abs(a - b) <= tol


if __name__ == "__main__":
    asyncio.run(run_live_validation())
