"""Unit Tests for ChangeImpactService (Phase 11L Stage 3).

Validates:
1. Direct and transitive source change impact calculation.
2. Direct test file modification detection.
3. Authoritative vs. inferred requirement impact mapping.
4. VersionComparisonResponse integration (added, modified, removed files).
5. Dynamic and unsupported file uncertainty with conservative over-selection.
6. Browser smoke and journey test impact.
7. Project isolation enforcement and deterministic repeated calculation.
"""

import uuid
import pytest

from app.schemas.development_version import VersionComparisonResponse, VersionFileDiff
from app.testing.impact.contracts import (
    AnalysisConfidence,
    ChangeImpactReport,
    ImpactReason,
)
from app.testing.impact.errors import ChangeImpactIsolationError
from app.testing.impact.service import ChangeImpactService
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

class TestChangeImpactService:
    """Comprehensive test suite for ChangeImpactService."""

    @pytest.fixture
    def project_id(self) -> str:
        return "00000000-0000-0000-0000-000000000001"

    @pytest.fixture
    def sample_files_map(self) -> dict[str, str]:
        return {
            "app/calculator.py": (
                "def add(a, b): return a + b\n"
                "def multiply(a, b): return a * b\n"
            ),
            "app/billing.py": (
                "from app.calculator import add, multiply\n\n"
                "def calculate_invoice(hours, rate):\n"
                "    return multiply(hours, rate)\n"
            ),
            "tests/test_calculator.py": (
                "from app.calculator import add\n\n"
                "def test_add(): assert add(1, 2) == 3\n"
            ),
            "tests/test_billing.py": (
                "from app.billing import calculate_invoice\n\n"
                "def test_invoice(): assert calculate_invoice(2, 50) == 100\n"
            ),
        }

    def test_direct_and_transitive_change_impact(
        self,
        project_id: str,
        sample_files_map: dict[str, str],
    ) -> None:
        """Verify modifying app/calculator.py affects both its direct tests and downstream billing tests."""
        # 1. Setup inventory
        t_calc = UnifiedTestDefinition(
            test_id=f"unit:{project_id}:test_calculator",
            tier=TestTier.UNIT,
            name="test_add",
            source_reference="tests/test_calculator.py::test_add",
            project_id=project_id,
            target_file="app/calculator.py",
            requirement_links=["REQ-CALC-001"],
            discovery_source=DiscoveryProvenance.PYTEST_DISCOVERY,
            metadata={"file_path": "tests/test_calculator.py"},
        )
        t_bill = UnifiedTestDefinition(
            test_id=f"unit:{project_id}:test_billing",
            tier=TestTier.UNIT,
            name="test_invoice",
            source_reference="tests/test_billing.py::test_invoice",
            project_id=project_id,
            target_file="app/billing.py",
            requirement_links=["REQ-BILL-001"],
            discovery_source=DiscoveryProvenance.PYTEST_DISCOVERY,
            metadata={"file_path": "tests/test_billing.py"},
        )
        inventory = make_test_inventory(project_id, [t_calc, t_bill])

        service = ChangeImpactService()
        report = service.analyze_change_impact(
            project_id=project_id,
            changed_files=["app/calculator.py"],
            files_map=sample_files_map,
            inventory=inventory,
            active_requirement_ids=["REQ-CALC-001", "REQ-BILL-001"],
        )

        assert report.changed_files == ["app/calculator.py"]
        # Directly affected: app/billing.py and tests/test_calculator.py directly import app/calculator.py
        assert "app/billing.py" in report.directly_affected_files
        assert "tests/test_calculator.py" in report.directly_affected_files

        # Transitively affected: tests/test_billing.py imports app/billing.py
        assert "tests/test_billing.py" in report.transitively_affected_files

        # Both tests are affected
        assert report.is_test_affected(t_calc.test_id) is True
        assert report.is_test_affected(t_bill.test_id) is True

        # Requirements affected
        assert report.is_requirement_affected("REQ-CALC-001") is True
        assert report.is_requirement_affected("REQ-BILL-001") is True

    def test_direct_test_file_modification(
        self,
        project_id: str,
        sample_files_map: dict[str, str],
    ) -> None:
        """Verify modifying only a test file marks that test as directly affected."""
        t_calc = UnifiedTestDefinition(
            test_id=f"unit:{project_id}:test_calculator",
            tier=TestTier.UNIT,
            name="test_add",
            source_reference="tests/test_calculator.py::test_add",
            project_id=project_id,
            target_file="app/calculator.py",
            requirement_links=["REQ-CALC-001"],
            discovery_source=DiscoveryProvenance.PYTEST_DISCOVERY,
            metadata={"file_path": "tests/test_calculator.py"},
        )
        inventory = make_test_inventory(project_id, [t_calc])

        service = ChangeImpactService()
        report = service.analyze_change_impact(
            project_id=project_id,
            changed_files=["tests/test_calculator.py"],
            files_map=sample_files_map,
            inventory=inventory,
        )

        assert report.changed_files == ["tests/test_calculator.py"]
        assert report.is_test_affected(t_calc.test_id) is True
        reasons = report.get_reasons_for_test(t_calc.test_id)
        assert ImpactReason.DIRECT_TEST_FILE in reasons
        assert ImpactReason.DIRECT_CHANGE in reasons

    def test_inferred_requirement_links_strictly_excluded_from_impact(
        self,
        project_id: str,
        sample_files_map: dict[str, str],
    ) -> None:
        """Stage 3 Invariant: Only authoritative requirement_links map to affected requirements."""
        t_calc = UnifiedTestDefinition(
            test_id=f"unit:{project_id}:test_calculator",
            tier=TestTier.UNIT,
            name="test_add",
            source_reference="tests/test_calculator.py::test_add",
            project_id=project_id,
            target_file="app/calculator.py",
            requirement_links=[],  # Empty authoritative links!
            inferred_requirement_links=["REQ-CALC-001"],  # Inferred link!
            discovery_source=DiscoveryProvenance.PYTEST_DISCOVERY,
            metadata={"file_path": "tests/test_calculator.py"},
        )
        inventory = make_test_inventory(project_id, [t_calc])

        service = ChangeImpactService()
        report = service.analyze_change_impact(
            project_id=project_id,
            changed_files=["app/calculator.py"],
            files_map=sample_files_map,
            inventory=inventory,
            active_requirement_ids=["REQ-CALC-001"],
        )

        assert report.is_test_affected(t_calc.test_id) is True
        # Requirement MUST NOT be marked as affected because test has no authoritative link
        assert report.is_requirement_affected("REQ-CALC-001") is False
        assert report.affected_requirements == []

    def test_version_comparison_response_integration(
        self,
        project_id: str,
        sample_files_map: dict[str, str],
    ) -> None:
        """Verify integration with VersionComparisonResponse containing added, modified, and removed files."""
        v_comp = VersionComparisonResponse(
            from_version_id=uuid.uuid4(),
            to_version_id=uuid.uuid4(),
            from_version_number=1,
            to_version_number=2,
            files_added=[VersionFileDiff(path="app/new_feature.py", change_type="ADDED", size_delta_bytes=100)],
            files_modified=[VersionFileDiff(path="app/calculator.py", change_type="MODIFIED", size_delta_bytes=50)],
            files_removed=[VersionFileDiff(path="app/old_deprecated.py", change_type="REMOVED", size_delta_bytes=-80)],
            verification_change_summary="Sprint update",
        )

        t_calc = UnifiedTestDefinition(
            test_id=f"unit:{project_id}:test_calculator",
            tier=TestTier.UNIT,
            name="test_add",
            source_reference="tests/test_calculator.py",
            project_id=project_id,
            target_file="app/calculator.py",
            requirement_links=["REQ-CALC-001"],
            discovery_source=DiscoveryProvenance.PYTEST_DISCOVERY,
        )
        inventory = make_test_inventory(project_id, [t_calc])

        service = ChangeImpactService()
        report = service.analyze_change_impact(
            project_id=project_id,
            changed_files=v_comp,
            files_map=sample_files_map,
            inventory=inventory,
        )

        assert "app/new_feature.py" in report.changed_files
        assert "app/calculator.py" in report.changed_files
        assert "app/old_deprecated.py" in report.changed_files
        assert report.is_test_affected(t_calc.test_id) is True
        assert report.comparison_context["from_version_number"] == 1

    def test_conservative_over_selection_on_unsupported_language_file(
        self,
        project_id: str,
    ) -> None:
        """Critical Safety Test: Modifying unsupported non-Python files triggers conservative fallback."""
        files_map = {
            "frontend/App.tsx": "export const App = () => <div>Hello</div>;",
            "app/main.py": "def run(): pass\n",
        }
        t_journey = UnifiedTestDefinition(
            test_id=f"browser_journey:{project_id}:bj_home",
            tier=TestTier.BROWSER_JOURNEY,
            name="Home Journey",
            source_reference="/",
            project_id=project_id,
            requirement_links=["REQ-UI-001"],
            discovery_source=DiscoveryProvenance.VALIDATED_BROWSER_JOURNEY,
            target_symbol="/",
        )
        inventory = make_test_inventory(project_id, [t_journey])

        service = ChangeImpactService()
        report = service.analyze_change_impact(
            project_id=project_id,
            changed_files=["frontend/App.tsx"],
            files_map=files_map,
            inventory=inventory,
        )

        assert "frontend/App.tsx" in report.uncertain_files
        assert report.requires_broader_regression is True
        assert report.analysis_confidence == AnalysisConfidence.MEDIUM
        # Browser test conservatively included with UNKNOWN_DEPENDENCY
        assert report.is_test_affected(t_journey.test_id) is True
        assert ImpactReason.UNKNOWN_DEPENDENCY in report.get_reasons_for_test(t_journey.test_id)

    def test_conservative_over_selection_on_dynamic_imports(
        self,
        project_id: str,
    ) -> None:
        """Critical Safety Test: Dynamic import in changed file flags uncertainty and requires broader regression."""
        files_map = {
            "app/dynamic_plugin.py": (
                "def load(name):\n"
                "    return __import__(name)\n"
            ),
            "app/main.py": "def run(): pass\n",
        }
        inventory = make_test_inventory(project_id, [])

        service = ChangeImpactService()
        report = service.analyze_change_impact(
            project_id=project_id,
            changed_files=["app/dynamic_plugin.py"],
            files_map=files_map,
            inventory=inventory,
        )

        assert "app/dynamic_plugin.py" in report.uncertain_files
        assert report.requires_broader_regression is True

    def test_project_isolation_enforcement(self, project_id: str) -> None:
        """Verify cross-project inventory or test is strictly rejected."""
        foreign_proj = "99999999-9999-9999-9999-999999999999"
        foreign_test = UnifiedTestDefinition(
            test_id=f"unit:{foreign_proj}:t1",
            tier=TestTier.UNIT,
            name="test_foreign",
            source_reference="tests/test.py",
            project_id=foreign_proj,
            discovery_source=DiscoveryProvenance.PYTEST_DISCOVERY,
        )
        inventory = make_test_inventory(project_id, [foreign_test])

        service = ChangeImpactService()
        with pytest.raises(ChangeImpactIsolationError) as exc_info:
            service.analyze_change_impact(
                project_id=project_id,
                changed_files=["app/main.py"],
                files_map={"app/main.py": "pass\n"},
                inventory=inventory,
            )

        assert "violating isolation" in str(exc_info.value)

    def test_empty_changed_files_yields_empty_impact(self, project_id: str) -> None:
        """Verify empty change set yields no affected files, tests, or requirements."""
        inventory = make_test_inventory(project_id, [])
        service = ChangeImpactService()

        report = service.analyze_change_impact(
            project_id=project_id,
            changed_files=[],
            files_map={"app/calc.py": "pass\n"},
            inventory=inventory,
        )

        assert report.changed_files == []
        assert report.directly_affected_files == []
        assert report.transitively_affected_files == []
        assert report.affected_tests == []
        assert report.affected_requirements == []
        assert report.requires_broader_regression is False
        assert report.analysis_confidence == AnalysisConfidence.HIGH

    def test_deterministic_repeated_impact_calculation(
        self,
        project_id: str,
        sample_files_map: dict[str, str],
    ) -> None:
        """Verify repeated impact analysis produces strictly equivalent reports."""
        t_calc = UnifiedTestDefinition(
            test_id=f"unit:{project_id}:test_calc",
            tier=TestTier.UNIT,
            name="test_add",
            source_reference="tests/test_calculator.py",
            project_id=project_id,
            target_file="app/calculator.py",
            requirement_links=["REQ-1"],
            discovery_source=DiscoveryProvenance.PYTEST_DISCOVERY,
        )
        inventory = make_test_inventory(project_id, [t_calc])

        service = ChangeImpactService()
        rep1 = service.analyze_change_impact(
            project_id=project_id,
            changed_files=["app/calculator.py"],
            files_map=sample_files_map,
            inventory=inventory,
            active_requirement_ids=["REQ-1"],
        )
        rep2 = service.analyze_change_impact(
            project_id=project_id,
            changed_files=["app/calculator.py"],
            files_map=sample_files_map,
            inventory=inventory,
            active_requirement_ids=["REQ-1"],
        )

        assert rep1 == rep2
        assert rep1.affected_test_ids == rep2.affected_test_ids
        assert rep1.affected_requirements == rep2.affected_requirements
