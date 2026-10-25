"""Deterministic Regression Plan Validator (Phase 11L Stage 4).

Validates regression plan integrity, test provenance, tier classification,
strict project isolation, validated browser journeys, and conservative safety invariants.
"""

import logging
from typing import Any

from app.testing.inventory.contracts import (
    DiscoveryProvenance,
    TestTier,
    UnifiedTestInventory,
)
from app.testing.regression.contracts import (
    RegressionPlan,
    RegressionPlanMode,
)
from app.testing.regression.errors import (
    RegressionPlanIsolationError,
    RegressionPlanValidationError,
)

logger = logging.getLogger(__name__)


class RegressionPlanValidator:
    """Authoritative validator verifying structural and safety invariants of a RegressionPlan."""

    def validate(
        self,
        plan: RegressionPlan,
        inventory: UnifiedTestInventory,
    ) -> None:
        """Deterministically validate a RegressionPlan against its source UnifiedTestInventory.

        Args:
            plan: The RegressionPlan to validate.
            inventory: The authoritative source UnifiedTestInventory.

        Raises:
            RegressionPlanIsolationError: On project ID mismatch or cross-project contamination.
            RegressionPlanValidationError: On structural, tier, journey, duplicate, or safety violations.
        """
        clean_plan_proj = str(plan.project_id).strip().lower()
        clean_inv_proj = str(inventory.project_id).strip().lower()

        # 1. Project Isolation Verification
        if clean_plan_proj != clean_inv_proj:
            raise RegressionPlanIsolationError(
                f"Plan project ID '{clean_plan_proj}' does not match inventory project ID '{clean_inv_proj}'."
            )

        # 2. Duplicate Detection
        if len(plan.selected_test_ids) != len(set(plan.selected_test_ids)):
            raise RegressionPlanValidationError(
                "Duplicate test IDs detected in plan.selected_test_ids."
            )

        selected_model_ids = [t.test_id for t in plan.selected_tests]
        if len(selected_model_ids) != len(set(selected_model_ids)):
            raise RegressionPlanValidationError(
                "Duplicate tests detected in plan.selected_tests."
            )

        if set(plan.selected_test_ids) != set(selected_model_ids):
            raise RegressionPlanValidationError(
                "Mismatch between plan.selected_test_ids and plan.selected_tests IDs."
            )

        # 3. Test Existence and Provenance Verification
        for sel_test in plan.selected_tests:
            inv_def = inventory.get_test(sel_test.test_id)
            if inv_def is None:
                raise RegressionPlanValidationError(
                    f"Plan contains unknown test ID '{sel_test.test_id}' not found in UnifiedTestInventory."
                )

            inv_test_proj = str(inv_def.project_id).strip().lower()
            if inv_test_proj != clean_plan_proj:
                raise RegressionPlanIsolationError(
                    f"Selected test '{sel_test.test_id}' belongs to project '{inv_test_proj}', "
                    f"violating isolation with plan project '{clean_plan_proj}'."
                )

            # 4. Test Tier Verification
            if not isinstance(sel_test.tier, TestTier):
                raise RegressionPlanValidationError(
                    f"Test '{sel_test.test_id}' has invalid tier '{sel_test.tier}'."
                )
            if sel_test.tier != inv_def.tier:
                raise RegressionPlanValidationError(
                    f"Test '{sel_test.test_id}' tier '{sel_test.tier}' disagrees with inventory tier '{inv_def.tier}'."
                )

            # 5. Browser Journey Safety: Only Validated Journeys Allowed
            if sel_test.tier == TestTier.BROWSER_JOURNEY:
                if inv_def.discovery_source != DiscoveryProvenance.VALIDATED_BROWSER_JOURNEY:
                    raise RegressionPlanValidationError(
                        f"Unvalidated browser journey candidate '{sel_test.test_id}' cannot enter regression plan. "
                        f"Discovery source is '{inv_def.discovery_source}'."
                    )
                if inv_def.metadata.get("is_validated") is False:
                    raise RegressionPlanValidationError(
                        f"Browser journey '{sel_test.test_id}' is explicitly marked as unvalidated in metadata."
                    )

        # 6. Tier Index Consistency Check
        for tier_key, test_ids in plan.selected_tests_by_tier.items():
            valid_tiers = {t.value for t in TestTier}
            if tier_key not in valid_tiers:
                raise RegressionPlanValidationError(
                    f"Invalid tier key '{tier_key}' in selected_tests_by_tier."
                )
            for tid in test_ids:
                if tid not in plan.selected_test_ids:
                    raise RegressionPlanValidationError(
                        f"Test ID '{tid}' in selected_tests_by_tier['{tier_key}'] is not in selected_test_ids."
                    )

        # 7. Requirement ID Formatting Verification
        for req_list_name, req_list in [
            ("selected_requirement_ids", plan.selected_requirement_ids),
            ("affected_requirement_ids", plan.affected_requirement_ids),
            ("protected_requirement_ids", plan.protected_requirement_ids),
            ("uncovered_affected_requirement_ids", plan.uncovered_affected_requirement_ids),
        ]:
            for rid in req_list:
                if not rid or not str(rid).strip():
                    raise RegressionPlanValidationError(
                        f"Malformed empty requirement ID in plan.{req_list_name}."
                    )

        # 8. Conservative Safety Invariant
        # UNKNOWN / UNCERTAIN must NEVER result in SELECTIVE + SAFE
        if plan.requires_broader_regression and plan.mode == RegressionPlanMode.SELECTIVE:
            if plan.is_execution_safe:
                raise RegressionPlanValidationError(
                    "Conservative safety invariant violated: plan is marked is_execution_safe=True "
                    "in SELECTIVE mode when requires_broader_regression is True."
                )

        # 9. Inventory Count Consistency
        if plan.total_inventory_tests != inventory.total_tests:
            raise RegressionPlanValidationError(
                f"total_inventory_tests ({plan.total_inventory_tests}) does not match "
                f"inventory.total_tests ({inventory.total_tests})."
            )

        expected_unselected = inventory.total_tests - len(plan.selected_test_ids)
        if plan.unselected_test_count != expected_unselected:
            raise RegressionPlanValidationError(
                f"unselected_test_count ({plan.unselected_test_count}) does not equal "
                f"expected unselected count ({expected_unselected})."
            )
