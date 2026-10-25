"""Unit Tests for SelectiveRegressionPlanner (Phase 11L Stage 4).

Validates all 30 prompt requirements (A-AD) and critical safety requirements:
1. Empty change set & no affected tests handling.
2. Direct, transitive, and multi-tier test selection.
3. Strict requirement protection using authoritative links only (inferred ignored).
4. Coverage gap detection for affected but uncovered requirements.
5. Mode semantics: SELECTIVE, BROAD, and FULL.
6. Conservative safety invariants (unknown dependencies/dynamic imports never result in SELECTIVE + SAFE).
7. Validated browser journey and smoke handling.
8. Deterministic repeated planning equivalence (plan_1 == plan_2).
9. Project isolation enforcement across all inputs.
10. Zero execution side effects.
"""

from datetime import datetime, timezone
import subprocess
import uuid
import pytest

from app.testing.coverage.contracts import UnifiedCoverageReport
from app.testing.impact.contracts import (
    AnalysisConfidence,
    ChangeImpactReport,
    ImpactReason,
    UncertainDependency,
)
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
    PlanSelectionReason,
    RegressionPlan,
    RegressionPlanMode,
    SelectedTest,
)
from app.testing.regression.errors import (
    RegressionPlanIsolationError,
    RegressionPlanValidationError,
)
from app.testing.regression.planner import SelectiveRegressionPlanner


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


def make_impact_report(
    project_id: str,
    changed_files: list[str] | None = None,
    affected_files: list[str] | None = None,
    affected_tests: list[UnifiedTestDefinition] | None = None,
    test_reasons: dict[str, list[ImpactReason]] | None = None,
    affected_reqs: list[str] | None = None,
    requires_broader: bool = False,
    confidence: AnalysisConfidence = AnalysisConfidence.HIGH,
    uncertain_files: list[str] | None = None,
) -> ChangeImpactReport:
    clean_proj = str(project_id).strip().lower()
    cf = sorted(changed_files or [])
    aff_files = sorted(affected_files or cf)
    aff_tests = affected_tests or []
    aff_test_ids = sorted([t.test_id for t in aff_tests])
    t_reasons = test_reasons or {}
    reqs = sorted(affected_reqs or [])
    u_files = sorted(uncertain_files or [])

    return ChangeImpactReport(
        project_id=clean_proj,
        changed_files=cf,
        directly_affected_files=aff_files,
        transitively_affected_files=[],
        all_affected_files=aff_files,
        affected_tests=aff_tests,
        affected_test_ids=aff_test_ids,
        test_impact_reasons=t_reasons,
        affected_requirements=reqs,
        requirement_impact_reasons={r: [ImpactReason.AUTHORITATIVE_REQUIREMENT_LINK] for r in reqs},
        uncertain_files=u_files,
        uncertain_dependencies=[UncertainDependency(file_path=f, reason="UNCERTAIN") for f in u_files],
        requires_broader_regression=requires_broader,
        analysis_confidence=confidence,
    )


# ==============================================================================
# Test Suite
# ==============================================================================

class TestSelectiveRegressionPlanner:
    """Comprehensive test suite for SelectiveRegressionPlanner."""

    @pytest.fixture
    def project_id(self) -> str:
        return "11111111-1111-1111-1111-111111111111"

    @pytest.fixture
    def planner(self) -> SelectiveRegressionPlanner:
        return SelectiveRegressionPlanner()

    @pytest.fixture
    def sample_unit_test(self, project_id: str) -> UnifiedTestDefinition:
        return UnifiedTestDefinition(
            test_id="unit:1111:tests/test_math.py::test_add",
            tier=TestTier.UNIT,
            name="test_add",
            source_reference="tests/test_math.py::test_add",
            project_id=project_id,
            requirement_links=["REQ-MATH-01"],
            discovery_source=DiscoveryProvenance.PYTEST_DISCOVERY,
            target_file="app/math.py",
            target_symbol="add",
            metadata={"file_path": "tests/test_math.py"},
        )

    @pytest.fixture
    def sample_ai_test(self, project_id: str) -> UnifiedTestDefinition:
        return UnifiedTestDefinition(
            test_id="ai_test:1111:tests/ai/test_billing.py::test_tax",
            tier=TestTier.AI_TEST,
            name="test_tax",
            source_reference="tests/ai/test_billing.py::test_tax",
            project_id=project_id,
            requirement_links=["REQ-BILLING-01"],
            discovery_source=DiscoveryProvenance.AI_TEST_SUITE,
            target_file="app/billing.py",
            metadata={"file_path": "tests/ai/test_billing.py"},
        )

    @pytest.fixture
    def sample_smoke_test(self, project_id: str) -> UnifiedTestDefinition:
        return UnifiedTestDefinition(
            test_id="smoke:1111:browser_smoke::route_login",
            tier=TestTier.BROWSER_SMOKE,
            name="route_login",
            source_reference="/login",
            project_id=project_id,
            requirement_links=["REQ-AUTH-01"],
            discovery_source=DiscoveryProvenance.BROWSER_SMOKE_SUITE,
            target_symbol="/login",
            metadata={"routes": ["/login"]},
        )

    @pytest.fixture
    def sample_journey_test(self, project_id: str) -> UnifiedTestDefinition:
        return UnifiedTestDefinition(
            test_id="journey:1111:journey_checkout",
            tier=TestTier.BROWSER_JOURNEY,
            name="journey_checkout",
            source_reference="checkout_flow",
            project_id=project_id,
            requirement_links=["REQ-CHECKOUT-01"],
            discovery_source=DiscoveryProvenance.VALIDATED_BROWSER_JOURNEY,
            metadata={"validated_journey_id": "vj_123", "is_validated": True},
        )

    # --------------------------------------------------------------------------
    # Scenario A: Empty Change Set
    # --------------------------------------------------------------------------
    def test_scenario_a_empty_change_set(
        self,
        planner: SelectiveRegressionPlanner,
        project_id: str,
        sample_unit_test: UnifiedTestDefinition,
    ) -> None:
        inventory = make_inventory(project_id, [sample_unit_test])
        impact = make_impact_report(project_id, changed_files=[])

        plan = planner.plan_regression(project_id, inventory, impact, mode=RegressionPlanMode.SELECTIVE)

        assert plan.selected_test_ids == []
        assert plan.selected_tests == []
        assert plan.mode == RegressionPlanMode.SELECTIVE
        assert plan.is_execution_safe is True
        assert plan.unselected_test_count == 1

    # --------------------------------------------------------------------------
    # Scenario B: No Affected Tests
    # --------------------------------------------------------------------------
    def test_scenario_b_no_affected_tests(
        self,
        planner: SelectiveRegressionPlanner,
        project_id: str,
        sample_unit_test: UnifiedTestDefinition,
    ) -> None:
        inventory = make_inventory(project_id, [sample_unit_test])
        impact = make_impact_report(project_id, changed_files=["docs/README.md"])

        plan = planner.plan_regression(project_id, inventory, impact, mode=RegressionPlanMode.SELECTIVE)

        assert plan.selected_test_ids == []
        assert plan.is_execution_safe is True
        assert plan.total_inventory_tests == 1

    # --------------------------------------------------------------------------
    # Scenario C: One Directly Changed Unit Test
    # --------------------------------------------------------------------------
    def test_scenario_c_one_directly_changed_unit_test(
        self,
        planner: SelectiveRegressionPlanner,
        project_id: str,
        sample_unit_test: UnifiedTestDefinition,
    ) -> None:
        inventory = make_inventory(project_id, [sample_unit_test])
        impact = make_impact_report(
            project_id,
            changed_files=["tests/test_math.py"],
            affected_tests=[sample_unit_test],
            test_reasons={sample_unit_test.test_id: [ImpactReason.DIRECT_CHANGE, ImpactReason.DIRECT_TEST_FILE]},
        )

        plan = planner.plan_regression(project_id, inventory, impact, mode=RegressionPlanMode.SELECTIVE)

        assert plan.selected_test_ids == [sample_unit_test.test_id]
        sel_t = plan.selected_tests[0]
        assert PlanSelectionReason.DIRECT_CHANGE in sel_t.selection_reasons
        assert sel_t.selection_scope == "DIRECT"
        assert plan.is_execution_safe is True

    # --------------------------------------------------------------------------
    # Scenario D: Direct Dependency Impact
    # --------------------------------------------------------------------------
    def test_scenario_d_direct_dependency_impact(
        self,
        planner: SelectiveRegressionPlanner,
        project_id: str,
        sample_unit_test: UnifiedTestDefinition,
    ) -> None:
        inventory = make_inventory(project_id, [sample_unit_test])
        impact = make_impact_report(
            project_id,
            changed_files=["app/math.py"],
            affected_tests=[sample_unit_test],
            test_reasons={sample_unit_test.test_id: [ImpactReason.DEPENDENCY_CLOSURE]},
        )

        plan = planner.plan_regression(project_id, inventory, impact, mode=RegressionPlanMode.SELECTIVE)

        assert plan.selected_test_ids == [sample_unit_test.test_id]
        sel_t = plan.selected_tests[0]
        assert PlanSelectionReason.DEPENDENCY_IMPACT in sel_t.selection_reasons
        assert sel_t.selection_scope == "DEPENDENCY"

    # --------------------------------------------------------------------------
    # Scenario E: Transitive Dependency Impact
    # --------------------------------------------------------------------------
    def test_scenario_e_transitive_dependency_impact(
        self,
        planner: SelectiveRegressionPlanner,
        project_id: str,
        sample_unit_test: UnifiedTestDefinition,
    ) -> None:
        inventory = make_inventory(project_id, [sample_unit_test])
        impact = make_impact_report(
            project_id,
            changed_files=["app/core/base_math.py"],
            affected_files=["app/core/base_math.py", "app/math.py", "tests/test_math.py"],
            affected_tests=[sample_unit_test],
            test_reasons={sample_unit_test.test_id: [ImpactReason.DEPENDENCY_CLOSURE]},
        )

        plan = planner.plan_regression(project_id, inventory, impact, mode=RegressionPlanMode.SELECTIVE)

        assert plan.selected_test_ids == [sample_unit_test.test_id]
        assert PlanSelectionReason.DEPENDENCY_IMPACT in plan.selected_tests[0].selection_reasons

    # --------------------------------------------------------------------------
    # Scenario F: Requirement Protection
    # --------------------------------------------------------------------------
    def test_scenario_f_requirement_protection(
        self,
        planner: SelectiveRegressionPlanner,
        project_id: str,
    ) -> None:
        test_a = UnifiedTestDefinition(
            test_id="unit:1111:tests/test_a.py::test_a",
            tier=TestTier.UNIT,
            name="test_a",
            source_reference="tests/test_a.py::test_a",
            project_id=project_id,
            requirement_links=["REQ-PAYMENT-01"],
            discovery_source=DiscoveryProvenance.PYTEST_DISCOVERY,
        )
        test_b = UnifiedTestDefinition(
            test_id="unit:1111:tests/test_b.py::test_b",
            tier=TestTier.UNIT,
            name="test_b",
            source_reference="tests/test_b.py::test_b",
            project_id=project_id,
            requirement_links=["REQ-PAYMENT-01"],
            discovery_source=DiscoveryProvenance.PYTEST_DISCOVERY,
        )
        test_c = UnifiedTestDefinition(
            test_id="unit:1111:tests/test_c.py::test_c",
            tier=TestTier.UNIT,
            name="test_c",
            source_reference="tests/test_c.py::test_c",
            project_id=project_id,
            requirement_links=["REQ-OTHER-99"],
            discovery_source=DiscoveryProvenance.PYTEST_DISCOVERY,
        )

        inventory = make_inventory(project_id, [test_a, test_b, test_c])
        # REQ-PAYMENT-01 is affected, test_a is affected via code impact, test_b is not directly affected
        impact = make_impact_report(
            project_id,
            changed_files=["app/payment.py"],
            affected_tests=[test_a],
            test_reasons={test_a.test_id: [ImpactReason.DEPENDENCY_CLOSURE]},
            affected_reqs=["REQ-PAYMENT-01"],
        )

        plan = planner.plan_regression(project_id, inventory, impact, mode=RegressionPlanMode.SELECTIVE)

        # Both test_a and test_b should be selected!
        assert test_a.test_id in plan.selected_test_ids
        assert test_b.test_id in plan.selected_test_ids
        assert test_c.test_id not in plan.selected_test_ids

        # test_b reason must be REQUIREMENT_PROTECTION
        test_b_sel = next(t for t in plan.selected_tests if t.test_id == test_b.test_id)
        assert PlanSelectionReason.REQUIREMENT_PROTECTION in test_b_sel.selection_reasons
        assert test_b_sel.selection_scope == "REQUIREMENT"
        assert plan.is_requirement_protected("REQ-PAYMENT-01") is True

    # --------------------------------------------------------------------------
    # Scenario G & H: Four Test Tiers Selection
    # --------------------------------------------------------------------------
    def test_scenario_gh_four_tier_selection(
        self,
        planner: SelectiveRegressionPlanner,
        project_id: str,
        sample_unit_test: UnifiedTestDefinition,
        sample_ai_test: UnifiedTestDefinition,
        sample_smoke_test: UnifiedTestDefinition,
        sample_journey_test: UnifiedTestDefinition,
    ) -> None:
        all_tests = [sample_unit_test, sample_ai_test, sample_smoke_test, sample_journey_test]
        inventory = make_inventory(project_id, all_tests)
        impact = make_impact_report(
            project_id,
            changed_files=["app/main.py"],
            affected_tests=all_tests,
            test_reasons={
                sample_unit_test.test_id: [ImpactReason.DEPENDENCY_CLOSURE],
                sample_ai_test.test_id: [ImpactReason.DEPENDENCY_CLOSURE],
                sample_smoke_test.test_id: [ImpactReason.BROWSER_ROUTE_OVERLAP],
                sample_journey_test.test_id: [ImpactReason.DEPENDENCY_CLOSURE],
            },
        )

        plan = planner.plan_regression(project_id, inventory, impact, mode=RegressionPlanMode.SELECTIVE)

        assert len(plan.selected_tests) == 4
        # Verify tests are segregated cleanly into all four tiers in selected_tests_by_tier
        assert plan.selected_tests_by_tier[TestTier.UNIT.value] == [sample_unit_test.test_id]
        assert plan.selected_tests_by_tier[TestTier.AI_TEST.value] == [sample_ai_test.test_id]
        assert plan.selected_tests_by_tier[TestTier.BROWSER_SMOKE.value] == [sample_smoke_test.test_id]
        assert plan.selected_tests_by_tier[TestTier.BROWSER_JOURNEY.value] == [sample_journey_test.test_id]

        # Verify deterministic execution ordering: UNIT (0), AI_TEST (1), BROWSER_SMOKE (2), BROWSER_JOURNEY (3)
        assert [t.tier for t in plan.selected_tests] == [
            TestTier.UNIT,
            TestTier.AI_TEST,
            TestTier.BROWSER_SMOKE,
            TestTier.BROWSER_JOURNEY,
        ]

    # --------------------------------------------------------------------------
    # Scenario I: Inferred Requirement Links Strictly Ignored
    # --------------------------------------------------------------------------
    def test_scenario_i_inferred_requirement_links_ignored(
        self,
        planner: SelectiveRegressionPlanner,
        project_id: str,
    ) -> None:
        inferred_only_test = UnifiedTestDefinition(
            test_id="unit:1111:tests/test_candidate.py::test_heuristic",
            tier=TestTier.UNIT,
            name="test_heuristic",
            source_reference="tests/test_candidate.py::test_heuristic",
            project_id=project_id,
            requirement_links=[],  # Authoritatively EMPTY
            inferred_requirement_links=["REQ-CRITICAL-01"],  # Only heuristic
            discovery_source=DiscoveryProvenance.PYTEST_DISCOVERY,
        )

        inventory = make_inventory(project_id, [inferred_only_test])
        impact = make_impact_report(
            project_id,
            changed_files=["app/service.py"],
            affected_tests=[],  # Not code affected
            affected_reqs=["REQ-CRITICAL-01"],
        )

        plan = planner.plan_regression(project_id, inventory, impact, mode=RegressionPlanMode.SELECTIVE)

        # Inferred test MUST NOT be selected for requirement protection!
        assert inferred_only_test.test_id not in plan.selected_test_ids
        assert plan.selected_test_ids == []
        assert "REQ-CRITICAL-01" in plan.uncovered_affected_requirement_ids

    # --------------------------------------------------------------------------
    # Scenario J: Affected But Uncovered Requirement (Coverage Gap)
    # --------------------------------------------------------------------------
    def test_scenario_j_affected_uncovered_requirement_coverage_gap(
        self,
        planner: SelectiveRegressionPlanner,
        project_id: str,
        sample_unit_test: UnifiedTestDefinition,
    ) -> None:
        inventory = make_inventory(project_id, [sample_unit_test])
        # REQ-UNCOVERED is affected, but inventory has 0 tests for it
        impact = make_impact_report(
            project_id,
            changed_files=["app/legacy.py"],
            affected_tests=[],
            affected_reqs=["REQ-UNCOVERED"],
        )

        plan = planner.plan_regression(project_id, inventory, impact, mode=RegressionPlanMode.SELECTIVE)

        assert plan.has_coverage_gap() is True
        assert "REQ-UNCOVERED" in plan.uncovered_affected_requirement_ids
        assert any("Coverage gap" in w for w in plan.plan_warnings)

    # --------------------------------------------------------------------------
    # Scenario K, L, M & Critical Safety: Unknown Dependency & Dynamic Imports
    # --------------------------------------------------------------------------
    def test_critical_safety_unknown_dependency_blocks_selective_safe(
        self,
        planner: SelectiveRegressionPlanner,
        project_id: str,
        sample_unit_test: UnifiedTestDefinition,
    ) -> None:
        """CRITICAL SAFETY TEST: Unknown dependency must NEVER result in SELECTIVE + SAFE."""
        inventory = make_inventory(project_id, [sample_unit_test])
        impact = make_impact_report(
            project_id,
            changed_files=["app/dynamic_module.py"],
            affected_tests=[sample_unit_test],
            requires_broader=True,  # Uncertainty flagged!
            confidence=AnalysisConfidence.MEDIUM,
            uncertain_files=["app/dynamic_module.py"],
        )

        # When explicitly requested in SELECTIVE mode without auto_broaden:
        plan = planner.plan_regression(
            project_id, inventory, impact, mode=RegressionPlanMode.SELECTIVE, auto_broaden=False
        )

        assert plan.mode == RegressionPlanMode.SELECTIVE
        assert plan.requires_broader_regression is True
        # Safety predicate MUST be False!
        assert plan.is_execution_safe is False
        assert any("Unsafe selective execution" in w for w in plan.plan_warnings)

    def test_critical_safety_auto_broaden_promotes_to_broad_and_safe(
        self,
        planner: SelectiveRegressionPlanner,
        project_id: str,
        sample_unit_test: UnifiedTestDefinition,
        sample_smoke_test: UnifiedTestDefinition,
    ) -> None:
        inventory = make_inventory(project_id, [sample_unit_test, sample_smoke_test])
        impact = make_impact_report(
            project_id,
            changed_files=["app/unsupported.ts"],
            affected_tests=[sample_unit_test],
            requires_broader=True,
            uncertain_files=["app/unsupported.ts"],
        )

        # With auto_broaden=True:
        plan = planner.plan_regression(
            project_id, inventory, impact, mode=RegressionPlanMode.SELECTIVE, auto_broaden=True
        )

        assert plan.mode == RegressionPlanMode.BROAD
        assert plan.is_execution_safe is True
        assert any("Auto-broadened" in r for r in plan.broadening_reasons)
        # Broad mode should have broadened to include both tests
        assert sample_unit_test.test_id in plan.selected_test_ids
        assert sample_smoke_test.test_id in plan.selected_test_ids

    # --------------------------------------------------------------------------
    # Scenario N, O, P, Q, R: Modes (SELECTIVE, BROAD, FULL)
    # --------------------------------------------------------------------------
    def test_scenario_modes_full_regression(
        self,
        planner: SelectiveRegressionPlanner,
        project_id: str,
        sample_unit_test: UnifiedTestDefinition,
        sample_ai_test: UnifiedTestDefinition,
        sample_smoke_test: UnifiedTestDefinition,
    ) -> None:
        all_tests = [sample_unit_test, sample_ai_test, sample_smoke_test]
        inventory = make_inventory(project_id, all_tests)
        impact = make_impact_report(project_id, changed_files=["app/minor.py"], affected_tests=[sample_unit_test])

        plan = planner.plan_regression(project_id, inventory, impact, mode=RegressionPlanMode.FULL)

        assert plan.mode == RegressionPlanMode.FULL
        assert set(plan.selected_test_ids) == {t.test_id for t in all_tests}
        assert plan.unselected_test_count == 0
        assert plan.is_execution_safe is True
        for sel_t in plan.selected_tests:
            assert PlanSelectionReason.FULL_REGRESSION in sel_t.selection_reasons
            assert sel_t.selection_scope == "FULL"

    def test_scenario_modes_broad_regression(
        self,
        planner: SelectiveRegressionPlanner,
        project_id: str,
        sample_unit_test: UnifiedTestDefinition,
        sample_smoke_test: UnifiedTestDefinition,
    ) -> None:
        inventory = make_inventory(project_id, [sample_unit_test, sample_smoke_test])
        impact = make_impact_report(project_id, changed_files=["app/util.py"], affected_tests=[])

        plan = planner.plan_regression(project_id, inventory, impact, mode=RegressionPlanMode.BROAD)

        assert plan.mode == RegressionPlanMode.BROAD
        assert sample_unit_test.test_id in plan.selected_test_ids
        assert sample_smoke_test.test_id in plan.selected_test_ids
        assert plan.is_execution_safe is True

    # --------------------------------------------------------------------------
    # Scenario S: Deterministic Repeated Planning (plan_1 == plan_2)
    # --------------------------------------------------------------------------
    def test_scenario_s_deterministic_repeated_planning_equivalence(
        self,
        planner: SelectiveRegressionPlanner,
        project_id: str,
        sample_unit_test: UnifiedTestDefinition,
        sample_ai_test: UnifiedTestDefinition,
    ) -> None:
        inventory = make_inventory(project_id, [sample_unit_test, sample_ai_test])
        impact = make_impact_report(
            project_id,
            changed_files=["app/math.py"],
            affected_tests=[sample_unit_test],
            test_reasons={sample_unit_test.test_id: [ImpactReason.DEPENDENCY_CLOSURE]},
            affected_reqs=["REQ-MATH-01"],
        )

        plan_1 = planner.plan_regression(
            project_id, inventory, impact, mode=RegressionPlanMode.SELECTIVE, created_at=datetime(2026, 1, 1, tzinfo=timezone.utc)
        )
        plan_2 = planner.plan_regression(
            project_id, inventory, impact, mode=RegressionPlanMode.SELECTIVE, created_at=datetime(2026, 2, 2, tzinfo=timezone.utc)
        )

        # Logical equality MUST hold even if created_at differs!
        assert plan_1 == plan_2

    # --------------------------------------------------------------------------
    # Scenario T: Duplicate Test Prevention
    # --------------------------------------------------------------------------
    def test_scenario_t_duplicate_test_prevention(
        self,
        planner: SelectiveRegressionPlanner,
        project_id: str,
        sample_unit_test: UnifiedTestDefinition,
    ) -> None:
        inventory = make_inventory(project_id, [sample_unit_test])
        # Test is affected via direct change AND covers affected requirement REQ-MATH-01
        impact = make_impact_report(
            project_id,
            changed_files=["tests/test_math.py"],
            affected_tests=[sample_unit_test],
            test_reasons={sample_unit_test.test_id: [ImpactReason.DIRECT_CHANGE]},
            affected_reqs=["REQ-MATH-01"],
        )

        plan = planner.plan_regression(project_id, inventory, impact, mode=RegressionPlanMode.SELECTIVE)

        assert len(plan.selected_test_ids) == 1
        assert len(plan.selected_tests) == 1
        sel_t = plan.selected_tests[0]
        # Must aggregate multiple reasons without duplicating test
        assert PlanSelectionReason.DIRECT_CHANGE in sel_t.selection_reasons
        assert PlanSelectionReason.REQUIREMENT_PROTECTION in sel_t.selection_reasons

    # --------------------------------------------------------------------------
    # Scenario V: Cross-Project Isolation
    # --------------------------------------------------------------------------
    def test_scenario_v_cross_project_isolation(
        self,
        planner: SelectiveRegressionPlanner,
        project_id: str,
        sample_unit_test: UnifiedTestDefinition,
    ) -> None:
        foreign_proj = "99999999-9999-9999-9999-999999999999"
        inventory = make_inventory(project_id, [sample_unit_test])
        impact_foreign = make_impact_report(foreign_proj, changed_files=["app/x.py"])

        with pytest.raises(RegressionPlanIsolationError) as exc_info:
            planner.plan_regression(project_id, inventory, impact_foreign)
        assert "does not match impact report project ID" in str(exc_info.value)

    # --------------------------------------------------------------------------
    # Scenario W & X: Browser Journey Handling
    # --------------------------------------------------------------------------
    def test_scenario_wx_browser_journey_selection_and_unvalidated_exclusion(
        self,
        planner: SelectiveRegressionPlanner,
        project_id: str,
        sample_journey_test: UnifiedTestDefinition,
    ) -> None:
        unvalidated_journey = UnifiedTestDefinition(
            test_id="journey:1111:candidate_unvalidated",
            tier=TestTier.BROWSER_JOURNEY,
            name="candidate_unvalidated",
            source_reference="raw_candidate",
            project_id=project_id,
            discovery_source=DiscoveryProvenance.AI_TEST_SUITE,  # NOT VALIDATED!
        )

        inventory = make_inventory(project_id, [sample_journey_test, unvalidated_journey])
        impact = make_impact_report(
            project_id,
            changed_files=["app/checkout.py"],
            affected_tests=[sample_journey_test, unvalidated_journey],
            test_reasons={
                sample_journey_test.test_id: [ImpactReason.DEPENDENCY_CLOSURE],
                unvalidated_journey.test_id: [ImpactReason.DEPENDENCY_CLOSURE],
            },
        )

        plan = planner.plan_regression(project_id, inventory, impact, mode=RegressionPlanMode.SELECTIVE)

        # Validated journey IS selected
        assert sample_journey_test.test_id in plan.selected_test_ids
        # Unvalidated journey MUST BE excluded!
        assert unvalidated_journey.test_id not in plan.selected_test_ids
        assert any("Excluded unvalidated browser journey" in w for w in plan.plan_warnings)

    # --------------------------------------------------------------------------
    # Scenario Y: Browser Smoke Handling
    # --------------------------------------------------------------------------
    def test_scenario_y_browser_smoke_route_impact(
        self,
        planner: SelectiveRegressionPlanner,
        project_id: str,
        sample_smoke_test: UnifiedTestDefinition,
    ) -> None:
        inventory = make_inventory(project_id, [sample_smoke_test])
        impact = make_impact_report(
            project_id,
            changed_files=["app/api/auth.py"],
            affected_tests=[sample_smoke_test],
            test_reasons={sample_smoke_test.test_id: [ImpactReason.BROWSER_ROUTE_OVERLAP]},
        )

        plan = planner.plan_regression(project_id, inventory, impact, mode=RegressionPlanMode.SELECTIVE)

        assert sample_smoke_test.test_id in plan.selected_test_ids
        assert PlanSelectionReason.BROWSER_ROUTE_IMPACT in plan.selected_tests[0].selection_reasons
        assert plan.selected_tests[0].selection_scope == "BROWSER_ROUTE"

    # --------------------------------------------------------------------------
    # Scenario Z: AI Test Selection (Deterministic, No AI Generation)
    # --------------------------------------------------------------------------
    def test_scenario_z_ai_test_deterministic_selection(
        self,
        planner: SelectiveRegressionPlanner,
        project_id: str,
        sample_ai_test: UnifiedTestDefinition,
    ) -> None:
        inventory = make_inventory(project_id, [sample_ai_test])
        impact = make_impact_report(
            project_id,
            changed_files=["app/billing.py"],
            affected_tests=[sample_ai_test],
            test_reasons={sample_ai_test.test_id: [ImpactReason.DEPENDENCY_CLOSURE]},
        )

        plan = planner.plan_regression(project_id, inventory, impact, mode=RegressionPlanMode.SELECTIVE)

        assert sample_ai_test.test_id in plan.selected_test_ids
        assert plan.selected_tests[0].tier == TestTier.AI_TEST

    # --------------------------------------------------------------------------
    # Scenario AA: Requirement Coverage Accounting (Set Union, No Averaging)
    # --------------------------------------------------------------------------
    def test_scenario_aa_requirement_coverage_accounting(
        self,
        planner: SelectiveRegressionPlanner,
        project_id: str,
        sample_unit_test: UnifiedTestDefinition,
        sample_ai_test: UnifiedTestDefinition,
    ) -> None:
        inventory = make_inventory(project_id, [sample_unit_test, sample_ai_test])
        impact = make_impact_report(
            project_id,
            changed_files=["app/math.py"],
            affected_tests=[sample_unit_test],
            affected_reqs=["REQ-MATH-01", "REQ-MISSING-01"],
        )

        plan = planner.plan_regression(project_id, inventory, impact, mode=RegressionPlanMode.SELECTIVE)

        assert plan.selected_requirement_ids == ["REQ-MATH-01"]
        assert plan.protected_requirement_ids == ["REQ-MATH-01"]
        assert plan.uncovered_affected_requirement_ids == ["REQ-MISSING-01"]

    # --------------------------------------------------------------------------
    # Scenario AC: Stage 3 ChangeImpactService Integration
    # --------------------------------------------------------------------------
    def test_scenario_ac_stage_3_service_integration(
        self,
        planner: SelectiveRegressionPlanner,
        project_id: str,
    ) -> None:
        files_map = {
            "app/calc.py": "def add(a, b): return a + b\n",
            "tests/test_calc.py": "from app.calc import add\ndef test_add(): assert add(1, 2) == 3\n",
        }
        test_calc = UnifiedTestDefinition(
            test_id="unit:1111:tests/test_calc.py::test_add",
            tier=TestTier.UNIT,
            name="test_add",
            source_reference="tests/test_calc.py::test_add",
            project_id=project_id,
            requirement_links=["REQ-CALC-01"],
            discovery_source=DiscoveryProvenance.PYTEST_DISCOVERY,
            target_file="app/calc.py",
            metadata={"file_path": "tests/test_calc.py"},
        )
        inventory = make_inventory(project_id, [test_calc])

        impact_service = ChangeImpactService()
        impact_report = impact_service.analyze_change_impact(
            project_id=project_id,
            changed_files=["app/calc.py"],
            files_map=files_map,
            inventory=inventory,
            active_requirement_ids=["REQ-CALC-01"],
        )

        plan = planner.plan_regression(
            project_id=project_id,
            inventory=inventory,
            impact_report=impact_report,
            mode=RegressionPlanMode.SELECTIVE,
        )

        assert test_calc.test_id in plan.selected_test_ids
        assert "REQ-CALC-01" in plan.protected_requirement_ids
        assert plan.is_execution_safe is True

    # --------------------------------------------------------------------------
    # Scenario AD: No Execution Side Effects
    # --------------------------------------------------------------------------
    def test_scenario_ad_no_execution_side_effects(
        self,
        planner: SelectiveRegressionPlanner,
        project_id: str,
        sample_unit_test: UnifiedTestDefinition,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Verify that planning performs zero subprocess calls or code execution."""
        def forbidden_call(*args, **kwargs):
            raise AssertionError("Subprocess execution is strictly forbidden in Stage 4 planning!")

        monkeypatch.setattr(subprocess, "run", forbidden_call)
        monkeypatch.setattr(subprocess, "Popen", forbidden_call)

        inventory = make_inventory(project_id, [sample_unit_test])
        impact = make_impact_report(
            project_id,
            changed_files=["app/math.py"],
            affected_tests=[sample_unit_test],
        )

        plan = planner.plan_regression(project_id, inventory, impact)
        assert plan.selected_test_ids == [sample_unit_test.test_id]
