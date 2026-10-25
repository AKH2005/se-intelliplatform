"""Deterministic Requirement Coverage Engine for Browser Journeys.

Phase 11K — Stage 2: Requirement Coverage Engine
Computes deterministic coverage metrics, bidirectional traceability mappings,
and uncovered requirement sets strictly from validated browser journeys.

ARCHITECTURAL INVARIANTS:
1. Pure Deterministic Calculation: Coverage calculations are executed entirely in Python
   backend code; no LLMs or probabilistic heuristics are used.
2. Authoritative Denominator: Denominator is strictly the count of authoritative active
   requirements from canonical project context.
3. Validated Inputs Only: Only authoritatively verified journeys and valid active requirement
   references contribute to coverage.
4. Safe Zero Handling: When total active requirements is 0, coverage percentage is deterministically 0.0.
"""

from typing import Sequence
from app.browser.journey.contracts import (
    RequirementCoverageReport,
    ValidatedBrowserJourney,
)


class RequirementCoverageEngine:
    """Authoritative deterministic requirement coverage calculator."""

    @classmethod
    def compute_coverage(
        cls,
        validated_journeys: Sequence[ValidatedBrowserJourney],
        active_requirement_ids: Sequence[str] | set[str],
    ) -> RequirementCoverageReport:
        """Compute authoritative requirement coverage from validated journeys.
        
        Args:
            validated_journeys: List of authoritatively validated user journeys.
            active_requirement_ids: Authoritative active project requirement IDs.
            
        Returns:
            Strongly typed RequirementCoverageReport with exact counts and percentages.
        """
        active_set: set[str] = {str(rid).strip() for rid in active_requirement_ids if str(rid).strip()}
        total_active: int = len(active_set)

        # Build bidirectional traceability maps
        req_to_journeys: dict[str, list[str]] = {}
        journey_to_reqs: dict[str, list[str]] = {}

        for journey in validated_journeys:
            valid_for_journey: set[str] = set()
            for req_id in journey.validated_requirement_ids:
                clean_id = str(req_id).strip()
                if clean_id in active_set:
                    valid_for_journey.add(clean_id)
                    if clean_id not in req_to_journeys:
                        req_to_journeys[clean_id] = []
                    if journey.journey_id not in req_to_journeys[clean_id]:
                        req_to_journeys[clean_id].append(journey.journey_id)

            journey_to_reqs[journey.journey_id] = sorted(list(valid_for_journey))

        # Calculate covered and uncovered sets
        covered_ids: list[str] = sorted(
            [rid for rid in active_set if rid in req_to_journeys and len(req_to_journeys[rid]) > 0]
        )
        uncovered_ids: list[str] = sorted(
            [rid for rid in active_set if rid not in req_to_journeys or len(req_to_journeys[rid]) == 0]
        )

        covered_count: int = len(covered_ids)
        uncovered_count: int = len(uncovered_ids)

        if total_active > 0:
            coverage_percentage: float = round((covered_count / total_active) * 100.0, 2)
        else:
            coverage_percentage = 0.0

        return RequirementCoverageReport(
            total_active_requirements=total_active,
            covered_requirement_count=covered_count,
            uncovered_requirement_count=uncovered_count,
            covered_requirement_ids=covered_ids,
            uncovered_requirement_ids=uncovered_ids,
            coverage_percentage=coverage_percentage,
            journey_count=len(validated_journeys),
            requirement_to_journeys_map=req_to_journeys,
            journey_to_requirements_map=journey_to_reqs,
        )
