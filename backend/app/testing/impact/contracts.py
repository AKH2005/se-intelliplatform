"""Contracts and Data Models for Change Impact Intelligence (Phase 11L Stage 3).

Defines dependency graph models, relation types, impact reasons, uncertainty records,
and the aggregate ChangeImpactReport.
"""

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Sequence
from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.testing.inventory.contracts import UnifiedTestDefinition


class DependencyRelationType(str, Enum):
    """Categorical classification of code dependency relationships."""

    IMPORT = "IMPORT"
    FROM_IMPORT = "FROM_IMPORT"
    DYNAMIC_IMPORT = "DYNAMIC_IMPORT"
    TEST_TARGET = "TEST_TARGET"
    UNKNOWN = "UNKNOWN"


class AnalysisConfidence(str, Enum):
    """Confidence level of dependency and impact analysis."""

    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


class ImpactReason(str, Enum):
    """Deterministic reason an entity (file, test, requirement) is marked affected."""

    DIRECT_CHANGE = "DIRECT_CHANGE"
    DEPENDENCY_CLOSURE = "DEPENDENCY_CLOSURE"
    DIRECT_TEST_FILE = "DIRECT_TEST_FILE"
    AUTHORITATIVE_REQUIREMENT_LINK = "AUTHORITATIVE_REQUIREMENT_LINK"
    UNKNOWN_DEPENDENCY = "UNKNOWN_DEPENDENCY"
    BROWSER_ROUTE_OVERLAP = "BROWSER_ROUTE_OVERLAP"


class DependencyNode(BaseModel):
    """Node in the static dependency graph representing a project file."""

    model_config = ConfigDict(extra="forbid")

    file_path: str = Field(
        ...,
        min_length=1,
        description="Normalized relative project file path",
    )
    project_id: str = Field(
        ...,
        description="Parent project UUID string",
    )
    is_test_file: bool = Field(
        default=False,
        description="Whether this file was classified as a test file by TestDiscovery",
    )
    language: str = Field(
        default="python",
        description="Detected source language (e.g. 'python', 'unsupported')",
    )
    has_syntax_error: bool = Field(
        default=False,
        description="True if file had unparseable syntax errors during AST inspection",
    )
    has_dynamic_imports: bool = Field(
        default=False,
        description="True if file contains dynamic import calls (__import__, importlib, eval, exec)",
    )

    @field_validator("file_path", mode="before")
    @classmethod
    def normalize_file_path(cls, v: Any) -> str:
        return str(v).replace("\\", "/").strip("/")

    @field_validator("project_id", mode="before")
    @classmethod
    def normalize_project_id(cls, v: Any) -> str:
        return str(v).strip().lower()


class DependencyEdge(BaseModel):
    """Directed edge in the dependency graph: source_file depends on target_file."""

    model_config = ConfigDict(extra="forbid")

    source_file: str = Field(
        ...,
        description="File that declares the import/dependency (the dependent)",
    )
    target_file: str = Field(
        ...,
        description="File being imported or referenced (the dependency)",
    )
    relation_type: DependencyRelationType = Field(
        default=DependencyRelationType.IMPORT,
        description="Type of dependency link",
    )
    symbol: str | None = Field(
        default=None,
        description="Specific symbol imported (e.g. function, class), if applicable",
    )
    line_number: int | None = Field(
        default=None,
        description="Line number in source_file where dependency is declared",
    )
    is_resolved: bool = Field(
        default=True,
        description="True if target_file was resolved to an internal project file",
    )

    @field_validator("source_file", "target_file", mode="before")
    @classmethod
    def normalize_paths(cls, v: Any) -> str:
        return str(v).replace("\\", "/").strip("/")


class UncertainDependency(BaseModel):
    """Record of an unresolved or dynamic dependency that introduces uncertainty."""

    model_config = ConfigDict(extra="forbid")

    file_path: str = Field(
        ...,
        description="File where uncertain dependency was detected",
    )
    reason: str = Field(
        ...,
        description="Explanation of uncertainty (e.g. 'DYNAMIC_IMPORT_DETECTED', 'UNRESOLVED_IMPORT')",
    )
    line_number: int | None = Field(
        default=None,
        description="Line number where uncertainty was flagged",
    )
    raw_statement: str | None = Field(
        default=None,
        description="Raw code snippet or module string",
    )

    @field_validator("file_path", mode="before")
    @classmethod
    def normalize_file_path(cls, v: Any) -> str:
        return str(v).replace("\\", "/").strip("/")


class DependencyGraph(BaseModel):
    """Deterministic, queryable static dependency graph representing project source files."""

    model_config = ConfigDict(extra="forbid")

    project_id: str = Field(
        ...,
        description="Canonical project UUID string",
    )
    nodes: dict[str, DependencyNode] = Field(
        default_factory=dict,
        description="Map of normalized file_path -> DependencyNode",
    )
    edges: list[DependencyEdge] = Field(
        default_factory=list,
        description="All directed dependency edges (source_file -> target_file)",
    )
    forward_adjacency: dict[str, list[str]] = Field(
        default_factory=dict,
        description="source_file -> sorted list of files it depends on (dependencies)",
    )
    reverse_adjacency: dict[str, list[str]] = Field(
        default_factory=dict,
        description="target_file -> sorted list of files that depend on it (dependents)",
    )
    unresolved_imports: list[str] = Field(
        default_factory=list,
        description="Sorted list of import module strings that could not be resolved internally",
    )
    uncertain_dependencies: list[UncertainDependency] = Field(
        default_factory=list,
        description="Detailed uncertainty records encountered during graph construction",
    )

    @field_validator("project_id", mode="before")
    @classmethod
    def normalize_project_id(cls, v: Any) -> str:
        return str(v).strip().lower()

    # Graph Traversal Methods
    def get_direct_dependents(self, file_path: str) -> list[str]:
        """Retrieve files that directly import / depend on file_path."""
        clean = file_path.replace("\\", "/").strip("/")
        return list(self.reverse_adjacency.get(clean, []))

    def get_direct_dependencies(self, file_path: str) -> list[str]:
        """Retrieve files that file_path directly imports / depends on."""
        clean = file_path.replace("\\", "/").strip("/")
        return list(self.forward_adjacency.get(clean, []))

    def get_transitive_dependents(self, changed_files: Sequence[str]) -> list[str]:
        """Compute cycle-safe transitive closure of all files dependent on changed_files.
        
        If file B changed, and A imports B, and X imports A:
        changed: B
        direct dependent: A
        transitive dependents: A, X
        
        Handles circular dependencies (A -> B -> C -> A) deterministically without infinite loops.
        """
        visited: set[str] = set()
        queue: list[str] = []

        for f in changed_files:
            clean = f.replace("\\", "/").strip("/")
            if clean:
                visited.add(clean)
                queue.append(clean)

        transitive_dependents: set[str] = set()

        while queue:
            current = queue.pop(0)
            # Find all files that depend on `current`
            dependents = self.reverse_adjacency.get(current, [])
            for dep in dependents:
                if dep not in visited:
                    visited.add(dep)
                    transitive_dependents.add(dep)
                    queue.append(dep)

        return sorted(list(transitive_dependents))


class ChangeImpactReport(BaseModel):
    """Deterministic, comprehensive change impact report linking changes to tests and requirements."""

    __test__ = False
    model_config = ConfigDict(extra="forbid")

    project_id: str = Field(
        ...,
        description="Canonical project UUID string",
    )
    changed_files: list[str] = Field(
        default_factory=list,
        description="Sorted list of directly modified, added, or deleted files",
    )
    directly_affected_files: list[str] = Field(
        default_factory=list,
        description="Sorted list of files directly dependent on changed files",
    )
    transitively_affected_files: list[str] = Field(
        default_factory=list,
        description="Sorted list of files transitively affected through dependency closure",
    )
    all_affected_files: list[str] = Field(
        default_factory=list,
        description="Sorted union of changed, directly affected, and transitively affected files",
    )
    affected_tests: list[UnifiedTestDefinition] = Field(
        default_factory=list,
        description="Sorted list of potentially impacted test definitions",
    )
    affected_test_ids: list[str] = Field(
        default_factory=list,
        description="Sorted list of affected test IDs",
    )
    test_impact_reasons: dict[str, list[ImpactReason]] = Field(
        default_factory=dict,
        description="test_id -> list of deterministic impact reasons",
    )
    affected_requirements: list[str] = Field(
        default_factory=list,
        description="Sorted list of authoritative active requirements linked to affected tests",
    )
    requirement_impact_reasons: dict[str, list[ImpactReason]] = Field(
        default_factory=dict,
        description="requirement_id -> list of deterministic impact reasons",
    )
    uncertain_files: list[str] = Field(
        default_factory=list,
        description="Files where dependency analysis was uncertain or dynamic",
    )
    uncertain_dependencies: list[UncertainDependency] = Field(
        default_factory=list,
        description="Detailed records of uncertain or unresolvable dependencies",
    )
    requires_broader_regression: bool = Field(
        default=False,
        description="Conservative flag: True if uncertain dependencies necessitate broader regression",
    )
    analysis_confidence: AnalysisConfidence = Field(
        default=AnalysisConfidence.HIGH,
        description="Confidence assessment based on static certainty",
    )
    comparison_context: dict[str, Any] = Field(
        default_factory=dict,
        description="Contextual metadata regarding base and target versions",
    )
    calculated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Timestamp when change impact was computed",
    )
    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Sanitized telemetry and audit annotations",
    )

    @field_validator("project_id", mode="before")
    @classmethod
    def normalize_project_id(cls, v: Any) -> str:
        return str(v).strip().lower()

    # Query Helpers
    def is_test_affected(self, test_id: str) -> bool:
        """Check if a specific test_id is marked as affected."""
        return test_id in self.affected_test_ids

    def is_requirement_affected(self, requirement_id: str) -> bool:
        """Check if an active requirement is affected via authoritative tests."""
        clean_req = str(requirement_id).strip()
        return clean_req in self.affected_requirements

    def get_reasons_for_test(self, test_id: str) -> list[ImpactReason]:
        """Retrieve deterministic impact reasons for a given test."""
        return list(self.test_impact_reasons.get(test_id, []))

    def get_reasons_for_requirement(self, requirement_id: str) -> list[ImpactReason]:
        """Retrieve deterministic impact reasons for a given requirement."""
        clean_req = str(requirement_id).strip()
        return list(self.requirement_impact_reasons.get(clean_req, []))

    def __eq__(self, other: Any) -> bool:
        """Deterministic equivalence check comparing all logical impact properties.
        
        Volatile execution attributes like calculated_at are excluded.
        """
        if not isinstance(other, ChangeImpactReport):
            return False
        return (
            self.project_id == other.project_id
            and self.changed_files == other.changed_files
            and self.directly_affected_files == other.directly_affected_files
            and self.transitively_affected_files == other.transitively_affected_files
            and self.all_affected_files == other.all_affected_files
            and self.affected_test_ids == other.affected_test_ids
            and self.test_impact_reasons == other.test_impact_reasons
            and self.affected_requirements == other.affected_requirements
            and self.requirement_impact_reasons == other.requirement_impact_reasons
            and self.uncertain_files == other.uncertain_files
            and self.uncertain_dependencies == other.uncertain_dependencies
            and self.requires_broader_regression == other.requires_broader_regression
            and self.analysis_confidence == other.analysis_confidence
            and self.comparison_context == other.comparison_context
            and self.metadata == other.metadata
        )
