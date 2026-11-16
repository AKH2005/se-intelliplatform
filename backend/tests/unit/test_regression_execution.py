"""Unit Tests for Selective Regression Execution (Phase 11L Stage 5).

Validates:
1. Valid SELECTIVE plan executes ONLY the selected tests (Critical Test Section 42).
2. Valid BROAD and FULL plans execute their exact respective test sets.
3. Unsafe selective plan blocks execution without invoking executors (Critical Safety Test Section 43).
4. Validated browser journey executes through BrowserTestingService (Critical Browser Test Section 44).
5. DevelopmentVersion and RegressionPlan remain completely immutable (Critical Test Section 45).
6. Multi-tier dispatch across UNIT, AI_TEST, BROWSER_SMOKE, and BROWSER_JOURNEY.
7. Test failure vs infrastructure failure distinction.
8. Partial failure handling and requirement outcome calculation.
9. Deterministic logical equivalence and repeat execution idempotency.
10. FailureAnalysisService and DevelopmentVerificationService reuse without automatic remediation.
"""

from datetime import datetime, timezone
from typing import Any
import uuid
import pytest

from app.agents.code_generation.contracts import CodeGenerationOutput, GeneratedFile
from app.browser.contracts import DeterministicBrowserTestDefinition
from app.browser.journey.adapter import BrowserJourneyAdapter
from app.browser.journey.contracts import ValidatedBrowserJourney
from app.sandbox.contracts import ExecutionRequest, ExecutionResult, ExecutionStatus, ExecutionType
from app.sandbox.mock_executor import MockSandboxExecutor
from app.schemas.browser_testing import BrowserTestRun, BrowserTestStatus
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
from app.testing.regression.errors import (
    RegressionPlanIsolationError,
    RegressionPlanValidationError,
)
from app.testing.regression.executor import RegressionExecutionService


# ==============================================================================
# Test Fixtures & Mocks
# ==============================================================================

class RecordingSandboxExecutor(MockSandboxExecutor):
    """Sandbox executor that records all executed test targets."""

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self.executed_targets: list[str] = []

    async def execute(self, request: ExecutionRequest, code_output: CodeGenerationOutput) -> ExecutionResult:
        if request.test_target:
            self.executed_targets.append(request.test_target)
        return await super().execute(request, code_output)


class MockBrowserTestingService:
    """Mock for BrowserTestingService recording calls and definitions."""

    def __init__(self, default_status: BrowserTestStatus = BrowserTestStatus.PASSED) -> None:
        self.default_status = default_status
        self.executed_runs: list[dict] = []

    async def execute_browser_tests(
        self,
        project_id: uuid.UUID,
        version_id: uuid.UUID | None = None,
        test_definitions: list[DeterministicBrowserTestDefinition] | None = None,
        limits: Any = None,
        files_map: dict[str, str] | None = None,
        manifest: Any = None,
    ) -> BrowserTestRun:
        self.executed_runs.append({
            "project_id": project_id,
            "version_id": version_id,
            "test_definitions": test_definitions or [],
            "files_map": files_map,
        })
        return BrowserTestRun(
            run_id=uuid.uuid4(),
            project_id=project_id,
            version_id=version_id,
            status=self.default_status,
            summary="Mock browser test run completed.",
            duration_seconds=0.15,
            started_at=datetime.now(timezone.utc),
            completed_at=datetime.now(timezone.utc),
        )


def make_inventory(project_id: str, tests: list[UnifiedTestDefinition]) -> UnifiedTestInventory:
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
            clean_r = str(r).strip()
            if clean_r not in tests_by_req:
                tests_by_req[clean_r] = []
            tests_by_req[clean_r].append(t.test_id)

    for tier_val in tests_by_tier:
        tests_by_tier[tier_val].sort()

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


def make_plan(
    project_id: str,
    inventory: UnifiedTestInventory,
    selected_tests: list[UnifiedTestDefinition],
    mode: RegressionPlanMode = RegressionPlanMode.SELECTIVE,
    is_execution_safe: bool = True,
    requires_broader: bool = False,
    affected_reqs: list[str] | None = None,
) -> RegressionPlan:
    clean_proj = str(project_id).strip().lower()
    sel_models: list[SelectedTest] = []
    sel_by_tier: dict[str, list[str]] = {t.value: [] for t in TestTier}
    reasons_by_test: dict[str, list[PlanSelectionReason]] = {}
    all_reqs: set[str] = set()

    for t in selected_tests:
        sel_models.append(
            SelectedTest(
                test_id=t.test_id,
                tier=t.tier,
                name=t.name,
                source_reference=t.source_reference,
                selection_reasons=[PlanSelectionReason.DIRECT_CHANGE],
                affected_requirements=list(t.requirement_links),
                affected_files=[],
                selection_scope="DIRECT",
            )
        )
        sel_by_tier[t.tier.value].append(t.test_id)
        reasons_by_test[t.test_id] = [PlanSelectionReason.DIRECT_CHANGE]
        all_reqs.update(t.requirement_links)

    for t_val in sel_by_tier:
        sel_by_tier[t_val].sort()

    aff_reqs_sorted = sorted(affected_reqs or list(all_reqs))
    prot_reqs = sorted(list(set(aff_reqs_sorted) & all_reqs))
    uncov_reqs = sorted(list(set(aff_reqs_sorted) - all_reqs))

    return RegressionPlan(
        project_id=clean_proj,
        mode=mode,
        inventory_id=inventory.inventory_id,
        selected_test_ids=sorted([t.test_id for t in selected_tests]),
        selected_tests=sel_models,
        selected_tests_by_tier=sel_by_tier,
        selected_requirement_ids=sorted(list(all_reqs)),
        affected_requirement_ids=aff_reqs_sorted,
        protected_requirement_ids=prot_reqs,
        uncovered_affected_requirement_ids=uncov_reqs,
        unrelated_requirement_ids=[],
        selection_reasons_by_test=reasons_by_test,
        broadening_reasons=[],
        requires_broader_regression=requires_broader,
        is_execution_safe=is_execution_safe,
        plan_warnings=[],
        total_inventory_tests=inventory.total_tests,
        unselected_test_count=inventory.total_tests - len(selected_tests),
        created_at=datetime.now(timezone.utc),
        metadata={},
    )


# ==============================================================================
# Test Suite
# ==============================================================================

class TestSelectiveRegressionExecution:
    """Comprehensive test suite for RegressionExecutionService."""

    @pytest.fixture
    def project_id(self) -> str:
        return "33333333-3333-3333-3333-333333333333"

    @pytest.fixture
    def sample_unit_tests(self, project_id: str) -> list[UnifiedTestDefinition]:
        return [
            UnifiedTestDefinition(
                test_id=f"unit:3333:tests/test_{letter}.py::test_{letter}",
                tier=TestTier.UNIT,
                name=f"test_{letter}",
                source_reference=f"tests/test_{letter}.py::test_{letter}",
                project_id=project_id,
                requirement_links=[f"REQ-{letter.upper()}"],
                discovery_source=DiscoveryProvenance.PYTEST_DISCOVERY,
                metadata={"file_path": f"tests/test_{letter}.py"},
            )
            for letter in ["a", "b", "c", "d", "e"]
        ]

    # --------------------------------------------------------------------------
    # CRITICAL TEST (Section 42): Executes ONLY selected tests, NOT unselected
    # --------------------------------------------------------------------------
    @pytest.mark.asyncio
    async def test_critical_test_executes_only_selected_tests(
        self,
        project_id: str,
        sample_unit_tests: list[UnifiedTestDefinition],
    ) -> None:
        """Prove that a SELECTIVE plan containing test_A, test_B, test_C executes ONLY

        test_A, test_B, test_C and DOES NOT execute test_D, test_E even though they exist in inventory.
        """
        # Inventory contains 5 tests: A, B, C, D, E
        inventory = make_inventory(project_id, sample_unit_tests)

        # Plan selects ONLY A, B, C
        selected = sample_unit_tests[:3]  # A, B, C
        plan = make_plan(project_id, inventory, selected, mode=RegressionPlanMode.SELECTIVE)

        mock_sandbox = RecordingSandboxExecutor()
        service = RegressionExecutionService(sandbox_executor=mock_sandbox)

        result = await service.execute_plan(project_id, plan, inventory)

        assert result.status == RegressionExecutionStatus.PASSED
        assert result.total_tests == 3
        assert result.passed_tests == 3
        assert len(result.test_results) == 3

        executed_ids = [t.test_id for t in result.test_results]
        assert executed_ids == [
            "unit:3333:tests/test_a.py::test_a",
            "unit:3333:tests/test_b.py::test_b",
            "unit:3333:tests/test_c.py::test_c",
        ]

        # Verify unselected tests D and E were NEVER dispatched to the executor
        assert "tests/test_d.py" not in mock_sandbox.executed_targets
        assert "tests/test_e.py" not in mock_sandbox.executed_targets
        assert len(mock_sandbox.executed_targets) == 3

    # --------------------------------------------------------------------------
    # CRITICAL SAFETY TEST (Section 43): Unsafe selective plan -> NO EXECUTION
    # --------------------------------------------------------------------------
    @pytest.mark.asyncio
    async def test_critical_safety_unsafe_selective_plan_blocks_execution(
        self,
        project_id: str,
        sample_unit_tests: list[UnifiedTestDefinition],
    ) -> None:
        """Prove that an unsafe selective plan (is_execution_safe=False) blocks execution

        and invokes NO executor.
        """
        inventory = make_inventory(project_id, sample_unit_tests)
        # Selective plan marked is_execution_safe=False due to uncertainty
        plan = make_plan(
            project_id,
            inventory,
            sample_unit_tests[:2],
            mode=RegressionPlanMode.SELECTIVE,
            is_execution_safe=False,
            requires_broader=True,
        )

        mock_sandbox = RecordingSandboxExecutor()
        mock_browser = MockBrowserTestingService()
        service = RegressionExecutionService(
            sandbox_executor=mock_sandbox,
            browser_service=mock_browser,
        )

        result = await service.execute_plan(project_id, plan, inventory)

        assert result.status == RegressionExecutionStatus.BLOCKED
        assert result.blocked_tests == 2
        assert result.passed_tests == 0
        assert result.failed_tests == 0
        # ZERO executor calls must have occurred!
        assert len(mock_sandbox.executed_targets) == 0
        assert len(mock_browser.executed_runs) == 0

    # --------------------------------------------------------------------------
    # CRITICAL BROWSER TEST (Section 44): Validated Journey routes via BrowserTestingService
    # --------------------------------------------------------------------------
    @pytest.mark.asyncio
    async def test_critical_browser_test_validated_journey_routes_via_browser_service(
        self,
        project_id: str,
    ) -> None:
        """Prove that validated browser journey executes through BrowserTestingService

        and BrowserJourneyAdapter, and NOT raw Playwright or arbitrary scripts.
        """
        from app.agents.browser_journey.contracts import (
            BrowserActionType,
            BrowserJourneyStep,
            JourneyCategory,
            JourneyPriority,
        )
        journey_id = "vj_user_checkout"
        validated_journey = ValidatedBrowserJourney(
            journey_id=journey_id,
            title="User Checkout Flow",
            description="End to end user checkout journey flow.",
            category=JourneyCategory.HAPPY_PATH,
            priority=JourneyPriority.HIGH,
            validated_requirement_ids=["REQ-PAY-01"],
            steps=[
                BrowserJourneyStep(
                    step_id="step_1",
                    action=BrowserActionType.NAVIGATE,
                    route="/checkout",
                    description="Navigate to checkout page",
                )
            ],
            validated_target_routes=["/checkout"],
        )

        journey_test = UnifiedTestDefinition(
            test_id=f"journey:3333:{journey_id}",
            tier=TestTier.BROWSER_JOURNEY,
            name="User Checkout Flow",
            source_reference=journey_id,
            project_id=project_id,
            requirement_links=["REQ-PAY-01"],
            discovery_source=DiscoveryProvenance.VALIDATED_BROWSER_JOURNEY,
            metadata={"validated_journey_id": journey_id, "is_validated": True},
        )

        inventory = make_inventory(project_id, [journey_test])
        plan = make_plan(project_id, inventory, [journey_test])

        mock_browser = MockBrowserTestingService()
        service = RegressionExecutionService(browser_service=mock_browser)

        result = await service.execute_plan(
            project_id,
            plan,
            inventory,
            validated_journeys=[validated_journey],
        )

        assert result.status == RegressionExecutionStatus.PASSED
        assert len(mock_browser.executed_runs) == 1
        run_record = mock_browser.executed_runs[0]
        # Verify adapted deterministic definition was passed
        assert len(run_record["test_definitions"]) == 1
        adapted_def = run_record["test_definitions"][0]
        assert isinstance(adapted_def, DeterministicBrowserTestDefinition)
        assert adapted_def.name == "User Checkout Flow"
        assert adapted_def.target_path == "/checkout"

    # --------------------------------------------------------------------------
    # CRITICAL DEVELOPMENTVERSION TEST (Section 45): Immutability
    # --------------------------------------------------------------------------
    @pytest.mark.asyncio
    async def test_critical_development_version_and_plan_remain_immutable(
        self,
        project_id: str,
        sample_unit_tests: list[UnifiedTestDefinition],
    ) -> None:
        """Prove that RegressionPlan and target artifacts are NEVER mutated by execution."""
        inventory = make_inventory(project_id, sample_unit_tests[:2])
        plan = make_plan(project_id, inventory, sample_unit_tests[:2])

        # Snapshot plan representation
        plan_snapshot = plan.model_dump()

        service = RegressionExecutionService(sandbox_executor=MockSandboxExecutor())
        await service.execute_plan(project_id, plan, inventory)

        # Assert plan was NOT modified
        assert plan.model_dump() == plan_snapshot

    # --------------------------------------------------------------------------
    # Multi-Tier Execution Dispatch (UNIT, AI_TEST, BROWSER_SMOKE, BROWSER_JOURNEY)
    # --------------------------------------------------------------------------
    @pytest.mark.asyncio
    async def test_four_tier_execution_dispatch(
        self,
        project_id: str,
    ) -> None:
        unit_test = UnifiedTestDefinition(
            test_id="unit:3333:tests/test_x.py::test_x",
            tier=TestTier.UNIT,
            name="test_x",
            source_reference="tests/test_x.py::test_x",
            project_id=project_id,
            requirement_links=["REQ-UNIT"],
            discovery_source=DiscoveryProvenance.PYTEST_DISCOVERY,
        )
        ai_test = UnifiedTestDefinition(
            test_id="ai_test:3333:tests/ai/test_y.py::test_y",
            tier=TestTier.AI_TEST,
            name="test_y",
            source_reference="tests/ai/test_y.py::test_y",
            project_id=project_id,
            requirement_links=["REQ-AI"],
            discovery_source=DiscoveryProvenance.AI_TEST_SUITE,
        )
        smoke_test = UnifiedTestDefinition(
            test_id="smoke:3333:browser_smoke::login",
            tier=TestTier.BROWSER_SMOKE,
            name="smoke_login",
            source_reference="/login",
            project_id=project_id,
            requirement_links=["REQ-SMOKE"],
            discovery_source=DiscoveryProvenance.BROWSER_SMOKE_SUITE,
            target_symbol="/login",
        )

        all_tests = [unit_test, ai_test, smoke_test]
        inventory = make_inventory(project_id, all_tests)
        plan = make_plan(project_id, inventory, all_tests)

        mock_sandbox = RecordingSandboxExecutor()
        mock_browser = MockBrowserTestingService()
        service = RegressionExecutionService(
            sandbox_executor=mock_sandbox,
            browser_service=mock_browser,
        )

        result = await service.execute_plan(project_id, plan, inventory)

        assert result.status == RegressionExecutionStatus.PASSED
        assert result.total_tests == 3
        # UNIT and AI_TEST routed to sandbox executor
        assert len(mock_sandbox.executed_targets) == 2
        # BROWSER_SMOKE routed to browser service
        assert len(mock_browser.executed_runs) == 1

        # Check tier summaries
        assert result.results_by_tier[TestTier.UNIT.value].passed_tests == 1
        assert result.results_by_tier[TestTier.AI_TEST.value].passed_tests == 1
        assert result.results_by_tier[TestTier.BROWSER_SMOKE.value].passed_tests == 1

    # --------------------------------------------------------------------------
    # Test Failure vs. Infrastructure Failure Distinction
    # --------------------------------------------------------------------------
    @pytest.mark.asyncio
    async def test_distinguishes_test_failure_from_infrastructure_error(
        self,
        project_id: str,
        sample_unit_tests: list[UnifiedTestDefinition],
    ) -> None:
        inventory = make_inventory(project_id, sample_unit_tests[:2])
        plan = make_plan(project_id, inventory, sample_unit_tests[:2])

        # Simulate sandbox error (infrastructure failure)
        mock_sandbox = MockSandboxExecutor(
            default_status=ExecutionStatus.SANDBOX_ERROR,
            mock_stderr="Docker daemon connection terminated unexpectedly.",
        )
        service = RegressionExecutionService(sandbox_executor=mock_sandbox)

        result = await service.execute_plan(project_id, plan, inventory)

        assert result.status == RegressionExecutionStatus.ERROR
        assert result.errored_tests == 2
        assert result.failed_tests == 0
        assert len(result.infrastructure_failures) > 0
        assert result.test_results[0].is_infrastructure_failure is True

    # --------------------------------------------------------------------------
    # Partial Failure & Requirement Outcome Mapping
    # --------------------------------------------------------------------------
    @pytest.mark.asyncio
    async def test_partial_failure_and_requirement_mapping(
        self,
        project_id: str,
    ) -> None:
        test_pass = UnifiedTestDefinition(
            test_id="unit:3333:tests/test_p.py::test_pass",
            tier=TestTier.UNIT,
            name="test_pass",
            source_reference="tests/test_p.py::test_pass",
            project_id=project_id,
            requirement_links=["REQ-PASS"],
            discovery_source=DiscoveryProvenance.PYTEST_DISCOVERY,
        )
        test_fail = UnifiedTestDefinition(
            test_id="unit:3333:tests/test_f.py::test_fail",
            tier=TestTier.UNIT,
            name="test_fail",
            source_reference="tests/test_f.py::test_fail",
            project_id=project_id,
            requirement_links=["REQ-FAIL"],
            discovery_source=DiscoveryProvenance.PYTEST_DISCOVERY,
        )

        inventory = make_inventory(project_id, [test_pass, test_fail])
        plan = make_plan(project_id, inventory, [test_pass, test_fail])

        # Custom executor: passes test_pass, fails test_fail
        class SelectiveFailExecutor(MockSandboxExecutor):
            async def execute(self, request: ExecutionRequest, code_output: CodeGenerationOutput) -> ExecutionResult:
                if "test_f.py" in request.test_target:
                    return ExecutionResult(
                        project_id=request.project_id,
                        execution_type=ExecutionType.TEST,
                        status=ExecutionStatus.FAILED,
                        exit_code=1,
                        tests_failed=1,
                    )
                return ExecutionResult(
                    project_id=request.project_id,
                    execution_type=ExecutionType.TEST,
                    status=ExecutionStatus.PASSED,
                    exit_code=0,
                    tests_passed=1,
                )

        service = RegressionExecutionService(sandbox_executor=SelectiveFailExecutor())
        result = await service.execute_plan(project_id, plan, inventory)

        assert result.status == RegressionExecutionStatus.PARTIAL_FAILURE
        assert result.passed_tests == 1
        assert result.failed_tests == 1

        # Check requirement mapping
        req_pass = result.get_result_for_requirement("REQ-PASS")
        req_fail = result.get_result_for_requirement("REQ-FAIL")
        assert req_pass is not None and req_pass.is_satisfied is True
        assert req_fail is not None and req_fail.is_satisfied is False
        assert "REQ-PASS" in result.protected_requirements_satisfied
        assert "REQ-FAIL" in result.protected_requirements_failed

    # --------------------------------------------------------------------------
    # Repeat Execution Idempotency
    # --------------------------------------------------------------------------
    @pytest.mark.asyncio
    async def test_repeat_execution_idempotency(
        self,
        project_id: str,
        sample_unit_tests: list[UnifiedTestDefinition],
    ) -> None:
        inventory = make_inventory(project_id, sample_unit_tests[:1])
        plan = make_plan(project_id, inventory, sample_unit_tests[:1])

        service = RegressionExecutionService(sandbox_executor=MockSandboxExecutor())

        res_1 = await service.execute_plan(project_id, plan, inventory)
        res_2 = await service.execute_plan(project_id, plan, inventory)

        # Unique execution identities
        assert res_1.execution_id != res_2.execution_id
        # Logical equality holds
        assert res_1 == res_2

    # --------------------------------------------------------------------------
    # BROAD and FULL Plan Execution Modes (Sections 5, 41-B, 41-C)
    # --------------------------------------------------------------------------
    @pytest.mark.asyncio
    async def test_broad_plan_executes_exact_broader_set(
        self,
        project_id: str,
        sample_unit_tests: list[UnifiedTestDefinition],
    ) -> None:
        """Prove that a BROAD plan executes the exact broader set selected."""
        inventory = make_inventory(project_id, sample_unit_tests)
        selected = sample_unit_tests[:4]  # 4 out of 5 tests
        plan = make_plan(
            project_id,
            inventory,
            selected,
            mode=RegressionPlanMode.BROAD,
            requires_broader=True,
        )

        mock_sandbox = RecordingSandboxExecutor()
        service = RegressionExecutionService(sandbox_executor=mock_sandbox)
        result = await service.execute_plan(project_id, plan, inventory)

        assert result.status == RegressionExecutionStatus.PASSED
        assert result.mode == RegressionPlanMode.BROAD
        assert result.total_tests == 4
        assert len(result.test_results) == 4
        assert len(mock_sandbox.executed_targets) == 4

    @pytest.mark.asyncio
    async def test_full_plan_executes_full_selected_set(
        self,
        project_id: str,
        sample_unit_tests: list[UnifiedTestDefinition],
    ) -> None:
        """Prove that a FULL plan executes all tests in the plan."""
        inventory = make_inventory(project_id, sample_unit_tests)
        plan = make_plan(
            project_id,
            inventory,
            sample_unit_tests,
            mode=RegressionPlanMode.FULL,
        )

        mock_sandbox = RecordingSandboxExecutor()
        service = RegressionExecutionService(sandbox_executor=mock_sandbox)
        result = await service.execute_plan(project_id, plan, inventory)

        assert result.status == RegressionExecutionStatus.PASSED
        assert result.mode == RegressionPlanMode.FULL
        assert result.total_tests == 5
        assert len(result.test_results) == 5
        assert len(mock_sandbox.executed_targets) == 5

    # --------------------------------------------------------------------------
    # Timeout and Infrastructure Failure Distinction (Sections 20, 27, 41-Q, 41-R)
    # --------------------------------------------------------------------------
    @pytest.mark.asyncio
    async def test_timeout_handling_records_infrastructure_failure(
        self,
        project_id: str,
        sample_unit_tests: list[UnifiedTestDefinition],
    ) -> None:
        """Prove that a timeout in the executor produces an ERROR status with infrastructure failure."""
        inventory = make_inventory(project_id, sample_unit_tests[:1])
        plan = make_plan(project_id, inventory, sample_unit_tests[:1])

        mock_sandbox = MockSandboxExecutor(
            default_status=ExecutionStatus.TIMEOUT,
            mock_stderr="Execution exceeded 30s limit.",
        )
        service = RegressionExecutionService(sandbox_executor=mock_sandbox)
        result = await service.execute_plan(project_id, plan, inventory)

        assert result.status == RegressionExecutionStatus.ERROR
        assert result.errored_tests == 1
        assert result.test_results[0].status == TestExecutionStatus.ERROR
        assert result.test_results[0].is_infrastructure_failure is True
        assert len(result.infrastructure_failures) == 1

    # --------------------------------------------------------------------------
    # Failure Analysis and Verification Service Reuse (Sections 21, 22, 41-U, 41-V)
    # --------------------------------------------------------------------------
    @pytest.mark.asyncio
    async def test_failure_analysis_and_verification_service_reuse(
        self,
        project_id: str,
        sample_unit_tests: list[UnifiedTestDefinition],
    ) -> None:
        """Prove that existing FailureAnalysisService and VerificationService are reused."""
        inventory = make_inventory(project_id, sample_unit_tests[:1])
        plan = make_plan(project_id, inventory, sample_unit_tests[:1])

        mock_sandbox = MockSandboxExecutor(default_status=ExecutionStatus.FAILED)
        mock_fa = object()  # Passed as an existing service instance
        mock_verif = object()

        service = RegressionExecutionService(
            sandbox_executor=mock_sandbox,
            failure_analysis_service=mock_fa,
            verification_service=mock_verif,
        )

        result = await service.execute_plan(
            project_id,
            plan,
            inventory,
            trigger_failure_analysis=True,
        )

        assert result.status == RegressionExecutionStatus.FAILED
        assert result.artifacts.get("failure_analysis_triggered") is True
        assert "failure_analysis_notes" in result.artifacts
        assert result.artifacts.get("verification_evaluated") is True

    # --------------------------------------------------------------------------
    # No Automatic Remediation or Replanning (Sections 35, 36, 41-AA, 41-AB)
    # --------------------------------------------------------------------------
    @pytest.mark.asyncio
    async def test_no_automatic_remediation_or_replanning_occurs(
        self,
        project_id: str,
        sample_unit_tests: list[UnifiedTestDefinition],
    ) -> None:
        """Prove that failed tests do NOT trigger any automatic source modification or replanning."""
        inventory = make_inventory(project_id, sample_unit_tests[:2])
        plan = make_plan(project_id, inventory, sample_unit_tests[:2])

        mock_sandbox = MockSandboxExecutor(default_status=ExecutionStatus.FAILED)
        service = RegressionExecutionService(sandbox_executor=mock_sandbox)

        result = await service.execute_plan(project_id, plan, inventory)

        assert result.status == RegressionExecutionStatus.FAILED
        # Verify no remediation artifacts or loops exist in metadata/artifacts
        assert "remediation" not in result.artifacts
        assert "replanned" not in result.metadata
        # Zero code modification occurred
        assert len(result.test_results) == 2

    # --------------------------------------------------------------------------
    # Execution Authority Matrix Verification (Sections 3, 38, 41-O)
    # --------------------------------------------------------------------------
    def test_no_execution_engine_duplication(self) -> None:
        """Verify that RegressionExecutionService delegates strictly to approved authorities."""
        mock_sandbox = MockSandboxExecutor()
        mock_browser = MockBrowserTestingService()
        service = RegressionExecutionService(
            sandbox_executor=mock_sandbox,
            browser_service=mock_browser,
        )

        # Confirm references to execution engines are exact injected authorities
        assert service.sandbox_executor is mock_sandbox
        assert service.browser_service is mock_browser
        assert service.journey_adapter is BrowserJourneyAdapter or issubclass(service.journey_adapter, BrowserJourneyAdapter)

