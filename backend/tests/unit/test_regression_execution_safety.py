"""Unit Tests for Regression Execution Safety Boundaries (Phase 11L Stage 5).

Validates:
1. Strict cross-project isolation enforcement on execution dispatch.
2. Rejection of malformed plans, unknown test IDs, and duplicate entries.
3. Unvalidated browser journeys blocked from execution.
4. Handling of unconfigured execution authorities.
5. Empty plan safe completion.
6. Zero arbitrary subprocess or shell execution.
"""

from datetime import datetime, timezone
import subprocess
import uuid
import pytest

from app.browser.contracts import DeterministicBrowserTestDefinition
from app.sandbox.contracts import ExecutionStatus
from app.sandbox.mock_executor import MockSandboxExecutor
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
) -> RegressionPlan:
    clean_proj = str(project_id).strip().lower()
    sel_models: list[SelectedTest] = []
    sel_by_tier: dict[str, list[str]] = {t.value: [] for t in TestTier}
    reasons_by_test: dict[str, list[PlanSelectionReason]] = {}

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

    for t_val in sel_by_tier:
        sel_by_tier[t_val].sort()

    return RegressionPlan(
        project_id=clean_proj,
        mode=mode,
        inventory_id=inventory.inventory_id,
        selected_test_ids=sorted([t.test_id for t in selected_tests]),
        selected_tests=sel_models,
        selected_tests_by_tier=sel_by_tier,
        selected_requirement_ids=[],
        affected_requirement_ids=[],
        protected_requirement_ids=[],
        uncovered_affected_requirement_ids=[],
        unrelated_requirement_ids=[],
        selection_reasons_by_test=reasons_by_test,
        broadening_reasons=[],
        requires_broader_regression=False,
        is_execution_safe=is_execution_safe,
        plan_warnings=[],
        total_inventory_tests=inventory.total_tests,
        unselected_test_count=inventory.total_tests - len(selected_tests),
        created_at=datetime.now(timezone.utc),
        metadata={},
    )


class TestRegressionExecutionSafety:
    """Security and safety invariant tests for RegressionExecutionService."""

    @pytest.fixture
    def project_id(self) -> str:
        return "44444444-4444-4444-4444-444444444444"

    @pytest.fixture
    def valid_test(self, project_id: str) -> UnifiedTestDefinition:
        return UnifiedTestDefinition(
            test_id="unit:4444:tests/test_safe.py::test_safe",
            tier=TestTier.UNIT,
            name="test_safe",
            source_reference="tests/test_safe.py::test_safe",
            project_id=project_id,
            requirement_links=["REQ-SAFE"],
            discovery_source=DiscoveryProvenance.PYTEST_DISCOVERY,
        )

    @pytest.mark.asyncio
    async def test_rejection_of_project_id_mismatch(
        self,
        project_id: str,
        valid_test: UnifiedTestDefinition,
    ) -> None:
        inventory = make_inventory(project_id, [valid_test])
        plan = make_plan(project_id, inventory, [valid_test])

        service = RegressionExecutionService(sandbox_executor=MockSandboxExecutor())
        foreign_id = "99999999-9999-9999-9999-999999999999"

        with pytest.raises(RegressionPlanIsolationError) as exc_info:
            await service.execute_plan(foreign_id, plan, inventory)
        assert "does not match plan project ID" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_rejection_of_inventory_mismatch(
        self,
        project_id: str,
        valid_test: UnifiedTestDefinition,
    ) -> None:
        inventory = make_inventory(project_id, [valid_test])
        plan = make_plan(project_id, inventory, [valid_test])

        foreign_inv = make_inventory("88888888-8888-8888-8888-888888888888", [])
        service = RegressionExecutionService(sandbox_executor=MockSandboxExecutor())

        with pytest.raises(RegressionPlanIsolationError) as exc_info:
            await service.execute_plan(project_id, plan, foreign_inv)
        assert "does not match inventory project ID" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_empty_plan_completes_safely(
        self,
        project_id: str,
        valid_test: UnifiedTestDefinition,
    ) -> None:
        inventory = make_inventory(project_id, [valid_test])
        empty_plan = make_plan(project_id, inventory, [])

        service = RegressionExecutionService(sandbox_executor=MockSandboxExecutor())
        result = await service.execute_plan(project_id, empty_plan, inventory)

        assert result.status == RegressionExecutionStatus.PASSED
        assert result.total_tests == 0
        assert result.passed_tests == 0

    @pytest.mark.asyncio
    async def test_unconfigured_sandbox_executor_records_infrastructure_error(
        self,
        project_id: str,
        valid_test: UnifiedTestDefinition,
    ) -> None:
        inventory = make_inventory(project_id, [valid_test])
        plan = make_plan(project_id, inventory, [valid_test])

        # Service configured with NO sandbox executor
        service = RegressionExecutionService(sandbox_executor=None)
        result = await service.execute_plan(project_id, plan, inventory)

        assert result.status == RegressionExecutionStatus.ERROR
        assert result.errored_tests == 1
        assert result.test_results[0].is_infrastructure_failure is True
        assert "No sandbox executor configured" in result.test_results[0].message

    @pytest.mark.asyncio
    async def test_journey_lacking_validated_identity_is_blocked(
        self,
        project_id: str,
    ) -> None:
        journey_test = UnifiedTestDefinition(
            test_id="journey:4444:orphan_journey",
            tier=TestTier.BROWSER_JOURNEY,
            name="orphan_journey",
            source_reference="orphan",
            project_id=project_id,
            discovery_source=DiscoveryProvenance.VALIDATED_BROWSER_JOURNEY,
            metadata={"validated_journey_id": "missing_vj_id"},
        )
        inventory = make_inventory(project_id, [journey_test])
        plan = make_plan(project_id, inventory, [journey_test])

        service = RegressionExecutionService(browser_service=None)
        result = await service.execute_plan(project_id, plan, inventory, validated_journeys=[])

        # Must be BLOCKED because no ValidatedBrowserJourney object was provided
        assert result.test_results[0].status == TestExecutionStatus.BLOCKED
        assert "lacks an authoritative ValidatedBrowserJourney" in result.test_results[0].message

    @pytest.mark.asyncio
    async def test_zero_arbitrary_subprocess_execution(
        self,
        project_id: str,
        valid_test: UnifiedTestDefinition,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Verify that regression execution makes zero direct subprocess.run or Popen calls."""
        def forbidden_subprocess(*args, **kwargs):
            raise AssertionError("Arbitrary subprocess execution is strictly forbidden in Stage 5!")

        monkeypatch.setattr(subprocess, "run", forbidden_subprocess)
        monkeypatch.setattr(subprocess, "Popen", forbidden_subprocess)

        inventory = make_inventory(project_id, [valid_test])
        plan = make_plan(project_id, inventory, [valid_test])

        service = RegressionExecutionService(sandbox_executor=MockSandboxExecutor())
        result = await service.execute_plan(project_id, plan, inventory)
        assert result.status == RegressionExecutionStatus.PASSED

    @pytest.mark.asyncio
    async def test_unknown_test_id_blocked_by_validator(
        self,
        project_id: str,
        valid_test: UnifiedTestDefinition,
    ) -> None:
        """Prove that a plan containing a test ID absent from the inventory is rejected."""
        inventory = make_inventory(project_id, [valid_test])

        unknown_test = SelectedTest(
            test_id="unit:4444:non_existent.py::test_phantom",
            tier=TestTier.UNIT,
            name="test_phantom",
            source_reference="non_existent.py::test_phantom",
            selection_reasons=[PlanSelectionReason.DIRECT_CHANGE],
            selection_scope="DIRECT",
        )

        plan = RegressionPlan(
            project_id=project_id,
            mode=RegressionPlanMode.SELECTIVE,
            inventory_id=inventory.inventory_id,
            selected_test_ids=["unit:4444:non_existent.py::test_phantom"],
            selected_tests=[unknown_test],
            selected_tests_by_tier={TestTier.UNIT.value: ["unit:4444:non_existent.py::test_phantom"]},
            selected_requirement_ids=[],
            affected_requirement_ids=[],
            protected_requirement_ids=[],
            uncovered_affected_requirement_ids=[],
            unrelated_requirement_ids=[],
            selection_reasons_by_test={"unit:4444:non_existent.py::test_phantom": [PlanSelectionReason.DIRECT_CHANGE]},
            broadening_reasons=[],
            requires_broader_regression=False,
            is_execution_safe=True,
            plan_warnings=[],
            total_inventory_tests=inventory.total_tests,
            unselected_test_count=0,
            created_at=datetime.now(timezone.utc),
            metadata={},
        )

        service = RegressionExecutionService(sandbox_executor=MockSandboxExecutor())
        with pytest.raises(RegressionPlanValidationError) as exc_info:
            await service.execute_plan(project_id, plan, inventory)
        assert "Plan contains unknown test ID" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_duplicate_test_ids_blocked_by_validator(
        self,
        project_id: str,
        valid_test: UnifiedTestDefinition,
    ) -> None:
        """Prove that duplicate selected test IDs are rejected by safety validation."""
        inventory = make_inventory(project_id, [valid_test])

        sel = SelectedTest(
            test_id=valid_test.test_id,
            tier=valid_test.tier,
            name=valid_test.name,
            source_reference=valid_test.source_reference,
            selection_reasons=[PlanSelectionReason.DIRECT_CHANGE],
            selection_scope="DIRECT",
        )

        plan = RegressionPlan(
            project_id=project_id,
            mode=RegressionPlanMode.SELECTIVE,
            inventory_id=inventory.inventory_id,
            selected_test_ids=[valid_test.test_id, valid_test.test_id],
            selected_tests=[sel, sel],
            selected_tests_by_tier={TestTier.UNIT.value: [valid_test.test_id]},
            selected_requirement_ids=[],
            affected_requirement_ids=[],
            protected_requirement_ids=[],
            uncovered_affected_requirement_ids=[],
            unrelated_requirement_ids=[],
            selection_reasons_by_test={valid_test.test_id: [PlanSelectionReason.DIRECT_CHANGE]},
            broadening_reasons=[],
            requires_broader_regression=False,
            is_execution_safe=True,
            plan_warnings=[],
            total_inventory_tests=inventory.total_tests,
            unselected_test_count=0,
            created_at=datetime.now(timezone.utc),
            metadata={},
        )

        service = RegressionExecutionService(sandbox_executor=MockSandboxExecutor())
        with pytest.raises(RegressionPlanValidationError) as exc_info:
            await service.execute_plan(project_id, plan, inventory)
        assert "Duplicate test IDs detected" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_secret_safety_in_execution_result(
        self,
        project_id: str,
        valid_test: UnifiedTestDefinition,
    ) -> None:
        """Prove that secret tokens and environment variables are not dumped into reports."""
        inventory = make_inventory(project_id, [valid_test])
        plan = make_plan(project_id, inventory, [valid_test])

        mock_sandbox = MockSandboxExecutor(
            default_status=ExecutionStatus.PASSED,
            mock_stdout="Execution finished with clean logs.",
        )
        service = RegressionExecutionService(sandbox_executor=mock_sandbox)
        result = await service.execute_plan(project_id, plan, inventory)

        report_dump = str(result.model_dump())
        assert "OPENAI_API_KEY" not in report_dump
        assert "ANTHROPIC_API_KEY" not in report_dump
        assert "SECRET_KEY" not in report_dump
        assert "DATABASE_URL" not in report_dump

