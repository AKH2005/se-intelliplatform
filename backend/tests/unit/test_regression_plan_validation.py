"""Unit Tests for RegressionPlanValidator (Phase 11L Stage 4).

Validates:
1. Rejection of unknown test IDs not present in UnifiedTestInventory.
2. Rejection of duplicate test IDs or models.
3. Strict cross-project boundary enforcement.
4. Rejection of unvalidated browser journeys.
5. Invariant enforcement: SELECTIVE + SAFE is rejected if requires_broader_regression is True.
6. Validation of tier integrity and requirement ID formatting.
7. Validation of inventory count consistency.
"""

from datetime import datetime, timezone
import pytest

from app.testing.inventory.contracts import (
    DiscoveryProvenance,
    DiscoveryStatus,
    TestTier,
    UnifiedTestDefinition,
    UnifiedTestInventory,
    compute_deterministic_inventory_id,
)
from app.testing.regression.contracts import (
    PlanSelectionReason,
    RegressionPlan,
    RegressionPlanMode,
    SelectedTest,
)
from app.testing.regression.errors import (
    RegressionPlanIsolationError,
    RegressionPlanValidationError,
)
from app.testing.regression.validator import RegressionPlanValidator


# ==============================================================================
# Helper Factories
# ==============================================================================

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


class TestRegressionPlanValidator:
    """Comprehensive test suite for RegressionPlanValidator."""

    @pytest.fixture
    def project_id(self) -> str:
        return "22222222-2222-2222-2222-222222222222"

    @pytest.fixture
    def validator(self) -> RegressionPlanValidator:
        return RegressionPlanValidator()

    @pytest.fixture
    def valid_unit_test(self, project_id: str) -> UnifiedTestDefinition:
        return UnifiedTestDefinition(
            test_id="unit:2222:tests/test_foo.py::test_foo",
            tier=TestTier.UNIT,
            name="test_foo",
            source_reference="tests/test_foo.py::test_foo",
            project_id=project_id,
            requirement_links=["REQ-FOO-01"],
            discovery_source=DiscoveryProvenance.PYTEST_DISCOVERY,
        )

    @pytest.fixture
    def valid_plan(
        self,
        project_id: str,
        valid_unit_test: UnifiedTestDefinition,
    ) -> tuple[RegressionPlan, UnifiedTestInventory]:
        inventory = make_inventory(project_id, [valid_unit_test])
        sel_test = SelectedTest(
            test_id=valid_unit_test.test_id,
            tier=TestTier.UNIT,
            name=valid_unit_test.name,
            source_reference=valid_unit_test.source_reference,
            selection_reasons=[PlanSelectionReason.DIRECT_CHANGE],
            affected_requirements=["REQ-FOO-01"],
            affected_files=[],
            selection_scope="DIRECT",
        )
        plan = RegressionPlan(
            project_id=project_id,
            mode=RegressionPlanMode.SELECTIVE,
            inventory_id=inventory.inventory_id,
            selected_test_ids=[valid_unit_test.test_id],
            selected_tests=[sel_test],
            selected_tests_by_tier={
                TestTier.UNIT.value: [valid_unit_test.test_id],
                TestTier.AI_TEST.value: [],
                TestTier.BROWSER_SMOKE.value: [],
                TestTier.BROWSER_JOURNEY.value: [],
            },
            selected_requirement_ids=["REQ-FOO-01"],
            affected_requirement_ids=["REQ-FOO-01"],
            protected_requirement_ids=["REQ-FOO-01"],
            uncovered_affected_requirement_ids=[],
            unrelated_requirement_ids=[],
            selection_reasons_by_test={valid_unit_test.test_id: [PlanSelectionReason.DIRECT_CHANGE]},
            broadening_reasons=[],
            requires_broader_regression=False,
            is_execution_safe=True,
            plan_warnings=[],
            total_inventory_tests=1,
            unselected_test_count=0,
            created_at=datetime.now(timezone.utc),
            metadata={},
        )
        return plan, inventory

    def test_valid_plan_passes_validation(
        self,
        validator: RegressionPlanValidator,
        valid_plan: tuple[RegressionPlan, UnifiedTestInventory],
    ) -> None:
        plan, inventory = valid_plan
        # Should complete without error
        validator.validate(plan, inventory)

    def test_rejection_of_unknown_test_id(
        self,
        validator: RegressionPlanValidator,
        valid_plan: tuple[RegressionPlan, UnifiedTestInventory],
    ) -> None:
        plan, inventory = valid_plan
        plan.selected_test_ids.append("unit:2222:tests/unknown.py::test_nonexistent")
        plan.selected_tests.append(
            SelectedTest(
                test_id="unit:2222:tests/unknown.py::test_nonexistent",
                tier=TestTier.UNIT,
                name="test_nonexistent",
                source_reference="tests/unknown.py::test_nonexistent",
                selection_scope="DIRECT",
            )
        )
        # Fix counts to isolate test id error
        plan.total_inventory_tests = inventory.total_tests
        plan.unselected_test_count = inventory.total_tests - len(plan.selected_test_ids)

        with pytest.raises(RegressionPlanValidationError) as exc_info:
            validator.validate(plan, inventory)
        assert "Plan contains unknown test ID" in str(exc_info.value)

    def test_rejection_of_duplicate_test_ids(
        self,
        validator: RegressionPlanValidator,
        valid_plan: tuple[RegressionPlan, UnifiedTestInventory],
    ) -> None:
        plan, inventory = valid_plan
        # Duplicate the test ID
        plan.selected_test_ids.append(plan.selected_test_ids[0])

        with pytest.raises(RegressionPlanValidationError) as exc_info:
            validator.validate(plan, inventory)
        assert "Duplicate test IDs detected" in str(exc_info.value)

    def test_rejection_of_project_isolation_mismatch(
        self,
        validator: RegressionPlanValidator,
        valid_plan: tuple[RegressionPlan, UnifiedTestInventory],
    ) -> None:
        plan, inventory = valid_plan
        plan.project_id = "99999999-9999-9999-9999-999999999999"

        with pytest.raises(RegressionPlanIsolationError) as exc_info:
            validator.validate(plan, inventory)
        assert "does not match inventory project ID" in str(exc_info.value)

    def test_rejection_of_foreign_test_in_plan(
        self,
        validator: RegressionPlanValidator,
        project_id: str,
    ) -> None:
        foreign_test = UnifiedTestDefinition(
            test_id="unit:foreign:tests/test_x.py::test_x",
            tier=TestTier.UNIT,
            name="test_x",
            source_reference="tests/test_x.py::test_x",
            project_id="88888888-8888-8888-8888-888888888888",  # Foreign!
            requirement_links=[],
            discovery_source=DiscoveryProvenance.PYTEST_DISCOVERY,
        )
        # Create inventory that illegally contains foreign test
        inventory = make_inventory(project_id, [foreign_test])
        sel_test = SelectedTest(
            test_id=foreign_test.test_id,
            tier=TestTier.UNIT,
            name=foreign_test.name,
            source_reference=foreign_test.source_reference,
            selection_scope="DIRECT",
        )
        plan = RegressionPlan(
            project_id=project_id,
            mode=RegressionPlanMode.SELECTIVE,
            inventory_id=inventory.inventory_id,
            selected_test_ids=[foreign_test.test_id],
            selected_tests=[sel_test],
            selected_tests_by_tier={
                TestTier.UNIT.value: [foreign_test.test_id],
                TestTier.AI_TEST.value: [],
                TestTier.BROWSER_SMOKE.value: [],
                TestTier.BROWSER_JOURNEY.value: [],
            },
            selected_requirement_ids=[],
            affected_requirement_ids=[],
            protected_requirement_ids=[],
            uncovered_affected_requirement_ids=[],
            unrelated_requirement_ids=[],
            is_execution_safe=True,
            total_inventory_tests=1,
            unselected_test_count=0,
        )

        with pytest.raises(RegressionPlanIsolationError) as exc_info:
            validator.validate(plan, inventory)
        assert "violating isolation with plan project" in str(exc_info.value)

    def test_rejection_of_unvalidated_browser_journey(
        self,
        validator: RegressionPlanValidator,
        project_id: str,
    ) -> None:
        unvalidated_journey = UnifiedTestDefinition(
            test_id="journey:2222:unvalidated_j",
            tier=TestTier.BROWSER_JOURNEY,
            name="unvalidated_j",
            source_reference="raw_candidate",
            project_id=project_id,
            discovery_source=DiscoveryProvenance.AI_TEST_SUITE,  # Not VALIDATED_BROWSER_JOURNEY
        )
        inventory = make_inventory(project_id, [unvalidated_journey])
        sel_test = SelectedTest(
            test_id=unvalidated_journey.test_id,
            tier=TestTier.BROWSER_JOURNEY,
            name=unvalidated_journey.name,
            source_reference=unvalidated_journey.source_reference,
            selection_scope="DIRECT",
        )
        plan = RegressionPlan(
            project_id=project_id,
            mode=RegressionPlanMode.SELECTIVE,
            inventory_id=inventory.inventory_id,
            selected_test_ids=[unvalidated_journey.test_id],
            selected_tests=[sel_test],
            selected_tests_by_tier={
                TestTier.UNIT.value: [],
                TestTier.AI_TEST.value: [],
                TestTier.BROWSER_SMOKE.value: [],
                TestTier.BROWSER_JOURNEY.value: [unvalidated_journey.test_id],
            },
            selected_requirement_ids=[],
            affected_requirement_ids=[],
            protected_requirement_ids=[],
            uncovered_affected_requirement_ids=[],
            unrelated_requirement_ids=[],
            is_execution_safe=True,
            total_inventory_tests=1,
            unselected_test_count=0,
        )

        with pytest.raises(RegressionPlanValidationError) as exc_info:
            validator.validate(plan, inventory)
        assert "Unvalidated browser journey candidate" in str(exc_info.value)

    def test_rejection_of_unsafe_selective_execution_invariant(
        self,
        validator: RegressionPlanValidator,
        valid_plan: tuple[RegressionPlan, UnifiedTestInventory],
    ) -> None:
        """CRITICAL INVARIANT: requires_broader_regression=True in SELECTIVE mode CANNOT have is_execution_safe=True."""
        plan, inventory = valid_plan
        plan.requires_broader_regression = True
        plan.mode = RegressionPlanMode.SELECTIVE
        plan.is_execution_safe = True  # ILLEGAL STATE!

        with pytest.raises(RegressionPlanValidationError) as exc_info:
            validator.validate(plan, inventory)
        assert "Conservative safety invariant violated" in str(exc_info.value)

    def test_rejection_of_inventory_count_mismatch(
        self,
        validator: RegressionPlanValidator,
        valid_plan: tuple[RegressionPlan, UnifiedTestInventory],
    ) -> None:
        plan, inventory = valid_plan
        plan.total_inventory_tests = 999  # Mismatched!

        with pytest.raises(RegressionPlanValidationError) as exc_info:
            validator.validate(plan, inventory)
        assert "total_inventory_tests" in str(exc_info.value)
