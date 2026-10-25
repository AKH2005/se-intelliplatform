"""Unit Tests for Unified Coverage Domain Contracts (Phase 11L Stage 2)."""

import pytest
from pydantic import ValidationError

from app.testing.coverage.contracts import (
    RequirementTraceabilityRecord,
    TierCoverageSummary,
    UnifiedCoverageReport,
)
from app.testing.inventory.contracts import TestTier


class TestUnifiedCoverageContracts:
    """Comprehensive tests for coverage contracts, models, and invariants."""

    def test_tier_coverage_summary_creation(self) -> None:
        """Verify valid TierCoverageSummary instantiation and field constraints."""
        summary = TierCoverageSummary(
            tier=TestTier.UNIT,
            total_active_requirements=4,
            covered_requirement_count=2,
            uncovered_requirement_count=2,
            covered_requirement_ids=["REQ-1", "REQ-2"],
            uncovered_requirement_ids=["REQ-3", "REQ-4"],
            coverage_percentage=50.0,
            test_count=5,
            test_ids_by_requirement={"REQ-1": ["unit:p:t1"], "REQ-2": ["unit:p:t2"]},
        )

        assert summary.tier == TestTier.UNIT
        assert summary.total_active_requirements == 4
        assert summary.covered_requirement_count == 2
        assert summary.coverage_percentage == 50.0
        assert summary.test_count == 5

    def test_tier_coverage_summary_rejects_negative_counts(self) -> None:
        """Verify negative counts are rejected."""
        with pytest.raises(ValidationError):
            TierCoverageSummary(
                tier=TestTier.AI_TEST,
                total_active_requirements=-1,
                covered_requirement_count=0,
                uncovered_requirement_count=0,
                coverage_percentage=0.0,
                test_count=0,
            )

    def test_requirement_traceability_record_creation(self) -> None:
        """Verify RequirementTraceabilityRecord accurately reflects covering tiers."""
        record = RequirementTraceabilityRecord(
            requirement_id="REQ-AUTH-01",
            is_covered=True,
            covering_tiers=[TestTier.UNIT, TestTier.BROWSER_JOURNEY],
            tests_by_tier={
                TestTier.UNIT.value: ["unit:proj:test_login"],
                TestTier.BROWSER_JOURNEY.value: ["browser_journey:proj:login_flow"],
            },
            total_tests=2,
        )

        assert record.requirement_id == "REQ-AUTH-01"
        assert record.is_covered is True
        assert len(record.covering_tiers) == 2
        assert record.total_tests == 2

    def test_unified_coverage_report_query_helpers(self) -> None:
        """Verify helper query methods on UnifiedCoverageReport."""
        proj_id = "proj-coverage-test"
        unit_summary = TierCoverageSummary(
            tier=TestTier.UNIT,
            total_active_requirements=2,
            covered_requirement_count=1,
            uncovered_requirement_count=1,
            covered_requirement_ids=["REQ-1"],
            uncovered_requirement_ids=["REQ-2"],
            coverage_percentage=50.0,
            test_count=1,
            test_ids_by_requirement={"REQ-1": ["unit:p:t1"]},
        )

        traceability = {
            "REQ-1": RequirementTraceabilityRecord(
                requirement_id="REQ-1",
                is_covered=True,
                covering_tiers=[TestTier.UNIT],
                tests_by_tier={"UNIT": ["unit:p:t1"]},
                total_tests=1,
            ),
            "REQ-2": RequirementTraceabilityRecord(
                requirement_id="REQ-2",
                is_covered=False,
                covering_tiers=[],
                tests_by_tier={},
                total_tests=0,
            ),
        }

        report = UnifiedCoverageReport(
            project_id=proj_id,
            total_active_requirements=2,
            active_requirement_ids=["REQ-1", "REQ-2"],
            tier_coverages={"UNIT": unit_summary},
            combined_covered_requirement_ids=["REQ-1"],
            combined_covered_count=1,
            combined_uncovered_requirement_ids=["REQ-2"],
            combined_uncovered_count=1,
            combined_coverage_percentage=50.0,
            requirement_traceability=traceability,
        )

        # 1. get_tier_coverage
        retrieved_tier = report.get_tier_coverage(TestTier.UNIT)
        assert retrieved_tier is not None
        assert retrieved_tier.coverage_percentage == 50.0
        assert report.get_tier_coverage("UNKNOWN") is None

        # 2. get_coverage_gaps
        assert report.get_coverage_gaps() == ["REQ-2"]

        # 3. is_requirement_covered
        assert report.is_requirement_covered("REQ-1") is True
        assert report.is_requirement_covered("REQ-2") is False
        assert report.is_requirement_covered("REQ-NONEXISTENT") is False

        # 4. get_tests_for_requirement
        tests_req_1 = report.get_tests_for_requirement("REQ-1")
        assert tests_req_1 == {"UNIT": ["unit:p:t1"]}
        assert report.get_tests_for_requirement("REQ-2") == {}

    def test_report_deterministic_equality_ignores_timestamp(self) -> None:
        """Verify report __eq__ ignores volatile calculated_at timestamps."""
        kwargs = {
            "project_id": "proj-eq",
            "total_active_requirements": 1,
            "active_requirement_ids": ["REQ-1"],
            "tier_coverages": {},
            "combined_covered_requirement_ids": ["REQ-1"],
            "combined_covered_count": 1,
            "combined_uncovered_requirement_ids": [],
            "combined_uncovered_count": 0,
            "combined_coverage_percentage": 100.0,
            "requirement_traceability": {},
        }

        rep1 = UnifiedCoverageReport(**kwargs)
        rep2 = UnifiedCoverageReport(**kwargs)

        assert rep1 == rep2
        # Different field should break equality
        rep3 = UnifiedCoverageReport(**{**kwargs, "combined_coverage_percentage": 50.0})
        assert rep1 != rep3

    def test_coverage_report_serialization_roundtrip(self) -> None:
        """Verify Pydantic model_dump and model_validate preserve all fields and types."""
        report = UnifiedCoverageReport(
            project_id="proj-roundtrip",
            total_active_requirements=1,
            active_requirement_ids=["REQ-1"],
            tier_coverages={},
            combined_covered_requirement_ids=["REQ-1"],
            combined_covered_count=1,
            combined_uncovered_requirement_ids=[],
            combined_uncovered_count=0,
            combined_coverage_percentage=100.0,
            requirement_traceability={},
        )

        dumped = report.model_dump(mode="json")
        loaded = UnifiedCoverageReport.model_validate(dumped)

        assert loaded.project_id == report.project_id
        assert loaded.combined_coverage_percentage == 100.0
        assert loaded.active_requirement_ids == ["REQ-1"]
