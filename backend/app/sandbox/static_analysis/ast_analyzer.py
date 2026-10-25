"""Deterministic Python AST Analysis and Structural Inspection."""

import ast
import logging
from typing import Any

from app.sandbox.static_analysis.contracts import (
    DiagnosticCategory,
    DiagnosticSeverity,
    StaticDiagnostic,
)

logger = logging.getLogger(__name__)


class ParsedModuleData:
    """Cached AST and structural extraction data for a single Python file."""

    def __init__(self, file_path: str, content: str) -> None:
        self.file_path = file_path
        self.content = content
        self.tree: ast.AST | None = None
        self.syntax_error: ast.SyntaxError | None = None
        self.imports: list[tuple[str, list[str], int]] = []  # (module, [names], line)
        self.functions: list[tuple[str, int]] = []  # (name, line)
        self.classes: list[tuple[str, int]] = []  # (name, line)
        self.dangerous_calls: list[tuple[str, int, int]] = []  # (func_name, line, col)


class ASTAnalyzer:
    """Performs single-pass AST parsing, syntax validation, and structure extraction."""

    def analyze_file(self, file_path: str, content: str) -> tuple[ParsedModuleData, list[StaticDiagnostic]]:
        """Parse Python source code once and extract structural diagnostics."""
        data = ParsedModuleData(file_path=file_path, content=content)
        diagnostics: list[StaticDiagnostic] = []

        try:
            tree = ast.parse(content, filename=file_path)
            data.tree = tree
        except SyntaxError as syn_err:
            data.syntax_error = syn_err
            diag = StaticDiagnostic(
                category=DiagnosticCategory.SYNTAX,
                severity=DiagnosticSeverity.ERROR,
                code="SYNTAX_ERROR",
                message=f"Syntax error: {syn_err.msg}",
                file_path=file_path,
                line=syn_err.lineno,
                column=syn_err.offset,
                source="ast",
                evidence=syn_err.text.strip() if syn_err.text else None,
            )
            diagnostics.append(diag)
            return data, diagnostics

        # Walk AST to extract imports, definitions, and security checks
        for node in ast.walk(tree):
            # Function definitions
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                data.functions.append((node.name, node.lineno))

            # Class definitions
            elif isinstance(node, ast.ClassDef):
                data.classes.append((node.name, node.lineno))

            # Regular imports: import foo, import foo.bar as b
            elif isinstance(node, ast.Import):
                for alias in node.names:
                    data.imports.append((alias.name, [], node.lineno))

            # From imports: from foo import bar, baz
            elif isinstance(node, ast.ImportFrom):
                mod_name = node.module or ""
                imported_names = [alias.name for alias in node.names]
                data.imports.append((mod_name, imported_names, node.lineno))

            # Security: check for eval() and exec()
            elif isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
                if node.func.id in ("eval", "exec"):
                    data.dangerous_calls.append((node.func.id, node.lineno, node.col_offset))
                    diagnostics.append(
                        StaticDiagnostic(
                            category=DiagnosticCategory.SECURITY,
                            severity=DiagnosticSeverity.CRITICAL,
                            code="FORBIDDEN_CALL",
                            message=f"Forbidden dynamic execution call '{node.func.id}()' detected.",
                            file_path=file_path,
                            line=node.lineno,
                            column=node.col_offset + 1,
                            source="ast",
                            evidence=f"{node.func.id}(...)",
                        )
                    )

        return data, diagnostics
