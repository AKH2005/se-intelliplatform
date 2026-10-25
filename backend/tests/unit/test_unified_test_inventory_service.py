"""Unit Tests for UnifiedTestInventoryService (Phase 11L Stage 1).

Validates:
1. Deterministic discovery and normalization across all four testing tiers.
2. Rejection of unvalidated candidates and isolation enforcement.
3. Bidirectional requirement traceability indexing.
4. Strict and non-strict duplicate collision handling.
5. Deterministic repeated discovery and empty inventory safety.
"""

import uuid
import pytest

from app.agents.browser_journey.contracts import (
    BrowserActionType,
    BrowserJourneyStep,
    BrowserJourneySuiteCandidate,
    BrowserTarget,
    BrowserTargetType,
    JourneyCategory,
    JourneyPriority,
)
from app.agents.test_generation.contracts import AITestSuite, GeneratedTest, TestCategory
from app.browser.contracts import DeterministicBrowserTestDefinition, DeterministicInteraction, BrowserInteractionType
from app.browser.journey.contracts import (
    RequirementCoverageReport,
    ValidatedBrowserJourney,
    ValidatedBrowserJourneySuite,
)
from app.testing.inventory.contracts import (
    DiscoveryProvenance,
    DiscoveryStatus,
    TestTier,
    UnifiedTestDefinition,
    UnifiedTestInventory,
    compute_deterministic_inventory_id,
)
from app.testing.inventory.errors import (
    UnifiedTestInventoryConflictError,
    UnifiedTestInventoryIsolationError,
    UnifiedTestInventoryValidationError,
)
from app.testing.inventory.service import UnifiedTestInventoryService


# ==============================================================================
# Fixtures and Helpers
# ==============================================================================

@pytest.fixture
def project_id() -> str:
    return "00000000-0000-0000-0000-000000000001"


@pytest.fixture
def sample_files_map() -> dict[str, str]:
    return {
        "app/calculator.py": (
            "def add(a, b):\n"
            "    return a + b\n\n"
            "def multiply(a, b):\n"
            "    return a * b\n"
        ),
        "tests/test_calculator.py": (
            '"""Tests for the calculator application."""\n\n'
            "def test_add():\n"
            '    """Verifies that add correctly sums numbers."""\n'
            "    assert add(1, 2) == 3\n\n"
            "class TestCalculatorAdvanced:\n"
            '    """Advanced test class."""\n'
            "    def test_multiply(self):\n"
            '        """Verifies multiplication."""\n'
            "        assert multiply(2, 3) == 6\n\n"
            "    def helper_method(self):\n"
            "        return 42\n\n"
            "def helper_func():\n"
            "    pass\n"
        ),
        "app/utils.py": "def noop(): pass\n",
    }


@pytest.fixture
def sample_ai_test_suite(project_id: str) -> AITestSuite:
    test_1 = GeneratedTest(
        test_id="ai_test_add_edge_case",
        name="test_add_negative_numbers",
        description="Verifies addition handles negative inputs accurately",
        category=TestCategory.EDGE_CASE,
        target_file="app/calculator.py",
        target_symbol="add",
        requirement_ids=["REQ-CALC-001"],
        rationale="Edge cases must be thoroughly exercised for negative bounds",
        code="def test_add_negative_numbers(): assert add(-1, -2) == -3",
        expected_behavior="Returns -3 without throwing an error",
    )
    test_2 = GeneratedTest(
        test_id="ai_test_mult_zero",
        name="test_multiply_by_zero",
        description="Verifies multiplication by zero returns zero",
        category=TestCategory.HAPPY_PATH,
        target_file="app/calculator.py",
        target_symbol="multiply",
        requirement_ids=["REQ-CALC-002"],
        rationale="Zero multiplication is a primary domain requirement",
        code="def test_multiply_by_zero(): assert multiply(5, 0) == 0",
        expected_behavior="Returns 0",
    )
    return AITestSuite(
        suite_id=uuid.uuid4(),
        project_id=uuid.UUID(project_id),
        summary="AI-generated unit test suite for calculator module",
        tests=[test_1, test_2],
        test_count=2,
        requirement_traceability={"REQ-CALC-001": [test_1.test_id], "REQ-CALC-002": [test_2.test_id]},
        test_files={"tests/test_ai_calculator.py": "# generated test code\n"},
    )


@pytest.fixture
def sample_browser_smoke_tests() -> list[DeterministicBrowserTestDefinition]:
    return [
        DeterministicBrowserTestDefinition(
            test_id="smoke_root_page",
            name="Verify Root Dashboard Page",
            target_path="/",
            expected_status=200,
            expected_title_contains="Calculator",
            expected_elements=["body", "#app"],
            interactions=[
                DeterministicInteraction(
                    action=BrowserInteractionType.ASSERT_VISIBLE,
                    selector="#app",
                    timeout_seconds=5.0,
                )
            ],
            capture_screenshot=True,
            metadata={"requirement_ids": ["REQ-UI-001"]},
        )
    ]


@pytest.fixture
def sample_browser_journey_suite(project_id: str) -> ValidatedBrowserJourneySuite:
    journey_1 = ValidatedBrowserJourney(
        journey_id="BJ-001",
        title="Calculator Standard Workflow",
        description="User navigates to calculator, performs add, and verifies display",
        category=JourneyCategory.HAPPY_PATH,
        priority=JourneyPriority.HIGH,
        validated_requirement_ids=["REQ-CALC-001", "REQ-UI-001"],
        preconditions=["System is running and accessible"],
        validated_target_routes=["/calculator"],
        steps=[
            BrowserJourneyStep(
                step_id="step_1",
                action=BrowserActionType.NAVIGATE,
                route="/calculator",
                description="Navigating to /calculator",
            ),
            BrowserJourneyStep(
                step_id="step_2",
                action=BrowserActionType.ASSERT_VISIBLE,
                target=BrowserTarget(
                    target_type=BrowserTargetType.CSS_SELECTOR,
                    value="#display",
                    description="Calculator display element",
                ),
                description="Check calculator display is visible",
            ),
        ],
        expected_outcomes=["Calculator display is visible and responsive"],
    )

    cov_report = RequirementCoverageReport(
        total_active_requirements=2,
        covered_requirement_count=2,
        uncovered_requirement_count=0,
        covered_requirement_ids=["REQ-CALC-001", "REQ-UI-001"],
        uncovered_requirement_ids=[],
        coverage_percentage=100.0,
        journey_count=1,
        requirement_to_journeys_map={"REQ-CALC-001": ["BJ-001"], "REQ-UI-001": ["BJ-001"]},
        journey_to_requirements_map={"BJ-001": ["REQ-CALC-001", "REQ-UI-001"]},
    )

    return ValidatedBrowserJourneySuite(
        suite_id=str(uuid.uuid4()),
        project_id=uuid.UUID(project_id),
        suite_name="Calculator Core Browser Journeys",
        summary="Validated end-to-end browser journeys for calculator functionality",
        journeys=[journey_1],
        coverage_report=cov_report,
    )


# ==============================================================================
# Service Test Suite
# ==============================================================================

class TestUnifiedTestInventoryService:
    """Comprehensive test suite for UnifiedTestInventoryService."""

    def test_discover_unit_tests(
        self,
        project_id: str,
        sample_files_map: dict[str, str],
    ) -> None:
        """Verify AST-based unit test discovery from files map."""
        service = UnifiedTestInventoryService()
        unit_tests = service.discover_unit_tests(project_id, sample_files_map)

        assert len(unit_tests) == 2

        # 1. Top-level test function
        func_test = next((t for t in unit_tests if t.name == "test_add"), None)
        assert func_test is not None
        assert func_test.tier == TestTier.UNIT
        assert func_test.discovery_source == DiscoveryProvenance.PYTEST_DISCOVERY
        assert func_test.source_reference == "tests/test_calculator.py::test_add"
        assert func_test.test_id == f"unit:{project_id}:tests_test_calculator_py__test_add"
        assert func_test.description == "Verifies that add correctly sums numbers."
        assert func_test.target_file == "app/calculator.py"
        assert func_test.requirement_links == []  # Crucial: no hallucinated links

        # 2. Test class member function
        class_test = next((t for t in unit_tests if t.name == "TestCalculatorAdvanced::test_multiply"), None)
        assert class_test is not None
        assert class_test.tier == TestTier.UNIT
        assert class_test.source_reference == "tests/test_calculator.py::TestCalculatorAdvanced::test_multiply"
        assert class_test.description == "Verifies multiplication."
        assert class_test.metadata["class_name"] == "TestCalculatorAdvanced"
        assert class_test.metadata["method_name"] == "test_multiply"
        assert class_test.target_file == "app/calculator.py"

    def test_discover_unit_tests_ignores_unparseable_files_gracefully(
        self,
        project_id: str,
    ) -> None:
        """Verify unparseable syntax error files do not break discovery of valid tests."""
        service = UnifiedTestInventoryService()
        files = {
            "tests/test_broken.py": "def test_syntax_error(:\n    pass\n",
            "tests/test_valid.py": "def test_ok():\n    assert True\n",
        }

        discovered = service.discover_unit_tests(project_id, files)
        assert len(discovered) == 1
        assert discovered[0].name == "test_ok"

    def test_normalize_ai_tests(
        self,
        project_id: str,
        sample_ai_test_suite: AITestSuite,
    ) -> None:
        """Verify normalization of authoritative AITestSuite."""
        service = UnifiedTestInventoryService()
        ai_tests = service.normalize_ai_tests(project_id, sample_ai_test_suite)

        assert len(ai_tests) == 2

        t1 = ai_tests[0]
        assert t1.tier == TestTier.AI_TEST
        assert t1.discovery_source == DiscoveryProvenance.AI_TEST_SUITE
        assert t1.test_id == f"ai_test:{project_id}:ai_test_add_edge_case"
        assert t1.requirement_links == ["REQ-CALC-001"]
        assert t1.target_file == "app/calculator.py"
        assert t1.target_symbol == "add"
        assert t1.metadata["category"] == "EDGE_CASE"

        t2 = ai_tests[1]
        assert t2.test_id == f"ai_test:{project_id}:ai_test_mult_zero"
        assert t2.requirement_links == ["REQ-CALC-002"]

    def test_normalize_ai_tests_enforces_project_isolation(
        self,
        project_id: str,
        sample_ai_test_suite: AITestSuite,
    ) -> None:
        """Verify cross-project AITestSuite normalization is strictly blocked."""
        service = UnifiedTestInventoryService()
        foreign_project_id = "99999999-9999-9999-9999-999999999999"

        with pytest.raises(UnifiedTestInventoryIsolationError) as exc_info:
            service.normalize_ai_tests(foreign_project_id, sample_ai_test_suite)

        assert "cannot normalize for target" in str(exc_info.value)

    def test_normalize_browser_smoke_tests(
        self,
        project_id: str,
        sample_browser_smoke_tests: list[DeterministicBrowserTestDefinition],
    ) -> None:
        """Verify normalization of deterministic browser smoke test definitions."""
        service = UnifiedTestInventoryService()
        smoke_tests = service.normalize_browser_smoke_tests(project_id, sample_browser_smoke_tests)

        assert len(smoke_tests) == 1
        st = smoke_tests[0]
        assert st.tier == TestTier.BROWSER_SMOKE
        assert st.discovery_source == DiscoveryProvenance.BROWSER_SMOKE_SUITE
        assert st.test_id == f"browser_smoke:{project_id}:smoke_root_page"
        assert st.name == "Verify Root Dashboard Page"
        assert st.source_reference == "/"
        assert st.target_symbol == "/"
        assert st.requirement_links == ["REQ-UI-001"]
        assert st.metadata["interactions_count"] == 1
        assert st.metadata["capture_screenshot"] is True

    def test_normalize_browser_journeys(
        self,
        project_id: str,
        sample_browser_journey_suite: ValidatedBrowserJourneySuite,
    ) -> None:
        """Verify normalization of validated browser journeys."""
        service = UnifiedTestInventoryService()
        journeys = service.normalize_browser_journeys(project_id, sample_browser_journey_suite)

        assert len(journeys) == 1
        j = journeys[0]
        assert j.tier == TestTier.BROWSER_JOURNEY
        assert j.discovery_source == DiscoveryProvenance.VALIDATED_BROWSER_JOURNEY
        assert j.test_id == f"browser_journey:{project_id}:BJ-001"
        assert j.name == "Calculator Standard Workflow"
        assert j.requirement_links == ["REQ-CALC-001", "REQ-UI-001"]
        assert j.metadata["category"] == "HAPPY_PATH"
        assert j.metadata["priority"] == "HIGH"
        assert j.metadata["steps_count"] == 2

    def test_normalize_browser_journeys_rejects_unvalidated_candidate(
        self,
        project_id: str,
    ) -> None:
        """Verify unvalidated BrowserJourneySuiteCandidate is rejected."""
        service = UnifiedTestInventoryService()
        unvalidated_candidate = BrowserJourneySuiteCandidate(
            summary="Candidate suite from LLM",
            journeys=[],
        )

        with pytest.raises(UnifiedTestInventoryValidationError) as exc_info:
            service.normalize_browser_journeys(project_id, unvalidated_candidate)  # type: ignore

        assert "Unvalidated BrowserJourneySuiteCandidate cannot be normalized" in str(exc_info.value)

    def test_normalize_browser_journeys_enforces_project_isolation(
        self,
        project_id: str,
        sample_browser_journey_suite: ValidatedBrowserJourneySuite,
    ) -> None:
        """Verify cross-project browser journey suite is strictly rejected."""
        service = UnifiedTestInventoryService()
        foreign_project_id = "88888888-8888-8888-8888-888888888888"

        with pytest.raises(UnifiedTestInventoryIsolationError) as exc_info:
            service.normalize_browser_journeys(foreign_project_id, sample_browser_journey_suite)

        assert "cannot normalize for target" in str(exc_info.value)

    def test_build_inventory_across_all_four_tiers(
        self,
        project_id: str,
        sample_files_map: dict[str, str],
        sample_ai_test_suite: AITestSuite,
        sample_browser_smoke_tests: list[DeterministicBrowserTestDefinition],
        sample_browser_journey_suite: ValidatedBrowserJourneySuite,
    ) -> None:
        """Verify end-to-end compilation of UnifiedTestInventory across all four tiers."""
        service = UnifiedTestInventoryService()
        inventory = service.build_inventory(
            project_id=project_id,
            files_map=sample_files_map,
            ai_test_suite=sample_ai_test_suite,
            smoke_tests=sample_browser_smoke_tests,
            journey_suite=sample_browser_journey_suite,
            strict=True,
        )

        assert inventory.project_id == project_id
        assert inventory.discovery_status == DiscoveryStatus.COMPLETE
        assert inventory.conflicts == []
        assert inventory.total_tests == 6  # 2 unit + 2 ai + 1 smoke + 1 journey

        # Check counts per tier
        assert inventory.tier_counts["UNIT"] == 2
        assert inventory.tier_counts["AI_TEST"] == 2
        assert inventory.tier_counts["BROWSER_SMOKE"] == 1
        assert inventory.tier_counts["BROWSER_JOURNEY"] == 1

        # Check tests_by_tier
        assert len(inventory.tests_by_tier["UNIT"]) == 2
        assert len(inventory.tests_by_tier["AI_TEST"]) == 2
        assert len(inventory.tests_by_tier["BROWSER_SMOKE"]) == 1
        assert len(inventory.tests_by_tier["BROWSER_JOURNEY"]) == 1

    def test_bidirectional_traceability_indexing(
        self,
        project_id: str,
        sample_files_map: dict[str, str],
        sample_ai_test_suite: AITestSuite,
        sample_browser_smoke_tests: list[DeterministicBrowserTestDefinition],
        sample_browser_journey_suite: ValidatedBrowserJourneySuite,
    ) -> None:
        """Verify forward and reverse requirement traceability indexing."""
        service = UnifiedTestInventoryService()
        inventory = service.build_inventory(
            project_id=project_id,
            files_map=sample_files_map,
            ai_test_suite=sample_ai_test_suite,
            smoke_tests=sample_browser_smoke_tests,
            journey_suite=sample_browser_journey_suite,
        )

        # Reverse lookup: Requirement -> Tests
        # REQ-CALC-001 is covered by AI test 1 and Browser Journey 1
        calc_001_tests = inventory.get_tests_for_requirement("REQ-CALC-001")
        assert len(calc_001_tests) == 2
        assert {t.tier for t in calc_001_tests} == {TestTier.AI_TEST, TestTier.BROWSER_JOURNEY}

        # REQ-UI-001 is covered by Browser Smoke 1 and Browser Journey 1
        ui_001_tests = inventory.get_tests_for_requirement("REQ-UI-001")
        assert len(ui_001_tests) == 2
        assert {t.tier for t in ui_001_tests} == {TestTier.BROWSER_SMOKE, TestTier.BROWSER_JOURNEY}

        # Forward lookup: Test -> Requirements
        ai_t1_id = f"ai_test:{project_id}:ai_test_add_edge_case"
        assert inventory.get_requirements_for_test(ai_t1_id) == ["REQ-CALC-001"]

        # Unit tests have no requirement links
        unit_t1_id = f"unit:{project_id}:tests_test_calculator_py__test_add"
        assert inventory.get_requirements_for_test(unit_t1_id) == []

        # Linked vs unlinked tests
        unlinked = inventory.get_unlinked_tests()
        assert len(unlinked) == 2
        assert all(t.tier == TestTier.UNIT for t in unlinked)

        linked = inventory.get_linked_tests()
        assert len(linked) == 4

    def test_duplicate_detection_strict_raises_conflict_error(
        self,
        project_id: str,
    ) -> None:
        """Verify strict mode raises UnifiedTestInventoryConflictError on duplicate test IDs."""
        service = UnifiedTestInventoryService()
        # Duplicate deterministic smoke tests
        st1 = DeterministicBrowserTestDefinition(
            test_id="smoke_duplicate",
            name="Smoke Test A",
            target_path="/",
        )
        st2 = DeterministicBrowserTestDefinition(
            test_id="smoke_duplicate",
            name="Smoke Test B",
            target_path="/dashboard",
        )

        with pytest.raises(UnifiedTestInventoryConflictError) as exc_info:
            service.build_inventory(
                project_id=project_id,
                smoke_tests=[st1, st2],
                strict=True,
            )

        assert "Duplicate normalized test_id" in str(exc_info.value)
        assert "smoke_duplicate" in str(exc_info.value)

    def test_duplicate_detection_non_strict_records_conflict(
        self,
        project_id: str,
    ) -> None:
        """Verify non-strict mode records conflict without raising and sets status to CONFLICT."""
        service = UnifiedTestInventoryService()
        st1 = DeterministicBrowserTestDefinition(
            test_id="smoke_dup",
            name="Smoke Test 1",
            target_path="/",
        )
        st2 = DeterministicBrowserTestDefinition(
            test_id="smoke_dup",
            name="Smoke Test 2",
            target_path="/settings",
        )

        inventory = service.build_inventory(
            project_id=project_id,
            smoke_tests=[st1, st2],
            strict=False,
        )

        assert inventory.discovery_status == DiscoveryStatus.CONFLICT
        assert len(inventory.conflicts) == 1
        assert inventory.conflicts[0].test_id == f"browser_smoke:{project_id}:smoke_dup"
        assert inventory.total_tests == 1  # Only first occurrence kept

    def test_deterministic_repeated_discovery(
        self,
        project_id: str,
        sample_files_map: dict[str, str],
        sample_ai_test_suite: AITestSuite,
        sample_browser_smoke_tests: list[DeterministicBrowserTestDefinition],
        sample_browser_journey_suite: ValidatedBrowserJourneySuite,
    ) -> None:
        """Verify repeated discovery against the exact same input produces identical inventories."""
        service = UnifiedTestInventoryService()

        inv1 = service.build_inventory(
            project_id=project_id,
            files_map=sample_files_map,
            ai_test_suite=sample_ai_test_suite,
            smoke_tests=sample_browser_smoke_tests,
            journey_suite=sample_browser_journey_suite,
        )

        inv2 = service.build_inventory(
            project_id=project_id,
            files_map=sample_files_map,
            ai_test_suite=sample_ai_test_suite,
            smoke_tests=sample_browser_smoke_tests,
            journey_suite=sample_browser_journey_suite,
        )

        assert inv1.inventory_id == inv2.inventory_id
        assert inv1.total_tests == inv2.total_tests
        assert [t.test_id for t in inv1.tests] == [t.test_id for t in inv2.tests]
        assert inv1.tests_by_requirement == inv2.tests_by_requirement
        assert inv1.requirements_by_test == inv2.requirements_by_test
        assert inv1 == inv2

    def test_empty_inventory(self, project_id: str) -> None:
        """Verify building an empty inventory produces valid deterministic defaults."""
        service = UnifiedTestInventoryService()
        inv = service.build_inventory(project_id=project_id)

        assert inv.project_id == project_id
        assert inv.total_tests == 0
        assert inv.tests == []
        assert inv.conflicts == []
        assert inv.discovery_status == DiscoveryStatus.COMPLETE
        assert inv.tier_counts == {"UNIT": 0, "AI_TEST": 0, "BROWSER_SMOKE": 0, "BROWSER_JOURNEY": 0}
        assert inv.inventory_id.startswith(f"inv_{project_id[:8]}_")
