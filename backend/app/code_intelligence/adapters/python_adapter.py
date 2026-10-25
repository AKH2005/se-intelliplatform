"""Deterministic Python Language Adapter for Polyglot Code Intelligence (Phase 14).

Wraps and preserves existing ASTAnalyzer, extracting rich symbols, imports,
exports, and internal project dependencies while isolating syntax failures.
"""

import ast
import logging
import os
from typing import Any

from app.code_intelligence.adapters.base import BaseLanguageAdapter
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
    SymbolKind,
)
from app.sandbox.static_analysis.ast_analyzer import ASTAnalyzer
from app.sandbox.static_analysis.dependency_analyzer import PYTHON_STDLIB_MODULES

logger = logging.getLogger(__name__)


class PythonLanguageAdapter(BaseLanguageAdapter):
    """Authoritative adapter for Python source code analysis."""

    def __init__(self, ast_analyzer: ASTAnalyzer | None = None) -> None:
        self.ast_analyzer = ast_analyzer or ASTAnalyzer()

    @property
    def language(self) -> CodeLanguage:
        return CodeLanguage.PYTHON

    def parse(self, file_path: str, content: str) -> CodeFile:
        """Parse Python source and extract symbols, imports, and exports."""
        parsed_data, raw_diags = self.ast_analyzer.analyze_file(file_path, content)

        symbols: list[CodeSymbol] = []
        imports: list[CodeImport] = []
        exports: list[CodeExport] = []
        diagnostics: list[CodeDiagnostic] = []
        has_dynamic = False

        # 1. Translate raw ASTAnalyzer diagnostics to normalized CodeDiagnostic
        for d in raw_diags:
            diagnostics.append(
                CodeDiagnostic(
                    file_path=file_path,
                    language=self.language,
                    error_type=d.code,
                    line=d.line,
                    column=d.column,
                    message=d.message,
                    unsupported_construct=d.evidence,
                    severity=d.severity.value,
                )
            )

        if parsed_data.syntax_error is not None:
            return CodeFile(
                file_path=file_path,
                language=self.language,
                has_syntax_error=True,
                diagnostics=diagnostics,
            )

        tree = parsed_data.tree
        if tree is None:
            return CodeFile(file_path=file_path, language=self.language)

        # 2. Extract imports from AST
        for node in ast.iter_child_nodes(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.append(
                        CodeImport(
                            module=alias.name,
                            imported_symbols=[],
                            alias=alias.asname,
                            is_dynamic=False,
                            is_relative=False,
                            line_number=node.lineno,
                            raw_statement=f"import {alias.name}" + (f" as {alias.asname}" if alias.asname else ""),
                        )
                    )
            elif isinstance(node, ast.ImportFrom):
                mod = ("." * node.level) + (node.module or "")
                imported = [alias.name for alias in node.names]
                is_rel = node.level > 0
                imports.append(
                    CodeImport(
                        module=mod,
                        imported_symbols=imported,
                        is_dynamic=False,
                        is_relative=is_rel,
                        line_number=node.lineno,
                        raw_statement=f"from {mod} import {', '.join(imported)}",
                    )
                )

        # 3. Detect dynamic imports and forbidden calls
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                # __import__(...)
                if isinstance(node.func, ast.Name) and node.func.id == "__import__":
                    has_dynamic = True
                    imports.append(
                        CodeImport(
                            module="<dynamic>",
                            is_dynamic=True,
                            line_number=node.lineno,
                            raw_statement="__import__(...)",
                        )
                    )
                    diagnostics.append(
                        CodeDiagnostic(
                            file_path=file_path,
                            language=self.language,
                            error_type="DYNAMIC_IMPORT",
                            line=node.lineno,
                            message="Dynamic __import__(...) invocation detected.",
                            unsupported_construct="__import__",
                            severity="WARNING",
                        )
                    )
                # importlib.import_module(...)
                elif isinstance(node.func, ast.Attribute) and node.func.attr == "import_module":
                    has_dynamic = True
                    imports.append(
                        CodeImport(
                            module="<dynamic>",
                            is_dynamic=True,
                            line_number=node.lineno,
                            raw_statement="importlib.import_module(...)",
                        )
                    )
                    diagnostics.append(
                        CodeDiagnostic(
                            file_path=file_path,
                            language=self.language,
                            error_type="DYNAMIC_IMPORT",
                            line=node.lineno,
                            message="Dynamic importlib.import_module(...) invocation detected.",
                            unsupported_construct="import_module",
                            severity="WARNING",
                        )
                    )
                # eval / exec
                elif isinstance(node.func, ast.Name) and node.func.id in ("eval", "exec"):
                    has_dynamic = True

        # 4. Extract symbols (classes, methods, functions)
        for node in tree.body:
            # Classes
            if isinstance(node, ast.ClassDef):
                doc = ast.get_docstring(node)
                symbols.append(
                    CodeSymbol(
                        name=node.name,
                        kind=SymbolKind.CLASS,
                        qualified_name=node.name,
                        line_number=node.lineno,
                        column=node.col_offset,
                        language=self.language,
                        is_exported=not node.name.startswith("_"),
                        docstring=doc,
                    )
                )
                for item in node.body:
                    if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        m_doc = ast.get_docstring(item)
                        symbols.append(
                            CodeSymbol(
                                name=item.name,
                                kind=SymbolKind.CONSTRUCTOR if item.name == "__init__" else SymbolKind.METHOD,
                                qualified_name=f"{node.name}.{item.name}",
                                line_number=item.lineno,
                                column=item.col_offset,
                                language=self.language,
                                is_exported=not item.name.startswith("_"),
                                docstring=m_doc,
                                parent_symbol=node.name,
                            )
                        )
            # Functions
            elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                f_doc = ast.get_docstring(node)
                symbols.append(
                    CodeSymbol(
                        name=node.name,
                        kind=SymbolKind.FUNCTION,
                        qualified_name=node.name,
                        line_number=node.lineno,
                        column=node.col_offset,
                        language=self.language,
                        is_exported=not node.name.startswith("_"),
                        docstring=f_doc,
                    )
                )
            # __all__ export declaration
            elif isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name) and target.id == "__all__":
                        if isinstance(node.value, (ast.List, ast.Tuple)):
                            for elt in node.value.elts:
                                if isinstance(elt, ast.Constant) and isinstance(elt.value, str):
                                    exports.append(
                                        CodeExport(
                                            name=elt.value,
                                            line_number=node.lineno,
                                        )
                                    )

        # If __all__ not explicitly defined, export public top-level symbols
        if not exports:
            for s in symbols:
                if s.parent_symbol is None and not s.name.startswith("_"):
                    exports.append(
                        CodeExport(
                            name=s.name,
                            symbol_kind=s.kind,
                            line_number=s.line_number,
                        )
                    )

        return CodeFile(
            file_path=file_path,
            language=self.language,
            symbols=symbols,
            imports=imports,
            exports=exports,
            diagnostics=diagnostics,
            has_dynamic_constructs=has_dynamic,
        )

    def resolve_internal_dependencies(
        self,
        source_file: str,
        imports: list[CodeImport],
        all_files: list[str],
    ) -> list[CodeDependencyEdge]:
        """Resolve Python imports against project file tree."""
        edges: list[CodeDependencyEdge] = []
        normalized_files = [f.replace("\\", "/").strip("/") for f in all_files]
        file_set = set(normalized_files)

        # Mapping of module path to project file: app/models/foo.py -> app.models.foo
        module_to_file: dict[str, str] = {}
        for f in normalized_files:
            if f.endswith(".py"):
                mod = f[:-3].replace("/", ".")
                module_to_file[mod] = f
                # Also index package __init__.py as package module
                if mod.endswith(".__init__"):
                    pkg_mod = mod[:-9]
                    module_to_file[pkg_mod] = f

        source_dir = os.path.dirname(source_file).replace("\\", "/")

        for imp in imports:
            if imp.is_dynamic or imp.module == "<dynamic>":
                edges.append(
                    CodeDependencyEdge(
                        source_file=source_file,
                        target_file="<dynamic>",
                        relation=DependencyRelation.DYNAMIC_IMPORT,
                        authority=AuthorityClassification.DYNAMIC,
                        line_number=imp.line_number,
                        is_resolved=False,
                        notes="Dynamic import call cannot be statically resolved.",
                    )
                )
                continue

            raw_mod = imp.module
            # Skip python standard library
            top_pkg = raw_mod.split(".")[0].lstrip(".")
            if top_pkg in PYTHON_STDLIB_MODULES:
                continue

            resolved_path: str | None = None

            # Handle relative imports: from . import foo, from ..bar import baz
            if imp.is_relative:
                # Count leading dots
                dot_count = len(raw_mod) - len(raw_mod.lstrip("."))
                sub_mod = raw_mod.lstrip(".")
                
                cur_parts = [p for p in source_dir.split("/") if p]
                pop_count = dot_count - 1
                if pop_count <= len(cur_parts):
                    target_dir_parts = cur_parts[: len(cur_parts) - pop_count] if pop_count > 0 else cur_parts
                    target_prefix = "/".join(target_dir_parts)
                    cand_base = f"{target_prefix}/{sub_mod}".strip("/").replace(".", "/")
                    
                    for ext_cand in (f"{cand_base}.py", f"{cand_base}/__init__.py"):
                        if ext_cand in file_set:
                            resolved_path = ext_cand
                            break
            else:
                # Absolute internal import: app.services.foo -> app/services/foo.py
                if raw_mod in module_to_file:
                    resolved_path = module_to_file[raw_mod]
                else:
                    # Check file paths directly
                    cand = raw_mod.replace(".", "/")
                    for ext_cand in (f"{cand}.py", f"{cand}/__init__.py"):
                        if ext_cand in file_set:
                            resolved_path = ext_cand
                            break

            if resolved_path and resolved_path != source_file:
                rel = DependencyRelation.FROM_IMPORT if imp.imported_symbols else DependencyRelation.IMPORT
                edges.append(
                    CodeDependencyEdge(
                        source_file=source_file,
                        target_file=resolved_path,
                        relation=rel,
                        symbol=", ".join(imp.imported_symbols) if imp.imported_symbols else None,
                        authority=AuthorityClassification.DETERMINISTIC,
                        line_number=imp.line_number,
                        is_resolved=True,
                    )
                )
            elif not resolved_path and not imp.is_relative:
                # Check if imported symbol is a module file in package
                found_sym_file = False
                for sym in imp.imported_symbols:
                    cand_mod = f"{raw_mod}.{sym}"
                    if cand_mod in module_to_file:
                        sym_target = module_to_file[cand_mod]
                        if sym_target != source_file:
                            edges.append(
                                CodeDependencyEdge(
                                    source_file=source_file,
                                    target_file=sym_target,
                                    relation=DependencyRelation.FROM_IMPORT,
                                    symbol=sym,
                                    authority=AuthorityClassification.DETERMINISTIC,
                                    line_number=imp.line_number,
                                    is_resolved=True,
                                )
                            )
                            found_sym_file = True
                if not found_sym_file:
                    # External or third-party dependency
                    edges.append(
                        CodeDependencyEdge(
                            source_file=source_file,
                            target_file=raw_mod,
                            relation=DependencyRelation.IMPORT,
                            authority=AuthorityClassification.UNRESOLVED,
                            line_number=imp.line_number,
                            is_resolved=False,
                            notes=f"External or third-party package '{raw_mod}'.",
                        )
                    )

        return edges
