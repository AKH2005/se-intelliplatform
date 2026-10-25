"""Deterministic Multi-Tier Coverage Engine (Phase 11L Stage 2).

Computes deterministic, side-effect free requirement-level coverage intelligence
across all four testing tiers (UNIT, AI_TEST, BROWSER_SMOKE, BROWSER_JOURNEY).

Architectural Invariants:
1. Analysis Only: ZERO test execution, ZERO Docker execution, ZERO Playwright calls, ZERO LLMs.
2. Requirement Level: Coverage is strictly calculated against authoritative active requirements.
3. Authoritative Links Only: Uses UnifiedTestDefinition.requirement_links; ignores inferred links.
4. Combined Union: Combined coverage is the set union of covered requirement IDs, NOT percentage averaging.
5. Strict Isolation: Rejects cross-project requirements or tests.
6. Safe Zero Handling: 0 active requirements yields 0.0% coverage deterministically.
"""

from datetime import datetime
import logging
import uuid
from typing import Any, Sequence

from app.models.requirement import Requirement, RequirementStatus
from app.schemas.requirement import RequirementResponse
from app.testing.coverage.contracts import (
    RequirementTraceabilityRecord,
    TierCoverageSummary,
    UnifiedCoverageReport,
)
from app.testing.coverage.errors import (
    UnifiedCoverageIsolationError,
    UnifiedCoverageValidationError,
)
from app.testing.inventory.contracts import TestTier, UnifiedTestInventory

logger = logging.getLogger(__name__)

INACTIVE_STATUSES = {
    RequirementStatus.DEFERRED,
    RequirementStatus.REJECTED,
    "DEFERRED",
    "REJECTED",
}


class UnifiedCoverageEngine:
    """Authoritative deterministic multi-tier requirement coverage calculator."""

    @classmethod
    def compute_coverage(
        cls,
        active_requirements: Sequence[Requirement | RequirementResponse | str] | set[str],
        inventory: UnifiedTestInventory,
        project_id: uuid.UUID | str | None = None,
        calculated_at: datetime | None = None,
    ) -> UnifiedCoverageReport:
        """Calculate deterministic requirement-level coverage across all 4 tiers.
        
        Args:
            active_requirements: Sequence of active requirement strings, Requirement ORM
                                models, or RequirementResponse schemas.
            inventory: Authoritative UnifiedTestInventory from Stage 1.
            project_id: Optional project UUID or string to verify against inventory.
            calculated_at: Optional fixed timestamp for deterministic testing.
            
        Returns:
            UnifiedCoverageReport: Complete multi-tier coverage analysis and gap report.
            
        Raises:
            UnifiedCoverageIsolationError: On cross-project requirement or inventory mismatch.
            UnifiedCoverageValidationError: On invalid input data.
        """
        clean_inv_proj = str(inventory.project_id).strip().lower()

        # 1. Verify Explicit Project ID if passed
        if project_id is not None:
            clean_proj = str(project_id).strip().lower()
            if clean_proj != clean_inv_proj:
                raise UnifiedCoverageIsolationError(
                    f"Specified project_id '{clean_proj}' does not match inventory project_id '{clean_inv_proj}'."
                )

        # 2. Extract and Filter Active Requirements with Strict Project Isolation
        active_ids_set: set[str] = set()

        for item in active_requirements:
            if isinstance(item, (Requirement, RequirementResponse)):
                item_proj = str(item.project_id).strip().lower()
                if item_proj != clean_inv_proj:
                    raise UnifiedCoverageIsolationError(
                        f"Requirement '{item.id}' belongs to project '{item_proj}', "
                        f"violating isolation with inventory project '{clean_inv_proj}'."
                    )

                if getattr(item, "is_archived", False):
                    # Archived requirements are inactive and excluded from active denominator
                    continue

                status_val = item.status.value if hasattr(item.status, "value") else str(item.status)
                if status_val in INACTIVE_STATUSES:
                    # Inactive requirements are excluded from active denominator
                    continue

                active_ids_set.add(str(item.id).strip())
                if hasattr(item, "title") and item.title and item.title.strip():
                    # Also permit code references if tests trace by requirement title
                    active_ids_set.add(item.title.strip())

            elif isinstance(item, str):
                clean_str = item.strip()
                if clean_str:
                    active_ids_set.add(clean_str)

            else:
                raise UnifiedCoverageValidationError(
                    f"Unsupported requirement item type: {type(item).__name__}."
                )

        sorted_active_ids = sorted(list(active_ids_set))
        total_active = len(sorted_active_ids)

        # 3. Defensive Check: Verify all tests in inventory respect project isolation
        for test in inventory.tests:
            test_proj = str(test.project_id).strip().lower()
            if test_proj != clean_inv_proj:
                raise UnifiedCoverageIsolationError(
                    f"Test '{test.test_id}' belongs to project '{test_proj}', "
                    f"violating inventory project '{clean_inv_proj}'."
                )

        # 4. Calculate Tier-Level Coverage for all 4 Tiers
        tier_coverages: dict[str, TierCoverageSummary] = {}
        tier_covered_sets: dict[TestTier, set[str]] = {}

        for tier in TestTier:
            tests_in_tier = inventory.get_tests_by_tier(tier)
            test_ids_by_req: dict[str, list[str]] = {}

            for test in tests_in_tier:
                # Stage 2 Rule: Strictly inspect authoritative requirement_links ONLY.
                # Inferred links MUST NOT contribute to authoritative coverage.
                for req_link in test.requirement_links:
                    clean_req = str(req_link).strip()
                    if clean_req in active_ids_set:
                        if clean_req not in test_ids_by_req:
                            test_ids_by_req[clean_req] = []
                        if test.test_id not in test_ids_by_req[clean_req]:
                            test_ids_by_req[clean_req].append(test.test_id)

            # Sort test IDs deterministically for each requirement
            for req_id in test_ids_by_req:
                test_ids_by_req[req_id].sort()

            # Determine covered and uncovered sets for this tier
            covered_reqs = sorted([r for r in sorted_active_ids if r in test_ids_by_req and len(test_ids_by_req[r]) > 0])
            uncovered_reqs = sorted([r for r in sorted_active_ids if r not in test_ids_by_req or len(test_ids_by_req[r]) == 0])

            covered_count = len(covered_reqs)
            uncovered_count = len(uncovered_reqs)

            if total_active > 0:
                tier_percentage = round((covered_count / total_active) * 100.0, 2)
            else:
                tier_percentage = 0.0

            tier_coverages[tier.value] = TierCoverageSummary(
                tier=tier,
                total_active_requirements=total_active,
                covered_requirement_count=covered_count,
                uncovered_requirement_count=uncovered_count,
                covered_requirement_ids=covered_reqs,
                uncovered_requirement_ids=uncovered_reqs,
                coverage_percentage=tier_percentage,
                test_count=len(tests_in_tier),
                test_ids_by_requirement=test_ids_by_req,
            )
            tier_covered_sets[tier] = set(covered_reqs)

        # 5. Combined Union Calculation Across All 4 Tiers
        combined_covered_set: set[str] = set().union(
            *(tier_covered_sets[tier] for tier in TestTier)
        )
        combined_covered_ids = sorted(list(combined_covered_set))
        combined_covered_count = len(combined_covered_ids)

        # Coverage Gaps: active requirements without any authoritative test in any tier
        combined_uncovered_set = active_ids_set - combined_covered_set
        combined_uncovered_ids = sorted(list(combined_uncovered_set))
        combined_uncovered_count = len(combined_uncovered_ids)

        if total_active > 0:
            combined_percentage = round((combined_covered_count / total_active) * 100.0, 2)
        else:
            combined_percentage = 0.0

        # 6. Detailed Multi-Tier Requirement Traceability Mapping
        requirement_traceability: dict[str, RequirementTraceabilityRecord] = {}

        for req_id in sorted_active_ids:
            covering_tiers: list[TestTier] = []
            tests_by_tier: dict[str, list[str]] = {}

            for tier in TestTier:
                t_summary = tier_coverages[tier.value]
                if req_id in t_summary.test_ids_by_requirement:
                    tids = t_summary.test_ids_by_requirement[req_id]
                    if tids:
                        covering_tiers.append(tier)
                        tests_by_tier[tier.value] = list(tids)

            is_covered = len(covering_tiers) > 0
            total_tests_for_req = sum(len(tids) for tids in tests_by_tier.values())

            requirement_traceability[req_id] = RequirementTraceabilityRecord(
                requirement_id=req_id,
                is_covered=is_covered,
                covering_tiers=covering_tiers,
                tests_by_tier=tests_by_tier,
                total_tests=total_tests_for_req,
            )

        # 7. Construct Report
        report_kwargs: dict[str, Any] = {
            "project_id": clean_inv_proj,
            "total_active_requirements": total_active,
            "active_requirement_ids": sorted_active_ids,
            "tier_coverages": tier_coverages,
            "combined_covered_requirement_ids": combined_covered_ids,
            "combined_covered_count": combined_covered_count,
            "combined_uncovered_requirement_ids": combined_uncovered_ids,
            "combined_uncovered_count": combined_uncovered_count,
            "combined_coverage_percentage": combined_percentage,
            "requirement_traceability": requirement_traceability,
            "metadata": {
                "active_denominator": total_active,
                "gap_count": combined_uncovered_count,
                "tiers_analyzed": [tier.value for tier in TestTier],
            },
        }
        if calculated_at is not None:
            report_kwargs["calculated_at"] = calculated_at

        return UnifiedCoverageReport(**report_kwargs)
