"""Phase 14 Polyglot Code Intelligence Package.

Provides normalized intermediate representation, deterministic language adapters,
polyglot dependency graph computation, and multi-language impact analysis for
Python, JavaScript, TypeScript, Java, and extensible targets.
"""

from app.code_intelligence.contracts import (
    AuthorityClassification,
    CodeDependencyEdge,
    CodeDiagnostic,
    CodeExport,
    CodeFile,
    CodeImport,
    CodeLanguage,
    CodeSymbol,
    DependencyRelation,
    PolyglotDependencyGraph,
    SymbolKind,
)
from app.code_intelligence.detector import LanguageDetector
from app.code_intelligence.graph_builder import PolyglotDependencyGraphBuilder
from app.code_intelligence.registry import LanguageAdapterRegistry, get_default_registry
from app.code_intelligence.service import PolyglotCodeIntelligenceService

__all__ = [
    "CodeLanguage",
    "SymbolKind",
    "DependencyRelation",
    "AuthorityClassification",
    "CodeDiagnostic",
    "CodeSymbol",
    "CodeImport",
    "CodeExport",
    "CodeDependencyEdge",
    "CodeFile",
    "PolyglotDependencyGraph",
    "LanguageDetector",
    "LanguageAdapterRegistry",
    "get_default_registry",
    "PolyglotDependencyGraphBuilder",
    "PolyglotCodeIntelligenceService",
]
