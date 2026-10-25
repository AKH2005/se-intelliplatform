"""Unit Tests for UnifiedCoverageEngine (Phase 11L Stage 2).

Validates:
1. Multi-tier coverage calculation across UNIT, AI_TEST, BROWSER_SMOKE, BROWSER_JOURNEY.
2. Requirement-level set union calculation (distinguished from percentage averaging).
3. Authoritative vs. inferred requirement link separation.
4. Active vs. inactive requirement filtering (DRAFT/APPROVED/IMPLEMENTED vs DEFERRED/REJECTED).
5. Safe zero active requirement handling.
6. Project isolation enforcement and deterministic repeated calculation.
"""

from datetime import datetime, timezone
import uuid
import pytest

from app.models.requirement import RequirementStatus
from app.schemas.requirement import RequirementResponse
from app.testing.coverage.contracts import UnifiedCoverageReport
from app.testing.coverage.engine import UnifiedCoverageEngine
from app.testing.coverage.errors import (
    UnifiedCoverageIsolationError,
    UnifiedCoverageValidationError,
)
from app.testing.inventory.contracts import (
    DiscoveryProvenance,
    DiscoveryStatus,
    TestTier,
    UnifiedTestDefinition,
    UnifiedTestInventory,
    compute_deterministic_inventory_id,
)


# ==============================================================================
# Helper to construct minimal UnifiedTestInventory
# ==============================================================================

def make_test_inventory(project_id: str, tests: list[UnifiedTestDefinition]) -> UnifiedTestInventory:
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


# ==============================================================================
# Test Suite
# ==============================================================================

class TestUnifiedCoverageEngine:
    """Comprehensive test suite for UnifiedCoverageEngine."""

    def test_critical_requirement_level_union_calculation(self) -> None:
        """CRITICAL TEST: Verify combined coverage is the set union of covered requirement IDs,

        NOT an arithmetic average of tier percentages.

        Scenario:
          Active requirements: REQ-1, REQ-2, REQ-3, REQ-4 (Total N = 4)
          UNIT covers: REQ-1, REQ-2 (2/4 = 50.0%)
          AI_TEST covers: REQ-2, REQ-3 (2/4 = 50.0%)
          BROWSER_SMOKE covers: REQ-3 (1/4 = 25.0%)
          BROWSER_JOURNEY covers: REQ-4 (1/4 = 25.0%)

          Average of tier percentages would be: (50 + 50 + 25 + 25) / 4 = 37.5% (WRONG!)
          Authoritative Union of requirement IDs: {REQ-1, REQ-2, REQ-3, REQ-4} (4/4 = 100.0%!)
        """
        proj_id = "00000000-0000-0000-0000-000000000001"
        active_reqs = ["REQ-1", "REQ-2", "REQ-3", "REQ-4"]

        t_unit = UnifiedTestDefinition(
            test_id=f"unit:{proj_id}:t_unit",
            tier=TestTier.UNIT,
            name="test_unit",
            source_reference="tests/test_unit.py",
            project_id=proj_id,
            requirement_links=["REQ-1", "REQ-2"],
            discovery_source=DiscoveryProvenance.PYTEST_DISCOVERY,
        )
        t_ai = UnifiedTestDefinition(
            test_id=f"ai_test:{proj_id}:t_ai",
            tier=TestTier.AI_TEST,
            name="test_ai",
            source_reference="tests/test_ai.py",
            project_id=proj_id,
            requirement_links=["REQ-2", "REQ-3"],
            discovery_source=DiscoveryProvenance.AI_TEST_SUITE,
        )
        t_smoke = UnifiedTestDefinition(
            test_id=f"browser_smoke:{proj_id}:t_smoke",
            tier=TestTier.BROWSER_SMOKE,
            name="test_smoke",
            source_reference="/",
            project_id=proj_id,
            requirement_links=["REQ-3"],
            discovery_source=DiscoveryProvenance.BROWSER_SMOKE_SUITE,
        )
        t_journey = UnifiedTestDefinition(
            test_id=f"browser_journey:{proj_id}:t_journey",
            tier=TestTier.BROWSER_JOURNEY,
            name="test_journey",
            source_reference="/dashboard",
            project_id=proj_id,
            requirement_links=["REQ-4"],
            discovery_source=DiscoveryProvenance.VALIDATED_BROWSER_JOURNEY,
        )

        inventory = make_test_inventory(proj_id, [t_unit, t_ai, t_smoke, t_journey])
        report = UnifiedCoverageEngine.compute_coverage(active_reqs, inventory)

        assert report.total_active_requirements == 4
        assert report.active_requirement_ids == ["REQ-1", "REQ-2", "REQ-3", "REQ-4"]

        # Verify individual tier percentages
        unit_summary = report.get_tier_coverage(TestTier.UNIT)
        assert unit_summary is not None
        assert unit_summary.coverage_percentage == 50.0
        assert unit_summary.covered_requirement_ids == ["REQ-1", "REQ-2"]

        ai_summary = report.get_tier_coverage(TestTier.AI_TEST)
        assert ai_summary is not None
        assert ai_summary.coverage_percentage == 50.0
        assert ai_summary.covered_requirement_ids == ["REQ-2", "REQ-3"]

        smoke_summary = report.get_tier_coverage(TestTier.BROWSER_SMOKE)
        assert smoke_summary is not None
        assert smoke_summary.coverage_percentage == 25.0
        assert smoke_summary.covered_requirement_ids == ["REQ-3"]

        journey_summary = report.get_tier_coverage(TestTier.BROWSER_JOURNEY)
        assert journey_summary is not None
        assert journey_summary.coverage_percentage == 25.0
        assert journey_summary.covered_requirement_ids == ["REQ-4"]

        # CRITICAL ASSERTION: Combined coverage MUST be 100.0%, NOT 37.5%
        assert report.combined_covered_requirement_ids == ["REQ-1", "REQ-2", "REQ-3", "REQ-4"]
        assert report.combined_covered_count == 4
        assert report.combined_uncovered_requirement_ids == []
        assert report.combined_uncovered_count == 0
        assert report.combined_coverage_percentage == 100.0

    def test_single_tier_coverage_modes(self) -> None:
        """Verify single tier coverage calculates accurately across all 4 tiers."""
        proj_id = "proj-single-tier"
        active_reqs = ["REQ-A", "REQ-B"]

        # 1. Unit only
        t_unit = UnifiedTestDefinition(
            test_id="unit:proj:t1",
            tier=TestTier.UNIT,
            name="test_1",
            source_reference="tests/test_1.py",
            project_id=proj_id,
            requirement_links=["REQ-A"],
            discovery_source=DiscoveryProvenance.PYTEST_DISCOVERY,
        )
        inv = make_test_inventory(proj_id, [t_unit])
        report = UnifiedCoverageEngine.compute_coverage(active_reqs, inv)

        assert report.tier_coverages["UNIT"].coverage_percentage == 50.0
        assert report.tier_coverages["AI_TEST"].coverage_percentage == 0.0
        assert report.tier_coverages["BROWSER_SMOKE"].coverage_percentage == 0.0
        assert report.tier_coverages["BROWSER_JOURNEY"].coverage_percentage == 0.0
        assert report.combined_coverage_percentage == 50.0
        assert report.get_coverage_gaps() == ["REQ-B"]

    def test_coverage_gaps_detection(self) -> None:
        """Verify uncovered active requirements are identified as coverage gaps."""
        proj_id = "proj-gaps"
        active_reqs = ["REQ-1", "REQ-2", "REQ-3", "REQ-4", "REQ-5"]

        t_unit = UnifiedTestDefinition(
            test_id="unit:proj:t1",
            tier=TestTier.UNIT,
            name="test_1",
            source_reference="tests/test_1.py",
            project_id=proj_id,
            requirement_links=["REQ-1"],
            discovery_source=DiscoveryProvenance.PYTEST_DISCOVERY,
        )
        t_journey = UnifiedTestDefinition(
            test_id="browser_journey:proj:t2",
            tier=TestTier.BROWSER_JOURNEY,
            name="test_2",
            source_reference="/flow",
            project_id=proj_id,
            requirement_links=["REQ-3"],
            discovery_source=DiscoveryProvenance.VALIDATED_BROWSER_JOURNEY,
        )
        inv = make_test_inventory(proj_id, [t_unit, t_journey])
        report = UnifiedCoverageEngine.compute_coverage(active_reqs, inv)

        assert report.combined_covered_count == 2
        assert report.combined_covered_requirement_ids == ["REQ-1", "REQ-3"]
        assert report.combined_uncovered_count == 3
        assert report.get_coverage_gaps() == ["REQ-2", "REQ-4", "REQ-5"]
        assert report.combined_coverage_percentage == 40.0  # 2 / 5 * 100

    def test_zero_active_requirements_handled_safely(self) -> None:
        """Verify empty active requirement set yields 0.0% coverage deterministically."""
        proj_id = "proj-zero-req"
        inv = make_test_inventory(proj_id, [])
        report = UnifiedCoverageEngine.compute_coverage([], inv)

        assert report.total_active_requirements == 0
        assert report.active_requirement_ids == []
        assert report.combined_covered_count == 0
        assert report.combined_uncovered_count == 0
        assert report.combined_coverage_percentage == 0.0
        assert report.get_coverage_gaps() == []

    def test_inferred_links_strictly_ignored_for_authoritative_coverage(self) -> None:
        """Stage 2 Rule: inferred_requirement_links MUST NOT contribute to authoritative coverage."""
        proj_id = "proj-inferred"
        active_reqs = ["REQ-100"]

        t = UnifiedTestDefinition(
            test_id="unit:proj:t_inferred",
            tier=TestTier.UNIT,
            name="test_user_login",
            source_reference="tests/test_auth.py",
            project_id=proj_id,
            requirement_links=[],  # Authoritative links empty!
            inferred_requirement_links=["REQ-100"],  # Inferred link present
            discovery_source=DiscoveryProvenance.PYTEST_DISCOVERY,
        )
        inv = make_test_inventory(proj_id, [t])
        report = UnifiedCoverageEngine.compute_coverage(active_reqs, inv)

        # Must NOT be counted as covered!
        assert report.combined_coverage_percentage == 0.0
        assert report.get_coverage_gaps() == ["REQ-100"]
        assert report.is_requirement_covered("REQ-100") is False

    def test_inactive_requirements_excluded_from_denominator(self) -> None:
        """Verify DEFERRED, REJECTED, and ARCHIVED requirements are excluded from the active denominator."""
        proj_id = uuid.uuid4()
        now = datetime.now(timezone.utc)
        req_active_1 = RequirementResponse(
            id=uuid.uuid4(),
            project_id=proj_id,
            title="Active Req 1",
            description="Functional requirement 1",
            status=RequirementStatus.APPROVED,
            is_archived=False,
            created_at=now,
            updated_at=now,
        )
        req_active_2 = RequirementResponse(
            id=uuid.uuid4(),
            project_id=proj_id,
            title="Active Req 2",
            description="Functional requirement 2",
            status=RequirementStatus.DRAFT,
            is_archived=False,
            created_at=now,
            updated_at=now,
        )
        req_deferred = RequirementResponse(
            id=uuid.uuid4(),
            project_id=proj_id,
            title="Deferred Req",
            description="Future scope",
            status=RequirementStatus.DEFERRED,
            is_archived=False,
            created_at=now,
            updated_at=now,
        )
        req_rejected = RequirementResponse(
            id=uuid.uuid4(),
            project_id=proj_id,
            title="Rejected Req",
            description="Out of scope",
            status=RequirementStatus.REJECTED,
            is_archived=False,
            created_at=now,
            updated_at=now,
        )
        req_archived = RequirementResponse(
            id=uuid.uuid4(),
            project_id=proj_id,
            title="Archived Req",
            description="Archived requirement",
            status=RequirementStatus.APPROVED,
            is_archived=True,
            created_at=now,
            updated_at=now,
        )

        all_reqs = [req_active_1, req_active_2, req_deferred, req_rejected, req_archived]

        # Only req_active_1 is covered
        t = UnifiedTestDefinition(
            test_id=f"unit:{proj_id}:t1",
            tier=TestTier.UNIT,
            name="test_req_1",
            source_reference="tests/test.py",
            project_id=str(proj_id),
            requirement_links=[str(req_active_1.id)],
            discovery_source=DiscoveryProvenance.PYTEST_DISCOVERY,
        )
        inv = make_test_inventory(str(proj_id), [t])

        report = UnifiedCoverageEngine.compute_coverage(all_reqs, inv)

        # Denominator should be active requirements (excluding deferred, rejected, archived)
        assert str(req_deferred.id) not in report.active_requirement_ids
        assert str(req_rejected.id) not in report.active_requirement_ids
        assert str(req_archived.id) not in report.active_requirement_ids
        assert report.is_requirement_covered(str(req_active_1.id)) is True

    def test_project_isolation_requirement_mismatch(self) -> None:
        """Verify cross-project Requirement object raises UnifiedCoverageIsolationError."""
        proj_a = uuid.uuid4()
        proj_b = uuid.uuid4()
        now = datetime.now(timezone.utc)

        foreign_req = RequirementResponse(
            id=uuid.uuid4(),
            project_id=proj_b,  # Belongs to proj_b
            title="Foreign Requirement",
            description="Foreign description",
            status=RequirementStatus.APPROVED,
            is_archived=False,
            created_at=now,
            updated_at=now,
        )

        inv = make_test_inventory(str(proj_a), [])

        with pytest.raises(UnifiedCoverageIsolationError) as exc_info:
            UnifiedCoverageEngine.compute_coverage([foreign_req], inv)

        assert "violating isolation" in str(exc_info.value)

    def test_project_isolation_explicit_project_id_mismatch(self) -> None:
        """Verify passing mismatched explicit project_id raises UnifiedCoverageIsolationError."""
        inv = make_test_inventory("proj-alpha", [])
        with pytest.raises(UnifiedCoverageIsolationError) as exc_info:
            UnifiedCoverageEngine.compute_coverage(["REQ-1"], inv, project_id="proj-beta")

        assert "does not match inventory project_id" in str(exc_info.value)

    def test_project_isolation_test_in_inventory_mismatch(self) -> None:
        """Defensive check: foreign test in inventory raises UnifiedCoverageIsolationError."""
        proj_id = "proj-good"
        foreign_test = UnifiedTestDefinition(
            test_id="unit:foreign:t1",
            tier=TestTier.UNIT,
            name="test_foreign",
            source_reference="tests/test.py",
            project_id="foreign-proj",  # Foreign!
            requirement_links=["REQ-1"],
            discovery_source=DiscoveryProvenance.PYTEST_DISCOVERY,
        )
        inv = make_test_inventory(proj_id, [foreign_test])

        with pytest.raises(UnifiedCoverageIsolationError) as exc_info:
            UnifiedCoverageEngine.compute_coverage(["REQ-1"], inv)

        assert "violating inventory project" in str(exc_info.value)

    def test_multiple_tests_covering_same_requirement(self) -> None:
        """Verify multiple tests covering the same requirement count as 1 covered requirement."""
        proj_id = "proj-multi-test"
        active_reqs = ["REQ-AUTH"]

        t1 = UnifiedTestDefinition(
            test_id=f"unit:{proj_id}:t1",
            tier=TestTier.UNIT,
            name="test_login_unit",
            source_reference="tests/test_auth.py::test_1",
            project_id=proj_id,
            requirement_links=["REQ-AUTH"],
            discovery_source=DiscoveryProvenance.PYTEST_DISCOVERY,
        )
        t2 = UnifiedTestDefinition(
            test_id=f"ai_test:{proj_id}:t2",
            tier=TestTier.AI_TEST,
            name="test_login_ai",
            source_reference="tests/test_ai_auth.py::test_2",
            project_id=proj_id,
            requirement_links=["REQ-AUTH"],
            discovery_source=DiscoveryProvenance.AI_TEST_SUITE,
        )
        t3 = UnifiedTestDefinition(
            test_id=f"browser_journey:{proj_id}:t3",
            tier=TestTier.BROWSER_JOURNEY,
            name="test_login_journey",
            source_reference="/login",
            project_id=proj_id,
            requirement_links=["REQ-AUTH"],
            discovery_source=DiscoveryProvenance.VALIDATED_BROWSER_JOURNEY,
        )

        inv = make_test_inventory(proj_id, [t1, t2, t3])
        report = UnifiedCoverageEngine.compute_coverage(active_reqs, inv)

        assert report.total_active_requirements == 1
        assert report.combined_covered_count == 1
        assert report.combined_coverage_percentage == 100.0

        trace = report.requirement_traceability["REQ-AUTH"]
        assert trace.is_covered is True
        assert trace.total_tests == 3
        assert set(trace.covering_tiers) == {TestTier.UNIT, TestTier.AI_TEST, TestTier.BROWSER_JOURNEY}
        assert trace.tests_by_tier["UNIT"] == [t1.test_id]
        assert trace.tests_by_tier["AI_TEST"] == [t2.test_id]
        assert trace.tests_by_tier["BROWSER_JOURNEY"] == [t3.test_id]

    def test_deterministic_repeated_calculation(self) -> None:
        """Verify computing coverage twice against identical inputs yields equivalent reports."""
        proj_id = "proj-repeat"
        active_reqs = ["REQ-B", "REQ-A", "REQ-C"]

        t = UnifiedTestDefinition(
            test_id=f"unit:{proj_id}:t1",
            tier=TestTier.UNIT,
            name="test_1",
            source_reference="tests/t.py",
            project_id=proj_id,
            requirement_links=["REQ-A"],
            discovery_source=DiscoveryProvenance.PYTEST_DISCOVERY,
        )
        inv = make_test_inventory(proj_id, [t])

        rep1 = UnifiedCoverageEngine.compute_coverage(active_reqs, inv)
        rep2 = UnifiedCoverageEngine.compute_coverage(active_reqs, inv)

        assert rep1 == rep2
        assert rep1.active_requirement_ids == ["REQ-A", "REQ-B", "REQ-C"]  # Deterministically sorted
        assert rep1.combined_coverage_percentage == rep2.combined_coverage_percentage

    def test_empty_inventory_yields_all_gaps(self) -> None:
        """Verify empty test inventory results in 0.0% coverage and all active reqs as gaps."""
        proj_id = "proj-empty-inv"
        active_reqs = ["REQ-1", "REQ-2"]
        inv = make_test_inventory(proj_id, [])

        report = UnifiedCoverageEngine.compute_coverage(active_reqs, inv)

        assert report.total_active_requirements == 2
        assert report.combined_covered_count == 0
        assert report.combined_coverage_percentage == 0.0
        assert report.get_coverage_gaps() == ["REQ-1", "REQ-2"]
        for tier in TestTier:
            assert report.tier_coverages[tier.value].coverage_percentage == 0.0
