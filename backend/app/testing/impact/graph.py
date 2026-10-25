"""Static AST Dependency Graph Builder for Project Source Files (Phase 11L Stage 3).

Analyzes project source files via ASTAnalyzer and constructs a deterministic directed graph:
source_file -> target_file (source depends on target).
"""

import ast
import logging
import uuid
from typing import Any

from app.code_intelligence.contracts import AuthorityClassification, CodeLanguage
from app.code_intelligence.detector import LanguageDetector
from app.code_intelligence.registry import LanguageAdapterRegistry, get_default_registry
from app.sandbox.static_analysis.ast_analyzer import ASTAnalyzer
from app.sandbox.static_analysis.dependency_analyzer import PYTHON_STDLIB_MODULES
from app.sandbox.static_analysis.test_discovery import TestDiscovery
from app.testing.impact.contracts import (
    DependencyEdge,
    DependencyGraph,
    DependencyNode,
    DependencyRelationType,
    UncertainDependency,
)

logger = logging.getLogger(__name__)


class ASTDependencyGraphBuilder:
    """Constructs a deterministic static dependency graph from project source code."""

    def __init__(
        self,
        ast_analyzer: ASTAnalyzer | None = None,
        test_discovery: TestDiscovery | None = None,
        polyglot_registry: LanguageAdapterRegistry | None = None,
        enable_polyglot: bool = False,
    ) -> None:
        self.ast_analyzer = ast_analyzer or ASTAnalyzer()
        self.test_discovery = test_discovery or TestDiscovery()
        self.polyglot_registry = polyglot_registry or get_default_registry()
        self.enable_polyglot = enable_polyglot

    def build_graph(
        self,
        project_id: uuid.UUID | str,
        files_map: dict[str, str],
        enable_polyglot: bool | None = None,
    ) -> DependencyGraph:
        """Parse all project files and compile a directed dependency graph.
        
        Args:
            project_id: Target project UUID or string.
            files_map: Mapping of relative project file paths to source code strings.
            enable_polyglot: Optional override to enable multi-language adapter parsing.
            
        Returns:
            DependencyGraph: Complete deterministic dependency graph with adjacency indexes.
        """
        clean_proj = str(project_id).strip().lower()
        use_polyglot = self.enable_polyglot if enable_polyglot is None else enable_polyglot

        # Normalize and sort file paths deterministically
        normalized_files: dict[str, str] = {
            p.replace("\\", "/").strip("/"): content
            for p, content in files_map.items()
        }
        sorted_paths = sorted(normalized_files.keys())

        nodes: dict[str, DependencyNode] = {}
        edges: list[DependencyEdge] = []
        forward_adj: dict[str, set[str]] = {p: set() for p in sorted_paths}
        reverse_adj: dict[str, set[str]] = {p: set() for p in sorted_paths}
        unresolved_imports: set[str] = set()
        uncertain_deps: list[UncertainDependency] = []
        polyglot_parsed: dict[str, Any] = {}

        # 1. First Pass: Create Nodes and detect language / syntax status
        for file_path in sorted_paths:
            content = normalized_files[file_path]
            is_py = file_path.endswith(".py")
            is_test = self.test_discovery.is_test_file(file_path) if is_py else LanguageDetector.is_test_file(file_path)

            if not is_py:
                if use_polyglot:
                    lang = LanguageDetector.detect(file_path, content)
                    adapter = self.polyglot_registry.get_adapter(lang)
                    if adapter:
                        cf = adapter.safe_parse(file_path, content)
                        polyglot_parsed[file_path] = (cf, adapter)

                        if cf.has_syntax_error:
                            uncertain_deps.append(
                                UncertainDependency(
                                    file_path=file_path,
                                    reason="SYNTAX_ERROR",
                                    raw_statement=cf.diagnostics[0].message if cf.diagnostics else None,
                                )
                            )
                        if cf.has_dynamic_constructs:
                            uncertain_deps.append(
                                UncertainDependency(
                                    file_path=file_path,
                                    reason="DYNAMIC_CONSTRUCT_DETECTED",
                                    raw_statement="Dynamic import/reflection/eval detected",
                                )
                            )

                        nodes[file_path] = DependencyNode(
                            file_path=file_path,
                            project_id=clean_proj,
                            is_test_file=is_test,
                            language=lang.value,
                            has_syntax_error=cf.has_syntax_error,
                            has_dynamic_imports=cf.has_dynamic_constructs,
                        )
                        continue

                nodes[file_path] = DependencyNode(
                    file_path=file_path,
                    project_id=clean_proj,
                    is_test_file=False,
                    language="unsupported",
                    has_syntax_error=False,
                    has_dynamic_imports=False,
                )
                continue

            parsed_data, diags = self.ast_analyzer.analyze_file(file_path, content)

            has_syntax_err = parsed_data.syntax_error is not None
            if has_syntax_err and parsed_data.syntax_error:
                uncertain_deps.append(
                    UncertainDependency(
                        file_path=file_path,
                        reason="SYNTAX_ERROR",
                        line_number=parsed_data.syntax_error.lineno,
                        raw_statement=parsed_data.syntax_error.text.strip() if parsed_data.syntax_error.text else None,
                    )
                )

            # Check for dynamic execution or dynamic imports
            has_dynamic_imp = False
            if parsed_data.tree:
                for node in ast.walk(parsed_data.tree):
                    if isinstance(node, ast.Call):
                        # Detect __import__(...)
                        if isinstance(node.func, ast.Name) and node.func.id == "__import__":
                            has_dynamic_imp = True
                            uncertain_deps.append(
                                UncertainDependency(
                                    file_path=file_path,
                                    reason="DYNAMIC_IMPORT_CALL",
                                    line_number=node.lineno,
                                    raw_statement="__import__(...)",
                                )
                            )
                        # Detect importlib.import_module(...)
                        elif isinstance(node.func, ast.Attribute) and node.func.attr == "import_module":
                            has_dynamic_imp = True
                            uncertain_deps.append(
                                UncertainDependency(
                                    file_path=file_path,
                                    reason="IMPORTLIB_DYNAMIC_IMPORT",
                                    line_number=node.lineno,
                                    raw_statement="importlib.import_module(...)",
                                )
                            )
                        # Detect eval() or exec()
                        elif isinstance(node.func, ast.Name) and node.func.id in ("eval", "exec"):
                            has_dynamic_imp = True
                            uncertain_deps.append(
                                UncertainDependency(
                                    file_path=file_path,
                                    reason=f"DYNAMIC_CODE_EXECUTION_{node.func.id.upper()}",
                                    line_number=node.lineno,
                                    raw_statement=f"{node.func.id}(...)",
                                )
                            )

            nodes[file_path] = DependencyNode(
                file_path=file_path,
                project_id=clean_proj,
                is_test_file=is_test,
                language="python",
                has_syntax_error=has_syntax_err,
                has_dynamic_imports=has_dynamic_imp,
            )

            # 2. Extract and resolve dependencies from AST imports
            if parsed_data.tree:
                seen_edge_signatures: set[tuple[str, str, str]] = set()

                for mod_name, imported_names, line_no in parsed_data.imports:
                    clean_mod = mod_name.strip()
                    top_pkg = clean_mod.split(".")[0].lstrip(".")

                    # Skip standard library modules
                    if top_pkg in PYTHON_STDLIB_MODULES:
                        continue

                    # Attempt to resolve internally within project files
                    resolved_targets = self._resolve_internal_targets(
                        source_path=file_path,
                        module_name=clean_mod,
                        imported_names=imported_names,
                        all_files=sorted_paths,
                    )

                    if resolved_targets:
                        for target_path, symbol in resolved_targets:
                            edge_sig = (file_path, target_path, symbol or "")
                            if edge_sig in seen_edge_signatures:
                                continue
                            seen_edge_signatures.add(edge_sig)

                            rel_type = DependencyRelationType.FROM_IMPORT if imported_names else DependencyRelationType.IMPORT
                            edges.append(
                                DependencyEdge(
                                    source_file=file_path,
                                    target_file=target_path,
                                    relation_type=rel_type,
                                    symbol=symbol,
                                    line_number=line_no,
                                    is_resolved=True,
                                )
                            )
                            forward_adj[file_path].add(target_path)
                            reverse_adj[target_path].add(file_path)
                    else:
                        # Could not resolve internally
                        if clean_mod and not clean_mod.startswith("."):
                            unresolved_imports.add(clean_mod)

        # 2b. Extract and resolve dependencies from Polyglot files (JS, TS, Java)
        for file_path, (cf, adapter) in polyglot_parsed.items():
            if cf.imports:
                p_edges = adapter.resolve_internal_dependencies(
                    source_file=file_path,
                    imports=cf.imports,
                    all_files=sorted_paths,
                )
                for pe in p_edges:
                    if pe.is_resolved and pe.target_file in normalized_files:
                        edges.append(
                            DependencyEdge(
                                source_file=pe.source_file,
                                target_file=pe.target_file,
                                relation_type=DependencyRelationType.IMPORT,
                                symbol=pe.symbol,
                                line_number=pe.line_number,
                                is_resolved=True,
                            )
                        )
                        forward_adj[file_path].add(pe.target_file)
                        reverse_adj[pe.target_file].add(file_path)
                    elif not pe.is_resolved:
                        unresolved_imports.add(pe.target_file)
                        if pe.authority == AuthorityClassification.DYNAMIC:
                            uncertain_deps.append(
                                UncertainDependency(
                                    file_path=file_path,
                                    reason="UNRESOLVED_DYNAMIC_IMPORT",
                                    line_number=pe.line_number,
                                    raw_statement=pe.target_file,
                                )
                            )

        # Sort all lists deterministically
        final_forward: dict[str, list[str]] = {p: sorted(list(targets)) for p, targets in forward_adj.items()}
        final_reverse: dict[str, list[str]] = {p: sorted(list(sources)) for p, sources in reverse_adj.items()}

        return DependencyGraph(
            project_id=clean_proj,
            nodes=nodes,
            edges=edges,
            forward_adjacency=final_forward,
            reverse_adjacency=final_reverse,
            unresolved_imports=sorted(list(unresolved_imports)),
            uncertain_dependencies=uncertain_deps,
        )

    # ==========================================================================
    # Internal Target Resolution
    # ==========================================================================

    def _resolve_internal_targets(
        self,
        source_path: str,
        module_name: str,
        imported_names: list[str],
        all_files: list[str],
    ) -> list[tuple[str, str | None]]:
        """Resolve a Python import to matching internal project source files."""
        resolved: list[tuple[str, str | None]] = []
        source_dir = "/".join(source_path.split("/")[:-1])

        # 1. Handle relative imports (e.g. from . import foo, from .bar import baz)
        if module_name.startswith("."):
            dots_count = len(module_name) - len(module_name.lstrip("."))
            remainder = module_name.lstrip(".")
            dir_parts = source_dir.split("/") if source_dir else []
            # Go up dots_count - 1 levels
            steps_up = dots_count - 1
            if steps_up <= len(dir_parts):
                target_base_dir = "/".join(dir_parts[:len(dir_parts) - steps_up]) if steps_up > 0 else source_dir
                target_prefix = f"{target_base_dir}/{remainder}".strip("/") if remainder else target_base_dir
                target_py = f"{target_prefix}.py".strip("/")
                target_init = f"{target_prefix}/__init__.py".strip("/")

                if target_py in all_files:
                    resolved.append((target_py, None))
                elif target_init in all_files:
                    resolved.append((target_init, None))

                # Check imported names as files in target_prefix directory
                for sym in imported_names:
                    cand = f"{target_prefix}/{sym}.py".strip("/")
                    if cand in all_files:
                        resolved.append((cand, sym))

            return resolved

        # 2. Handle absolute module imports (e.g. app.calculator -> app/calculator.py)
        mod_as_path = module_name.replace(".", "/")
        cand_direct_py = f"{mod_as_path}.py"
        cand_init_py = f"{mod_as_path}/__init__.py"

        if cand_direct_py in all_files:
            resolved.append((cand_direct_py, None))
        elif cand_init_py in all_files:
            resolved.append((cand_init_py, None))

        # 3. Check if imported names are modules within the target package
        # Example: from app import calculator -> app/calculator.py
        for sym in imported_names:
            cand_sym_py = f"{mod_as_path}/{sym}.py"
            cand_sym_init = f"{mod_as_path}/{sym}/__init__.py"
            if cand_sym_py in all_files:
                resolved.append((cand_sym_py, sym))
            elif cand_sym_init in all_files:
                resolved.append((cand_sym_init, sym))

        # 4. Check relative to source_dir if not found in root
        if not resolved and source_dir:
            cand_local_py = f"{source_dir}/{mod_as_path}.py"
            cand_local_init = f"{source_dir}/{mod_as_path}/__init__.py"
            if cand_local_py in all_files:
                resolved.append((cand_local_py, None))
            elif cand_local_init in all_files:
                resolved.append((cand_local_init, None))

        return resolved
