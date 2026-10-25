"""AST Dependency Graph and Change Impact Intelligence Package (Phase 11L Stage 3).

Provides deterministic static dependency graphing, transitive impact calculation,
conservative uncertainty over-selection, and affected test/requirement mapping.
"""

from app.testing.impact.contracts import (
    AnalysisConfidence,
    ChangeImpactReport,
    DependencyEdge,
    DependencyGraph,
    DependencyNode,
    DependencyRelationType,
    ImpactReason,
    UncertainDependency,
)
from app.testing.impact.errors import (
    ChangeImpactError,
    ChangeImpactIsolationError,
    ChangeImpactValidationError,
)
from app.testing.impact.graph import ASTDependencyGraphBuilder
from app.testing.impact.service import ChangeImpactService

__all__ = [
    "AnalysisConfidence",
    "ChangeImpactReport",
    "DependencyEdge",
    "DependencyGraph",
    "DependencyNode",
    "DependencyRelationType",
    "ImpactReason",
    "UncertainDependency",
    "ChangeImpactError",
    "ChangeImpactIsolationError",
    "ChangeImpactValidationError",
    "ASTDependencyGraphBuilder",
    "ChangeImpactService",
]
