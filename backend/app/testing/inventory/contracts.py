"""Unified Test Inventory & Traceability Domain Contracts for Phase 11L Stage 1.

Provides a normalized, queryable, in-memory representation of project tests across
all four testing tiers (UNIT, AI_TEST, BROWSER_SMOKE, BROWSER_JOURNEY).

Architectural Invariants:
1. Purely deterministic representation: zero probabilistic heuristics or LLM calls.
2. Clear distinction between authoritative requirement links and candidate/inferred links.
3. Stable, deterministic identities derived strictly from test provenance (zero random UUIDs).
4. Strict project isolation: tests cannot cross project boundaries.
5. Zero execution authority: contracts describe test intent and provenance, never executing code.
"""

from datetime import datetime, timezone
from enum import Enum
import hashlib
from typing import Any
import uuid
from pydantic import BaseModel, ConfigDict, Field, field_validator


# ==============================================================================
# 1. Test Tier & Provenance Enumerations
# ==============================================================================

class TestTier(str, Enum):
    """Authoritative classification of application test tiers."""

    __test__ = False

    UNIT = "UNIT"
    AI_TEST = "AI_TEST"
    BROWSER_SMOKE = "BROWSER_SMOKE"
    BROWSER_JOURNEY = "BROWSER_JOURNEY"


class DiscoveryProvenance(str, Enum):
    """Source origin characterizing how a test definition was discovered/normalized."""

    PYTEST_DISCOVERY = "pytest_discovery"
    AI_TEST_SUITE = "ai_test_suite"
    BROWSER_SMOKE_SUITE = "browser_smoke_suite"
    VALIDATED_BROWSER_JOURNEY = "validated_browser_journey"


class DiscoveryStatus(str, Enum):
    """Completeness and integrity status of an inventory discovery cycle."""

    COMPLETE = "COMPLETE"
    PARTIAL = "PARTIAL"
    CONFLICT = "CONFLICT"


class RequirementLinkageType(str, Enum):
    """Epistemic classification of requirement traceability links."""

    EXPLICIT = "EXPLICIT"    # Authoritatively declared by test or validated journey
    INFERRED = "INFERRED"    # Heuristic, candidate, or unverified association


# ==============================================================================
# 2. Individual Unified Test Definition
# ==============================================================================

class UnifiedTestDefinition(BaseModel):
    """Normalized, strongly typed representation of an individual test case."""

    model_config = ConfigDict(extra="forbid")

    test_id: str = Field(
        ...,
        min_length=3,
        max_length=200,
        description="Deterministic, unique identifier for the test case (e.g. 'unit:proj_id:tests/test_x.py::test_fn')",
    )
    tier: TestTier = Field(
        ...,
        description="Functional test tier classification",
    )
    name: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description="Human-readable title or test function name",
    )
    description: str | None = Field(
        default=None,
        max_length=2000,
        description="Detailed description of the test scenario or assertion intent",
    )
    source_reference: str = Field(
        ...,
        min_length=1,
        max_length=500,
        description="Source code location, pytest node ID, or route reference",
    )
    project_id: str = Field(
        ...,
        min_length=1,
        max_length=64,
        description="Owner project UUID string",
    )
    requirement_links: list[str] = Field(
        default_factory=list,
        description="Authoritatively verified requirement IDs or titles explicitly linked to this test",
    )
    inferred_requirement_links: list[str] = Field(
        default_factory=list,
        description="Candidate or heuristic requirement links (strictly excluded from authoritative coverage)",
    )
    discovery_source: DiscoveryProvenance = Field(
        ...,
        description="Provenance origin mechanism producing this test definition",
    )
    target_file: str | None = Field(
        default=None,
        max_length=255,
        description="Project-relative path of the target source file under test, if known",
    )
    target_symbol: str | None = Field(
        default=None,
        max_length=150,
        description="Specific function, class, or endpoint symbol targeted by this test, if known",
    )
    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Sanitized metadata preserving execution preconditions or assertions",
    )

    @field_validator("project_id", mode="before")
    @classmethod
    def normalize_project_id(cls, v: Any) -> str:
        """Coerce UUID or string to clean lowercase string."""
        return str(v).strip().lower()

    @field_validator("test_id")
    @classmethod
    def validate_test_id_safety(cls, v: str) -> str:
        """Ensure test_id contains no whitespace, control characters, or invalid delimiters."""
        clean = v.strip()
        if not clean:
            raise ValueError("test_id cannot be empty.")
        if any(c.isspace() for c in clean):
            raise ValueError(f"test_id cannot contain whitespace characters: '{clean}'")
        return clean


# ==============================================================================
# 3. Conflict and Inventory Models
# ==============================================================================

class TestInventoryConflict(BaseModel):
    """Records a collision or conflict between two test definitions sharing identical IDs."""

    __test__ = False

    model_config = ConfigDict(extra="forbid")

    test_id: str = Field(..., description="Colliding deterministic test ID")
    existing_source: str = Field(..., description="Source reference of the first encountered definition")
    conflicting_source: str = Field(..., description="Source reference of the colliding definition")
    message: str = Field(..., description="Descriptive explanation of the conflict")


class UnifiedTestInventory(BaseModel):
    """Authoritative, queryable catalog of all tests across tiers for a project."""

    model_config = ConfigDict(extra="forbid")

    inventory_id: str = Field(
        ...,
        min_length=5,
        max_length=100,
        description="Deterministic identifier derived from project_id and sorted test_ids",
    )
    project_id: str = Field(
        ...,
        min_length=1,
        max_length=64,
        description="Owner project UUID string",
    )
    tests: list[UnifiedTestDefinition] = Field(
        default_factory=list,
        description="Complete list of normalized test definitions",
    )
    discovery_status: DiscoveryStatus = Field(
        default=DiscoveryStatus.COMPLETE,
        description="Completeness status of the inventory discovery process",
    )
    conflicts: list[TestInventoryConflict] = Field(
        default_factory=list,
        description="Detected duplicate ID collisions or unresolvable test references",
    )
    tests_by_id: dict[str, UnifiedTestDefinition] = Field(
        default_factory=dict,
        description="Direct test_id lookup index",
    )
    tests_by_tier: dict[str, list[str]] = Field(
        default_factory=dict,
        description="TestTier value -> list of test_ids index",
    )
    tests_by_requirement: dict[str, list[str]] = Field(
        default_factory=dict,
        description="Bidirectional index: Requirement ID -> sorted list of linked test_ids",
    )
    requirements_by_test: dict[str, list[str]] = Field(
        default_factory=dict,
        description="Bidirectional index: Test ID -> sorted list of linked requirement IDs",
    )
    tier_counts: dict[str, int] = Field(
        default_factory=dict,
        description="Count of tests in each TestTier",
    )
    total_tests: int = Field(
        default=0,
        ge=0,
        description="Total count of discovered, non-conflicting tests",
    )
    discovered_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Timestamp when inventory was compiled",
    )
    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Discovery telemetry and source descriptors",
    )

    @field_validator("project_id", mode="before")
    @classmethod
    def normalize_project_id(cls, v: Any) -> str:
        return str(v).strip().lower()

    # Query Helper Methods
    def get_test(self, test_id: str) -> UnifiedTestDefinition | None:
        """Retrieve a test definition by its deterministic test_id."""
        return self.tests_by_id.get(test_id)

    def get_tests_by_tier(self, tier: TestTier | str) -> list[UnifiedTestDefinition]:
        """Retrieve all tests belonging to a specific TestTier."""
        tier_key = tier.value if isinstance(tier, TestTier) else str(tier)
        test_ids = self.tests_by_tier.get(tier_key, [])
        return [self.tests_by_id[tid] for tid in test_ids if tid in self.tests_by_id]

    def get_tests_for_requirement(self, requirement_id: str) -> list[UnifiedTestDefinition]:
        """Retrieve all tests authoritatively linked to a specific requirement ID."""
        clean_req = str(requirement_id).strip()
        test_ids = self.tests_by_requirement.get(clean_req, [])
        return [self.tests_by_id[tid] for tid in test_ids if tid in self.tests_by_id]

    def get_requirements_for_test(self, test_id: str) -> list[str]:
        """Retrieve all requirement IDs authoritatively linked to a specific test ID."""
        return self.requirements_by_test.get(test_id, [])

    def get_unlinked_tests(self) -> list[UnifiedTestDefinition]:
        """Retrieve tests that have no authoritative requirement links."""
        return [t for t in self.tests if len(t.requirement_links) == 0]

    def get_linked_tests(self) -> list[UnifiedTestDefinition]:
        """Retrieve tests that have at least one authoritative requirement link."""
        return [t for t in self.tests if len(t.requirement_links) > 0]

    def __eq__(self, other: Any) -> bool:
        """Deterministic equivalence check comparing all logical inventory properties.
        
        Volatile execution attributes like discovered_at are excluded to ensure deterministic equality.
        """
        if not isinstance(other, UnifiedTestInventory):
            return False
        return (
            self.inventory_id == other.inventory_id
            and self.project_id == other.project_id
            and self.discovery_status == other.discovery_status
            and self.tests == other.tests
            and self.conflicts == other.conflicts
            and self.tests_by_id == other.tests_by_id
            and self.tests_by_tier == other.tests_by_tier
            and self.tests_by_requirement == other.tests_by_requirement
            and self.requirements_by_test == other.requirements_by_test
            and self.tier_counts == other.tier_counts
            and self.total_tests == other.total_tests
            and self.metadata == other.metadata
        )


def compute_deterministic_inventory_id(project_id: str, test_ids: list[str]) -> str:
    """Compute a deterministic hash ID from sorted test IDs and project_id."""
    clean_proj = str(project_id).strip().lower()
    sorted_ids = sorted(test_ids)
    payload = f"{clean_proj}:" + ",".join(sorted_ids)
    digest = hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]
    return f"inv_{clean_proj[:8]}_{digest}"
