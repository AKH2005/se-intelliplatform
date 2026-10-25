"""Unit Tests for Unified Test Inventory Domain Contracts (Phase 11L Stage 1)."""

import uuid
import pytest
from pydantic import ValidationError

from app.testing.inventory.contracts import (
    DiscoveryProvenance,
    DiscoveryStatus,
    RequirementLinkageType,
    TestInventoryConflict,
    TestTier,
    UnifiedTestDefinition,
    UnifiedTestInventory,
    compute_deterministic_inventory_id,
)


class TestUnifiedTestContracts:
    """Comprehensive tests for inventory contracts, models, and invariants."""

    def test_all_four_test_tiers_supported(self) -> None:
        """Verify all four mandatory test tiers are distinct and present."""
        tiers = [t.value for t in TestTier]
        assert "UNIT" in tiers
        assert "AI_TEST" in tiers
        assert "BROWSER_SMOKE" in tiers
        assert "BROWSER_JOURNEY" in tiers
        assert len(tiers) == 4

    def test_discovery_provenance_enums(self) -> None:
        """Verify explicit discovery provenance sources."""
        sources = [p.value for p in DiscoveryProvenance]
        assert "pytest_discovery" in sources
        assert "ai_test_suite" in sources
        assert "browser_smoke_suite" in sources
        assert "validated_browser_journey" in sources

    def test_discovery_status_enums(self) -> None:
        """Verify completeness statuses."""
        statuses = [s.value for s in DiscoveryStatus]
        assert "COMPLETE" in statuses
        assert "PARTIAL" in statuses
        assert "CONFLICT" in statuses

    def test_requirement_linkage_types(self) -> None:
        """Verify explicit vs inferred requirement linkage types."""
        assert RequirementLinkageType.EXPLICIT.value == "EXPLICIT"
        assert RequirementLinkageType.INFERRED.value == "INFERRED"

    def test_unified_test_definition_creation(self) -> None:
        """Verify valid UnifiedTestDefinition instantiation and normalization."""
        proj_id = uuid.uuid4()
        test_def = UnifiedTestDefinition(
            test_id=f"unit:{proj_id}:tests_test_auth_py__test_login",
            tier=TestTier.UNIT,
            name="test_login",
            description="Verifies login credentials validation",
            source_reference="tests/test_auth.py::test_login",
            project_id=str(proj_id),
            requirement_links=["REQ-001", "REQ-002"],
            inferred_requirement_links=[],
            discovery_source=DiscoveryProvenance.PYTEST_DISCOVERY,
            target_file="app/auth.py",
            target_symbol="authenticate_user",
            metadata={"line": 42},
        )

        assert test_def.tier == TestTier.UNIT
        assert test_def.name == "test_login"
        assert len(test_def.requirement_links) == 2
        assert test_def.project_id == str(proj_id).lower()
        assert test_def.metadata["line"] == 42

    def test_unified_test_definition_coerces_uuid_project_id(self) -> None:
        """Verify project_id passed as UUID object is normalized to string."""
        proj_uuid = uuid.uuid4()
        test_def = UnifiedTestDefinition(
            test_id="ai_test:123:test_calc",
            tier=TestTier.AI_TEST,
            name="test_calc",
            source_reference="app/calc.py::add",
            project_id=str(proj_uuid),
            discovery_source=DiscoveryProvenance.AI_TEST_SUITE,
        )
        assert test_def.project_id == str(proj_uuid).lower()

    def test_unified_test_definition_rejects_empty_or_whitespace_id(self) -> None:
        """Verify test_id cannot be whitespace or contain spaces."""
        with pytest.raises(ValidationError):
            UnifiedTestDefinition(
                test_id="   ",
                tier=TestTier.UNIT,
                name="test_invalid",
                source_reference="tests/test.py",
                project_id="proj-123",
                discovery_source=DiscoveryProvenance.PYTEST_DISCOVERY,
            )

        with pytest.raises(ValidationError):
            UnifiedTestDefinition(
                test_id="unit:proj:test with spaces",
                tier=TestTier.UNIT,
                name="test_spaces",
                source_reference="tests/test.py",
                project_id="proj-123",
                discovery_source=DiscoveryProvenance.PYTEST_DISCOVERY,
            )

    def test_compute_deterministic_inventory_id(self) -> None:
        """Verify deterministic inventory ID derivation from project and test IDs."""
        proj_id = "test-project-1"
        test_ids_a = ["unit:1:b", "unit:1:a", "ai:1:c"]
        test_ids_b = ["ai:1:c", "unit:1:a", "unit:1:b"]  # Different order

        id_a = compute_deterministic_inventory_id(proj_id, test_ids_a)
        id_b = compute_deterministic_inventory_id(proj_id, test_ids_b)

        assert id_a == id_b
        assert id_a.startswith("inv_test-pro_")

    def test_unified_test_inventory_query_methods(self) -> None:
        """Verify query helper methods on UnifiedTestInventory."""
        proj_id = "proj-xyz"
        t1 = UnifiedTestDefinition(
            test_id="unit:proj-xyz:t1",
            tier=TestTier.UNIT,
            name="test_unit_1",
            source_reference="tests/t1.py::test_1",
            project_id=proj_id,
            requirement_links=["REQ-A"],
            discovery_source=DiscoveryProvenance.PYTEST_DISCOVERY,
        )
        t2 = UnifiedTestDefinition(
            test_id="ai_test:proj-xyz:t2",
            tier=TestTier.AI_TEST,
            name="test_ai_2",
            source_reference="tests/t2.py::test_2",
            project_id=proj_id,
            requirement_links=["REQ-A", "REQ-B"],
            discovery_source=DiscoveryProvenance.AI_TEST_SUITE,
        )
        t3 = UnifiedTestDefinition(
            test_id="browser_journey:proj-xyz:t3",
            tier=TestTier.BROWSER_JOURNEY,
            name="Journey 3",
            source_reference="/dashboard",
            project_id=proj_id,
            requirement_links=[],  # Unlinked test
            discovery_source=DiscoveryProvenance.VALIDATED_BROWSER_JOURNEY,
        )

        tests = [t1, t2, t3]
        tests_by_id = {t.test_id: t for t in tests}
        tests_by_tier = {
            TestTier.UNIT.value: [t1.test_id],
            TestTier.AI_TEST.value: [t2.test_id],
            TestTier.BROWSER_JOURNEY.value: [t3.test_id],
        }
        tests_by_req = {
            "REQ-A": [t1.test_id, t2.test_id],
            "REQ-B": [t2.test_id],
        }
        reqs_by_test = {
            t1.test_id: ["REQ-A"],
            t2.test_id: ["REQ-A", "REQ-B"],
            t3.test_id: [],
        }

        inv_id = compute_deterministic_inventory_id(proj_id, [t.test_id for t in tests])

        inventory = UnifiedTestInventory(
            inventory_id=inv_id,
            project_id=proj_id,
            tests=tests,
            discovery_status=DiscoveryStatus.COMPLETE,
            conflicts=[],
            tests_by_id=tests_by_id,
            tests_by_tier=tests_by_tier,
            tests_by_requirement=tests_by_req,
            requirements_by_test=reqs_by_test,
            tier_counts={"UNIT": 1, "AI_TEST": 1, "BROWSER_JOURNEY": 1, "BROWSER_SMOKE": 0},
            total_tests=3,
        )

        # Test get_test
        assert inventory.get_test("unit:proj-xyz:t1") == t1
        assert inventory.get_test("unknown_id") is None

        # Test get_tests_by_tier
        unit_tests = inventory.get_tests_by_tier(TestTier.UNIT)
        assert len(unit_tests) == 1
        assert unit_tests[0].name == "test_unit_1"

        # Test get_tests_for_requirement
        req_a_tests = inventory.get_tests_for_requirement("REQ-A")
        assert len(req_a_tests) == 2
        assert {t.test_id for t in req_a_tests} == {t1.test_id, t2.test_id}

        req_b_tests = inventory.get_tests_for_requirement("REQ-B")
        assert len(req_b_tests) == 1
        assert req_b_tests[0].test_id == t2.test_id

        # Test get_requirements_for_test
        assert inventory.get_requirements_for_test(t2.test_id) == ["REQ-A", "REQ-B"]
        assert inventory.get_requirements_for_test(t3.test_id) == []

        # Test linked vs unlinked
        unlinked = inventory.get_unlinked_tests()
        assert len(unlinked) == 1
        assert unlinked[0].test_id == t3.test_id

        linked = inventory.get_linked_tests()
        assert len(linked) == 2

    def test_empty_inventory_defaults(self) -> None:
        """Verify empty inventory compiles with valid deterministic defaults."""
        inv_id = compute_deterministic_inventory_id("proj-empty", [])
        inventory = UnifiedTestInventory(
            inventory_id=inv_id,
            project_id="proj-empty",
            tests=[],
            discovery_status=DiscoveryStatus.COMPLETE,
            conflicts=[],
            tests_by_id={},
            tests_by_tier={},
            tests_by_requirement={},
            requirements_by_test={},
            tier_counts={},
            total_tests=0,
        )

        assert inventory.total_tests == 0
        assert inventory.discovery_status == DiscoveryStatus.COMPLETE
        assert len(inventory.tests) == 0
        assert inventory.get_linked_tests() == []
        assert inventory.get_unlinked_tests() == []

    def test_inventory_serialization_roundtrip(self) -> None:
        """Verify Pydantic model_dump and model_validate preserve all fields and types."""
        proj_id = "proj-roundtrip"
        t1 = UnifiedTestDefinition(
            test_id="unit:proj:test1",
            tier=TestTier.UNIT,
            name="test_1",
            source_reference="tests/test_1.py",
            project_id=proj_id,
            discovery_source=DiscoveryProvenance.PYTEST_DISCOVERY,
        )
        inv = UnifiedTestInventory(
            inventory_id="inv_proj_123",
            project_id=proj_id,
            tests=[t1],
            tests_by_id={t1.test_id: t1},
            total_tests=1,
        )

        dumped = inv.model_dump(mode="json")
        loaded = UnifiedTestInventory.model_validate(dumped)

        assert loaded.inventory_id == inv.inventory_id
        assert loaded.total_tests == 1
        assert loaded.tests[0].tier == TestTier.UNIT
