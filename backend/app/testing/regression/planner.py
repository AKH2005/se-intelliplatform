"""Deterministic Selective Regression Planner (Phase 11L Stage 4).

Generates strongly-typed, validated regression plans from Stage 3 ChangeImpactReport,
Stage 2 UnifiedCoverageReport, and Stage 1 UnifiedTestInventory.

Architectural Invariants:
1. Plans Only: ZERO test execution, ZERO Docker containers, ZERO Playwright sessions, ZERO LLM calls.
2. Conservative Safety: UNKNOWN / UNCERTAIN never results in unsafe under-selection.
3. Strict Determinism: Sorted test lists, stable tier order, reproducible plan equality.
4. Authoritative Requirement Links: Only authoritative requirement_links used for requirement protection.
5. Multi-Tier Support: Preserves UNIT, AI_TEST, BROWSER_SMOKE, and BROWSER_JOURNEY tiers.
6. Safe Browser Journeys: Only validated browser journeys are eligible for selection.
7. Strict Project Isolation: Enforces project boundaries across all inputs.
"""

from datetime import datetime, timezone
import logging
from typing import Any, Sequence
import uuid

from app.testing.coverage.contracts import UnifiedCoverageReport
from app.testing.impact.contracts import (
    AnalysisConfidence,
    ChangeImpactReport,
    ImpactReason,
)
from app.testing.inventory.contracts import (
    DiscoveryProvenance,
    TestTier,
    UnifiedTestDefinition,
    UnifiedTestInventory,
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

logger = logging.getLogger(__name__)

# Deterministic Tier Execution Order
TIER_EXECUTION_ORDER: dict[TestTier, int] = {
    TestTier.UNIT: 0,
    TestTier.AI_TEST: 1,
    TestTier.BROWSER_SMOKE: 2,
    TestTier.BROWSER_JOURNEY: 3,
}


class SelectiveRegressionPlanner:
    """Authoritative service for generating deterministic regression plans."""

    def __init__(self, validator: RegressionPlanValidator | None = None) -> None:
        self.validator = validator or RegressionPlanValidator()

    def plan_regression(
        self,
        project_id: uuid.UUID | str,
        inventory: UnifiedTestInventory,
        impact_report: ChangeImpactReport,
        coverage_report: UnifiedCoverageReport | None = None,
        mode: RegressionPlanMode = RegressionPlanMode.SELECTIVE,
        auto_broaden: bool = False,
        base_version_id: str | None = None,
        target_version_id: str | None = None,
        created_at: datetime | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> RegressionPlan:
        """Create a deterministic, validated RegressionPlan.

        Args:
            project_id: Canonical project UUID or string.
            inventory: Authoritative UnifiedTestInventory from Stage 1.
            impact_report: Authoritative ChangeImpactReport from Stage 3.
            coverage_report: Optional UnifiedCoverageReport from Stage 2.
            mode: Requested execution scope (SELECTIVE, BROAD, FULL).
            auto_broaden: If True, automatically promotes SELECTIVE to BROAD when uncertainty exists.
            base_version_id: Optional base version ID.
            target_version_id: Optional target version ID.
            created_at: Optional fixed timestamp for deterministic testing.
            metadata: Optional telemetry or contextual metadata.

        Returns:
            RegressionPlan: Fully validated, deterministic regression plan.

        Raises:
            RegressionPlanIsolationError: On project boundary violation.
            RegressionPlanValidationError: On invalid test definitions, tiers, journeys, or safety violations.
        """
        clean_proj = str(project_id).strip().lower()
        inv_proj = str(inventory.project_id).strip().lower()
        impact_proj = str(impact_report.project_id).strip().lower()

        # 1. Enforce Project Isolation Across All Inputs
        if clean_proj != inv_proj:
            raise RegressionPlanIsolationError(
                f"Project ID '{clean_proj}' does not match inventory project ID '{inv_proj}'."
            )
        if clean_proj != impact_proj:
            raise RegressionPlanIsolationError(
                f"Project ID '{clean_proj}' does not match impact report project ID '{impact_proj}'."
            )
        if coverage_report is not None:
            cov_proj = str(coverage_report.project_id).strip().lower()
            if clean_proj != cov_proj:
                raise RegressionPlanIsolationError(
                    f"Project ID '{clean_proj}' does not match coverage report project ID '{cov_proj}'."
                )

        # 2. Determine Effective Plan Mode and Broadening Rationale
        active_mode = mode
        broadening_reasons: list[str] = []
        plan_warnings: list[str] = []

        if impact_report.requires_broader_regression:
            if auto_broaden and active_mode == RegressionPlanMode.SELECTIVE:
                active_mode = RegressionPlanMode.BROAD
                broadening_reasons.append(
                    "Auto-broadened from SELECTIVE to BROAD due to uncertainty in change impact."
                )
            elif active_mode == RegressionPlanMode.BROAD:
                broadening_reasons.append(
                    "Conservative broadening active: uncertainty detected in dependency impact."
                )
            elif active_mode == RegressionPlanMode.SELECTIVE:
                plan_warnings.append(
                    "Unsafe selective execution: change impact flagged uncertainty requiring broader regression."
                )

        if active_mode == RegressionPlanMode.BROAD and not broadening_reasons:
            broadening_reasons.append("BROAD mode explicitly requested.")
        elif active_mode == RegressionPlanMode.FULL:
            broadening_reasons.append("FULL regression mode: all valid inventory tests selected.")

        # 3. Test Candidate Selection Map: test_id -> candidate data dict
        candidates: dict[str, dict[str, Any]] = {}

        if active_mode == RegressionPlanMode.FULL:
            # Full Regression: select all valid tests from inventory
            for inv_test in inventory.tests:
                if inv_test.tier == TestTier.BROWSER_JOURNEY:
                    if (
                        inv_test.discovery_source != DiscoveryProvenance.VALIDATED_BROWSER_JOURNEY
                        or inv_test.metadata.get("is_validated") is False
                    ):
                        plan_warnings.append(
                            f"Excluded unvalidated browser journey '{inv_test.test_id}' from full regression."
                        )
                        continue

                aff_reqs = set(inv_test.requirement_links) & set(impact_report.affected_requirements)
                candidates[inv_test.test_id] = {
                    "test_def": inv_test,
                    "reasons": {PlanSelectionReason.FULL_REGRESSION},
                    "affected_requirements": aff_reqs,
                    "affected_files": set(),
                    "selection_scope": "FULL",
                }
        else:
            # SELECTIVE or BROAD Regression

            # A. Process Stage 3 Impacted Tests
            for affected_t in impact_report.affected_tests:
                inv_test = inventory.get_test(affected_t.test_id)
                if inv_test is None:
                    continue

                # Browser Journey Safety Invariant
                if inv_test.tier == TestTier.BROWSER_JOURNEY:
                    if (
                        inv_test.discovery_source != DiscoveryProvenance.VALIDATED_BROWSER_JOURNEY
                        or inv_test.metadata.get("is_validated") is False
                    ):
                        plan_warnings.append(
                            f"Excluded unvalidated browser journey candidate '{inv_test.test_id}'."
                        )
                        continue

                impact_reasons = impact_report.get_reasons_for_test(inv_test.test_id)
                plan_reasons: set[PlanSelectionReason] = set()
                scope = "DEPENDENCY"

                if any(r in (ImpactReason.DIRECT_CHANGE, ImpactReason.DIRECT_TEST_FILE) for r in impact_reasons):
                    plan_reasons.add(PlanSelectionReason.DIRECT_CHANGE)
                    scope = "DIRECT"
                if ImpactReason.DEPENDENCY_CLOSURE in impact_reasons:
                    plan_reasons.add(PlanSelectionReason.DEPENDENCY_IMPACT)
                if ImpactReason.BROWSER_ROUTE_OVERLAP in impact_reasons:
                    plan_reasons.add(PlanSelectionReason.BROWSER_ROUTE_IMPACT)
                    scope = "BROWSER_ROUTE"
                if ImpactReason.UNKNOWN_DEPENDENCY in impact_reasons:
                    plan_reasons.add(PlanSelectionReason.CONSERVATIVE_FALLBACK)
                    scope = "CONSERVATIVE"
                if ImpactReason.AUTHORITATIVE_REQUIREMENT_LINK in impact_reasons:
                    plan_reasons.add(PlanSelectionReason.REQUIREMENT_PROTECTION)

                if not plan_reasons:
                    plan_reasons.add(PlanSelectionReason.DEPENDENCY_IMPACT)

                aff_files: set[str] = set()
                t_file = inv_test.metadata.get("file_path") or inv_test.target_file
                if t_file and t_file in impact_report.all_affected_files:
                    aff_files.add(t_file)

                aff_reqs = set(inv_test.requirement_links) & set(impact_report.affected_requirements)

                candidates[inv_test.test_id] = {
                    "test_def": inv_test,
                    "reasons": plan_reasons,
                    "affected_requirements": aff_reqs,
                    "affected_files": aff_files,
                    "selection_scope": scope,
                }

            # B. Requirement Protection
            # For each affected requirement, select all authoritative tests protecting it
            for req_id in impact_report.affected_requirements:
                clean_req = str(req_id).strip()
                protecting_tests = inventory.get_tests_for_requirement(clean_req)
                for inv_test in protecting_tests:
                    if inv_test.tier == TestTier.BROWSER_JOURNEY:
                        if (
                            inv_test.discovery_source != DiscoveryProvenance.VALIDATED_BROWSER_JOURNEY
                            or inv_test.metadata.get("is_validated") is False
                        ):
                            continue

                    if inv_test.test_id not in candidates:
                        candidates[inv_test.test_id] = {
                            "test_def": inv_test,
                            "reasons": {PlanSelectionReason.REQUIREMENT_PROTECTION},
                            "affected_requirements": {clean_req},
                            "affected_files": set(),
                            "selection_scope": "REQUIREMENT",
                        }
                    else:
                        candidates[inv_test.test_id]["reasons"].add(PlanSelectionReason.REQUIREMENT_PROTECTION)
                        candidates[inv_test.test_id]["affected_requirements"].add(clean_req)

            # C. Conservative Broadening (BROAD mode)
            if active_mode == RegressionPlanMode.BROAD:
                for inv_test in inventory.tests:
                    if inv_test.tier == TestTier.BROWSER_JOURNEY:
                        if (
                            inv_test.discovery_source != DiscoveryProvenance.VALIDATED_BROWSER_JOURNEY
                            or inv_test.metadata.get("is_validated") is False
                        ):
                            continue

                    # In BROAD mode, include all UNIT and BROWSER_SMOKE tests as safety perimeter
                    if inv_test.tier in (TestTier.UNIT, TestTier.BROWSER_SMOKE):
                        aff_reqs = set(inv_test.requirement_links) & set(impact_report.affected_requirements)
                        if inv_test.test_id not in candidates:
                            candidates[inv_test.test_id] = {
                                "test_def": inv_test,
                                "reasons": {PlanSelectionReason.BROAD_REGRESSION},
                                "affected_requirements": aff_reqs,
                                "affected_files": set(),
                                "selection_scope": "BROADENING",
                            }
                        else:
                            candidates[inv_test.test_id]["reasons"].add(PlanSelectionReason.BROAD_REGRESSION)

        # 4. Deterministic Ordering of Selected Tests
        # Stable sort: primary key is Tier execution order, secondary key is test_id
        ordered_candidates = sorted(
            candidates.values(),
            key=lambda c: (
                TIER_EXECUTION_ORDER.get(c["test_def"].tier, 99),
                c["test_def"].test_id,
            ),
        )

        selected_tests: list[SelectedTest] = []
        selected_tests_by_tier: dict[str, list[str]] = {t.value: [] for t in TestTier}
        selection_reasons_by_test: dict[str, list[PlanSelectionReason]] = {}

        for cand in ordered_candidates:
            t_def: UnifiedTestDefinition = cand["test_def"]
            reasons_sorted = sorted(list(cand["reasons"]), key=lambda r: r.value)
            aff_reqs_sorted = sorted(list(cand["affected_requirements"]))
            aff_files_sorted = sorted(list(cand["affected_files"]))

            sel_test = SelectedTest(
                test_id=t_def.test_id,
                tier=t_def.tier,
                name=t_def.name,
                source_reference=t_def.source_reference,
                selection_reasons=reasons_sorted,
                affected_requirements=aff_reqs_sorted,
                affected_files=aff_files_sorted,
                selection_scope=cand["selection_scope"],
                target_file=t_def.target_file,
                target_symbol=t_def.target_symbol,
            )
            selected_tests.append(sel_test)
            selected_tests_by_tier[t_def.tier.value].append(t_def.test_id)
            selection_reasons_by_test[t_def.test_id] = reasons_sorted

        # Ensure tier lists are sorted
        for t_val in selected_tests_by_tier:
            selected_tests_by_tier[t_val].sort()

        selected_test_ids = sorted([t.test_id for t in selected_tests])

        # 5. Requirement Coverage Accounting (Set Union, Zero Tier Averaging)
        all_linked_reqs: set[str] = set()
        for sel_test in selected_tests:
            t_def = inventory.get_test(sel_test.test_id)
            if t_def:
                for r in t_def.requirement_links:
                    clean_r = str(r).strip()
                    if clean_r:
                        all_linked_reqs.add(clean_r)

        selected_requirement_ids = sorted(list(all_linked_reqs))
        affected_requirement_ids = sorted(list(set(impact_report.affected_requirements)))

        # Protected requirements = affected requirements covered by selected tests
        protected_reqs_set = set(affected_requirement_ids) & all_linked_reqs
        protected_requirement_ids = sorted(list(protected_reqs_set))

        # Coverage gap: affected requirements with zero selected tests protecting them
        uncovered_affected_set = set(affected_requirement_ids) - protected_reqs_set
        uncovered_affected_requirement_ids = sorted(list(uncovered_affected_set))

        if uncovered_affected_requirement_ids:
            plan_warnings.append(
                f"Coverage gap: affected requirements {uncovered_affected_requirement_ids} "
                f"have no authoritative test protection in inventory."
            )

        # Unrelated requirements: active requirements neither affected nor selected
        unrelated_requirement_ids: list[str] = []
        if coverage_report is not None:
            active_set = set(coverage_report.active_requirement_ids)
            unrelated_set = active_set - set(affected_requirement_ids) - set(selected_requirement_ids)
            unrelated_requirement_ids = sorted(list(unrelated_set))

        # 6. Deterministic Safety Evaluation
        # UNKNOWN / UNCERTAIN must NEVER result in SELECTIVE + SAFE
        if active_mode == RegressionPlanMode.FULL:
            is_execution_safe = True
        elif active_mode == RegressionPlanMode.BROAD:
            is_execution_safe = True
        else:
            # SELECTIVE mode
            if impact_report.requires_broader_regression:
                is_execution_safe = False
            elif impact_report.analysis_confidence == AnalysisConfidence.LOW:
                is_execution_safe = False
                plan_warnings.append("Unsafe selective execution: analysis confidence is LOW.")
            else:
                is_execution_safe = True

        # 7. Construct RegressionPlan
        clean_warnings = sorted(list(set(plan_warnings)))
        clean_broadening_reasons = sorted(list(set(broadening_reasons)))

        plan = RegressionPlan(
            project_id=clean_proj,
            mode=active_mode,
            base_version_id=base_version_id,
            target_version_id=target_version_id,
            inventory_id=inventory.inventory_id,
            selected_test_ids=selected_test_ids,
            selected_tests=selected_tests,
            selected_tests_by_tier=selected_tests_by_tier,
            selected_requirement_ids=selected_requirement_ids,
            affected_requirement_ids=affected_requirement_ids,
            protected_requirement_ids=protected_requirement_ids,
            uncovered_affected_requirement_ids=uncovered_affected_requirement_ids,
            unrelated_requirement_ids=unrelated_requirement_ids,
            selection_reasons_by_test=selection_reasons_by_test,
            broadening_reasons=clean_broadening_reasons,
            requires_broader_regression=impact_report.requires_broader_regression,
            is_execution_safe=is_execution_safe,
            plan_warnings=clean_warnings,
            total_inventory_tests=inventory.total_tests,
            unselected_test_count=inventory.total_tests - len(selected_test_ids),
            created_at=created_at or datetime.now(timezone.utc),
            metadata=metadata or {},
        )

        # 8. Deterministic Validation
        self.validator.validate(plan, inventory)

        return plan
