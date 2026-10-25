"""Deterministic Polyglot Dependency Graph Builder (Phase 14).

Constructs unified multi-language dependency graphs with forward and reverse
adjacency indexing, cross-language resolution, and full Phase 11L compatibility.
"""

from collections import defaultdict
from datetime import datetime, timezone
import logging
from typing import Any
import uuid

from app.code_intelligence.contracts import (
    AuthorityClassification,
    CodeDependencyEdge,
    CodeDiagnostic,
    CodeFile,
    CodeLanguage,
    DependencyRelation,
    PolyglotDependencyGraph,
)
from app.code_intelligence.detector import LanguageDetector
from app.code_intelligence.registry import LanguageAdapterRegistry, get_default_registry
from app.testing.impact.contracts import (
    DependencyEdge as LegacyDependencyEdge,
    DependencyGraph as LegacyDependencyGraph,
    DependencyNode as LegacyDependencyNode,
    DependencyRelationType as LegacyRelationType,
    UncertainDependency as LegacyUncertainDependency,
)

logger = logging.getLogger(__name__)


class PolyglotDependencyGraphBuilder:
    """Builds unified multi-language dependency graphs for projects."""

    def __init__(self, registry: LanguageAdapterRegistry | None = None) -> None:
        self.registry = registry or get_default_registry()

    def build_graph(
        self,
        project_id: uuid.UUID | str,
        files_map: dict[str, str],
    ) -> PolyglotDependencyGraph:
        """Parse all project files across supported languages and compile unified dependency graph."""
        clean_proj = str(project_id).strip().lower()

        # 1. Normalize paths deterministically
        normalized_files: dict[str, str] = {
            p.replace("\\", "/").strip("/"): content
            for p, content in files_map.items()
        }
        sorted_paths = sorted(normalized_files.keys())

        code_files: dict[str, CodeFile] = {}
        all_edges: list[CodeDependencyEdge] = []
        forward_adj: dict[str, set[str]] = {p: set() for p in sorted_paths}
        reverse_adj: dict[str, set[str]] = {p: set() for p in sorted_paths}
        language_counts: dict[str, int] = defaultdict(int)
        unresolved_set: set[str] = set()
        uncertain_records: list[dict[str, Any]] = []
        all_diagnostics: list[CodeDiagnostic] = []
        total_symbols = 0

        # 2. First Pass: Parse files and extract local metadata
        for file_path in sorted_paths:
            content = normalized_files[file_path]
            lang = LanguageDetector.detect(file_path, content)
            language_counts[lang.value] += 1

            adapter = self.registry.get_adapter(lang)
            if adapter:
                code_file = adapter.safe_parse(file_path, content)
            else:
                # Unsupported language
                code_file = CodeFile(
                    file_path=file_path,
                    language=lang,
                    is_test_file=LanguageDetector.is_test_file(file_path),
                    has_syntax_error=False,
                )

            code_files[file_path] = code_file
            total_symbols += len(code_file.symbols)
            all_diagnostics.extend(code_file.diagnostics)

            # Record uncertainties for regression planning
            if code_file.has_syntax_error:
                uncertain_records.append({
                    "file_path": file_path,
                    "language": lang.value,
                    "reason": "SYNTAX_ERROR",
                    "diagnostics": [d.message for d in code_file.diagnostics],
                })

            if code_file.has_dynamic_constructs:
                uncertain_records.append({
                    "file_path": file_path,
                    "language": lang.value,
                    "reason": "DYNAMIC_CONSTRUCT_DETECTED",
                    "diagnostics": [d.message for d in code_file.diagnostics if "DYNAMIC" in d.error_type or "REFLECTION" in d.error_type],
                })

        # 3. Second Pass: Resolve internal and cross-language dependencies
        for file_path in sorted_paths:
            code_file = code_files[file_path]
            adapter = self.registry.get_adapter(code_file.language)

            if adapter and code_file.imports:
                edges = adapter.resolve_internal_dependencies(
                    source_file=file_path,
                    imports=code_file.imports,
                    all_files=sorted_paths,
                )
                code_file.dependencies = edges

                for edge in edges:
                    all_edges.append(edge)
                    if edge.is_resolved and edge.target_file in normalized_files:
                        forward_adj[file_path].add(edge.target_file)
                        reverse_adj[edge.target_file].add(file_path)
                    elif not edge.is_resolved:
                        unresolved_set.add(edge.target_file)
                        if edge.authority == AuthorityClassification.DYNAMIC:
                            uncertain_records.append({
                                "file_path": file_path,
                                "language": code_file.language.value,
                                "reason": "UNRESOLVED_DYNAMIC_IMPORT",
                                "target": edge.target_file,
                                "line_number": edge.line_number,
                            })

        # Deterministic sorting
        final_forward: dict[str, list[str]] = {p: sorted(list(targets)) for p, targets in forward_adj.items()}
        final_reverse: dict[str, list[str]] = {p: sorted(list(sources)) for p, sources in reverse_adj.items()}

        return PolyglotDependencyGraph(
            project_id=clean_proj,
            files=code_files,
            edges=all_edges,
            forward_adjacency=final_forward,
            reverse_adjacency=final_reverse,
            language_breakdown=dict(sorted(language_counts.items())),
            unresolved_imports=sorted(list(unresolved_set)),
            uncertain_dependencies=uncertain_records,
            diagnostics=all_diagnostics,
            total_symbols=total_symbols,
            analyzed_at=datetime.now(timezone.utc),
        )

    def to_legacy_dependency_graph(
        self,
        poly_graph: PolyglotDependencyGraph,
    ) -> LegacyDependencyGraph:
        """Convert PolyglotDependencyGraph to Phase 11L DependencyGraph contract with 100% fidelity."""
        legacy_nodes: dict[str, LegacyDependencyNode] = {}

        for path, cf in poly_graph.files.items():
            legacy_nodes[path] = LegacyDependencyNode(
                file_path=path,
                project_id=poly_graph.project_id,
                is_test_file=cf.is_test_file,
                language=cf.language.value,
                has_syntax_error=cf.has_syntax_error,
                has_dynamic_imports=cf.has_dynamic_constructs,
            )

        legacy_edges: list[LegacyDependencyEdge] = []
        for e in poly_graph.edges:
            rel_map = {
                DependencyRelation.IMPORT: LegacyRelationType.IMPORT,
                DependencyRelation.FROM_IMPORT: LegacyRelationType.FROM_IMPORT,
                DependencyRelation.DYNAMIC_IMPORT: LegacyRelationType.DYNAMIC_IMPORT,
                DependencyRelation.TEST_TARGET: LegacyRelationType.TEST_TARGET,
            }
            leg_rel = rel_map.get(e.relation, LegacyRelationType.IMPORT)
            legacy_edges.append(
                LegacyDependencyEdge(
                    source_file=e.source_file,
                    target_file=e.target_file,
                    relation_type=leg_rel,
                    symbol=e.symbol,
                    line_number=e.line_number,
                    is_resolved=e.is_resolved,
                )
            )

        legacy_uncertain: list[LegacyUncertainDependency] = []
        for u in poly_graph.uncertain_dependencies:
            legacy_uncertain.append(
                LegacyUncertainDependency(
                    file_path=u.get("file_path", ""),
                    reason=u.get("reason", "UNCERTAIN_DEPENDENCY"),
                    line_number=u.get("line_number"),
                    raw_statement=u.get("target") or (u.get("diagnostics")[0] if u.get("diagnostics") else None),
                )
            )

        return LegacyDependencyGraph(
            project_id=poly_graph.project_id,
            nodes=legacy_nodes,
            edges=legacy_edges,
            forward_adjacency=poly_graph.forward_adjacency,
            reverse_adjacency=poly_graph.reverse_adjacency,
            unresolved_imports=poly_graph.unresolved_imports,
            uncertain_dependencies=legacy_uncertain,
        )
