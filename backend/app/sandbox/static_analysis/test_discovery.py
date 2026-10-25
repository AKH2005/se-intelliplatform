"""Deterministic Test File and Test Case Discovery without Execution."""

import logging
from typing import Any

from app.sandbox.static_analysis.ast_analyzer import ParsedModuleData
from app.sandbox.static_analysis.contracts import (
    DiagnosticCategory,
    DiagnosticSeverity,
    StaticDiagnostic,
)

logger = logging.getLogger(__name__)


class TestDiscovery:
    """Discovers pytest test files and test functions statically via AST."""

    def is_test_file(self, path: str) -> bool:
        """Determine whether a file path conforms to pytest discovery conventions."""
        filename = path.strip("/").split("/")[-1].lower()
        if not filename.endswith(".py"):
            return False
        return (
            filename.startswith("test_")
            or filename.endswith("_test.py")
            or "/tests/" in f"/{path}/"
            or path.startswith("tests/")
        )

    def discover(self, modules: list[ParsedModuleData]) -> tuple[list[str], int, list[StaticDiagnostic]]:
        """Identify test files and count test functions/classes."""
        test_files: list[str] = []
        total_test_functions = 0
        diagnostics: list[StaticDiagnostic] = []

        for mod in modules:
            if not self.is_test_file(mod.file_path):
                continue

            test_files.append(mod.file_path)
            # Count test functions and test classes
            file_test_count = sum(1 for name, _ in mod.functions if name.startswith("test_"))
            file_test_classes = sum(1 for name, _ in mod.classes if name.startswith("Test"))
            total_test_functions += file_test_count

        if test_files:
            diagnostics.append(
                StaticDiagnostic(
                    category=DiagnosticCategory.TEST,
                    severity=DiagnosticSeverity.INFO,
                    code="TEST_DISCOVERED",
                    message=(
                        f"Discovered {len(test_files)} test file(s) containing "
                        f"{total_test_functions} test function(s)."
                    ),
                    source="test_discovery",
                    metadata={
                        "test_files": test_files,
                        "test_function_count": total_test_functions,
                    },
                )
            )
        else:
            diagnostics.append(
                StaticDiagnostic(
                    category=DiagnosticCategory.TEST,
                    severity=DiagnosticSeverity.WARNING,
                    code="TEST_NO_TESTS",
                    message="No automated test files (test_*.py or *_test.py) discovered in project.",
                    source="test_discovery",
                )
            )

        return test_files, total_test_functions, diagnostics
