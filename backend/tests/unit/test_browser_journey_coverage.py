"""Unit Tests for Phase 11K Stage 2 Requirement Coverage Engine.

Tests requirement-based coverage calculations:
- 100% coverage
- Partial coverage
- 0% coverage
- Zero active requirements (boundary 0.0%)
- Deduplication of multiple journeys covering the same requirement
- Uncovered requirement identification
- Bidirectional traceability mapping
"""

import uuid
import pytest

from app.agents.browser_journey.contracts import (
    BrowserActionType,
    BrowserJourneyStep,
    BrowserTarget,
    BrowserTargetType,
    JourneyCategory,
    JourneyPriority,
)
from app.browser.journey.contracts import ValidatedBrowserJourney
from app.browser.journey.coverage import RequirementCoverageEngine


def _make_dummy_journey(journey_id: str, requirement_ids: list[str]) -> ValidatedBrowserJourney:
    return ValidatedBrowserJourney(
        journey_id=journey_id,
        title=f"Journey {journey_id}",
        description="Testing journey for coverage engine",
        category=JourneyCategory.HAPPY_PATH,
        priority=JourneyPriority.MEDIUM,
        validated_requirement_ids=requirement_ids,
        validated_target_routes=["/test"],
        steps=[
            BrowserJourneyStep(
                step_id="step-1",
                action=BrowserActionType.NAVIGATE,
                route="/test",
                description="Navigate to test route",
            ),
            BrowserJourneyStep(
                step_id="step-2",
                action=BrowserActionType.CLICK,
                target=BrowserTarget(target_type=BrowserTargetType.TEST_ID, value="btn"),
                description="Click button",
            ),
        ],
    )


def test_coverage_100_percent():
    active_reqs = ["REQ-001", "REQ-002", "REQ-003"]
    j1 = _make_dummy_journey("BJ-1", ["REQ-001", "REQ-002"])
    j2 = _make_dummy_journey("BJ-2", ["REQ-003"])

    report = RequirementCoverageEngine.compute_coverage(
        validated_journeys=[j1, j2],
        active_requirement_ids=active_reqs,
    )

    assert report.total_active_requirements == 3
    assert report.covered_requirement_count == 3
    assert report.uncovered_requirement_count == 0
    assert report.coverage_percentage == 100.0
    assert report.covered_requirement_ids == ["REQ-001", "REQ-002", "REQ-003"]
    assert report.uncovered_requirement_ids == []
    assert report.journey_count == 2
    assert report.requirement_to_journeys_map["REQ-001"] == ["BJ-1"]
    assert report.requirement_to_journeys_map["REQ-002"] == ["BJ-1"]
    assert report.requirement_to_journeys_map["REQ-003"] == ["BJ-2"]


def test_coverage_partial_percent():
    active_reqs = ["REQ-001", "REQ-002", "REQ-003", "REQ-004"]
    j1 = _make_dummy_journey("BJ-1", ["REQ-001"])
    j2 = _make_dummy_journey("BJ-2", ["REQ-003"])

    report = RequirementCoverageEngine.compute_coverage(
        validated_journeys=[j1, j2],
        active_requirement_ids=active_reqs,
    )

    assert report.total_active_requirements == 4
    assert report.covered_requirement_count == 2
    assert report.uncovered_requirement_count == 2
    assert report.coverage_percentage == 50.0
    assert report.covered_requirement_ids == ["REQ-001", "REQ-003"]
    assert report.uncovered_requirement_ids == ["REQ-002", "REQ-004"]


def test_coverage_zero_percent():
    active_reqs = ["REQ-001", "REQ-002"]
    # Journey has no requirement links
    j1 = _make_dummy_journey("BJ-1", [])

    report = RequirementCoverageEngine.compute_coverage(
        validated_journeys=[j1],
        active_requirement_ids=active_reqs,
    )

    assert report.total_active_requirements == 2
    assert report.covered_requirement_count == 0
    assert report.uncovered_requirement_count == 2
    assert report.coverage_percentage == 0.0
    assert report.covered_requirement_ids == []
    assert report.uncovered_requirement_ids == ["REQ-001", "REQ-002"]


def test_coverage_zero_active_requirements_safe_zero():
    # When active requirements list is empty, division by zero is avoided
    j1 = _make_dummy_journey("BJ-1", [])

    report = RequirementCoverageEngine.compute_coverage(
        validated_journeys=[j1],
        active_requirement_ids=[],
    )

    assert report.total_active_requirements == 0
    assert report.covered_requirement_count == 0
    assert report.uncovered_requirement_count == 0
    assert report.coverage_percentage == 0.0
    assert report.covered_requirement_ids == []
    assert report.uncovered_requirement_ids == []


def test_coverage_deduplication_multiple_journeys_one_requirement():
    active_reqs = ["REQ-001", "REQ-002"]
    # Both j1 and j2 cover REQ-001
    j1 = _make_dummy_journey("BJ-1", ["REQ-001"])
    j2 = _make_dummy_journey("BJ-2", ["REQ-001"])

    report = RequirementCoverageEngine.compute_coverage(
        validated_journeys=[j1, j2],
        active_requirement_ids=active_reqs,
    )

    assert report.total_active_requirements == 2
    assert report.covered_requirement_count == 1
    assert report.uncovered_requirement_count == 1
    assert report.coverage_percentage == 50.0
    assert report.covered_requirement_ids == ["REQ-001"]
    assert report.uncovered_requirement_ids == ["REQ-002"]
    assert report.requirement_to_journeys_map["REQ-001"] == ["BJ-1", "BJ-2"]


def test_coverage_ignores_unrecognized_ids():
    active_reqs = ["REQ-001"]
    # Journey references an ID not in active_requirement_ids
    j1 = _make_dummy_journey("BJ-1", ["REQ-001", "NON-EXISTENT"])

    report = RequirementCoverageEngine.compute_coverage(
        validated_journeys=[j1],
        active_requirement_ids=active_reqs,
    )

    # Only REQ-001 counts
    assert report.total_active_requirements == 1
    assert report.covered_requirement_count == 1
    assert report.coverage_percentage == 100.0
    assert report.covered_requirement_ids == ["REQ-001"]
    assert "NON-EXISTENT" not in report.requirement_to_journeys_map
