"""Deterministic Relevant Source Selection & Evidence Bounding for Failure Analysis."""

import re
from typing import Sequence
from app.agents.code_generation.contracts import GeneratedFile
from app.agents.failure_analysis.contracts import RelevantSourceFile
from app.sandbox.contracts import ExecutionResult
from app.sandbox.static_analysis.contracts import (
    DiagnosticSeverity,
    StaticAnalysisResult,
    StaticDiagnostic,
)

MAX_FILES = 10
MAX_TOTAL_BYTES = 50 * 1024  # 50 KB
MAX_INDIVIDUAL_FILE_BYTES = 20 * 1024  # 20 KB
MAX_EXECUTION_OUTPUT_BYTES = 20 * 1024  # 20 KB
MAX_DIAGNOSTICS = 50


class SourceSelector:
    """Selects and bounds relevant project source code and diagnostics deterministically."""

    @staticmethod
    def extract_traceback_files(text: str, project_paths: set[str]) -> list[str]:
        """Extract project relative file paths referenced in python tracebacks."""
        found: list[str] = []
        # Pattern 1: File "app/main.py", line 12
        matches = re.findall(r'File\s+["\']([^"\']+)["\']', text)
        # Pattern 2: app/main.py:12:
        matches += re.findall(r'([\w/\.-]+\.py):\d+', text)

        for match in matches:
            clean = match.replace("\\", "/")
            # Match directly or by ending relative path
            matched_path = next(
                (p for p in project_paths if p == clean or clean.endswith(p) or p.endswith(clean)),
                None,
            )
            if matched_path and matched_path not in found:
                found.append(matched_path)
        return found

    @staticmethod
    def filter_and_bound_diagnostics(
        static_analysis: StaticAnalysisResult | None,
    ) -> list[StaticDiagnostic]:
        """Filter and cap diagnostics to priority errors and warnings."""
        if not static_analysis or not static_analysis.diagnostics:
            return []

        # Sort priority: CRITICAL > ERROR > WARNING > INFO
        severity_order = {
            DiagnosticSeverity.CRITICAL: 0,
            DiagnosticSeverity.ERROR: 1,
            DiagnosticSeverity.WARNING: 2,
            DiagnosticSeverity.INFO: 3,
        }

        sorted_diags = sorted(
            static_analysis.diagnostics,
            key=lambda d: severity_order.get(d.severity, 4),
        )
        return sorted_diags[:MAX_DIAGNOSTICS]

    @staticmethod
    def bound_execution_output(text: str) -> str:
        """Bound stdout or stderr text to configured size limit."""
        if not text:
            return ""
        if len(text.encode("utf-8")) <= MAX_EXECUTION_OUTPUT_BYTES:
            return text
        # Truncate and mark
        truncated = text[:MAX_EXECUTION_OUTPUT_BYTES]
        return f"{truncated}\n... [OUTPUT TRUNCATED TO 20KB LIMIT]"

    @classmethod
    def select_relevant_source(
        cls,
        files: Sequence[GeneratedFile],
        static_analysis: StaticAnalysisResult | None = None,
        execution_result: ExecutionResult | None = None,
        ai_test_execution_result: Any | None = None,
        ai_test_suite: Any | None = None,
    ) -> list[RelevantSourceFile]:
        """Select, prioritize, and format source code files under strict size bounds."""
        file_map = {f.path: f for f in files}
        project_paths = set(file_map.keys())

        # Collect priority targets
        priority_files: list[tuple[str, str]] = []

        # 1. Target application files of failing AI tests
        if ai_test_execution_result:
            failing_names = {
                tr.name
                for tr in getattr(ai_test_execution_result, "test_results", [])
                if getattr(tr, "status", "") in ("FAILED", "ERROR")
            }
            # Fallback if pytest failed but test_results was empty
            tests_failed = getattr(ai_test_execution_result, "tests_failed", 0)

            if ai_test_suite and hasattr(ai_test_suite, "tests"):
                for t in ai_test_suite.tests:
                    is_failed = t.name in failing_names or t.test_id in failing_names or (len(failing_names) == 0 and tests_failed > 0)
                    if is_failed:
                        tgt = getattr(t, "target_file", None)
                        if tgt and tgt in file_map:
                            reason = f"Target application file for failing AI test '{t.name}' ({t.test_id})"
                            if not any(p == tgt for p, _ in priority_files):
                                priority_files.append((tgt, reason))

            # Traceback files from AI test execution output and failure summaries
            combined_ai = f"{getattr(ai_test_execution_result, 'stdout', '')}\n{getattr(ai_test_execution_result, 'stderr', '')}"
            for summary in getattr(ai_test_execution_result, "failure_summaries", []):
                combined_ai += f"\n{summary}"
            ai_tb_files = cls.extract_traceback_files(combined_ai, project_paths)
            for path in ai_tb_files:
                reason = "Referenced in AI test traceback"
                if not any(p == path for p, _ in priority_files):
                    priority_files.append((path, reason))

        # 2. Directly referenced by failing static diagnostics
        if static_analysis:
            for diag in static_analysis.diagnostics:
                if diag.file_path and diag.file_path in file_map:
                    reason = f"Referenced by static diagnostic {diag.code} ({diag.severity.value})"
                    if (diag.file_path, reason) not in priority_files:
                        priority_files.append((diag.file_path, reason))

        # 3. Referenced in execution stdout/stderr tracebacks
        if execution_result:
            combined_out = f"{execution_result.stdout}\n{execution_result.stderr}"
            tb_files = cls.extract_traceback_files(combined_out, project_paths)
            for path in tb_files:
                reason = "Referenced in runtime traceback / test failure output"
                if not any(p == path for p, _ in priority_files):
                    priority_files.append((path, reason))

        # 4. Failing test files
        if (execution_result and execution_result.tests_failed > 0) or (ai_test_execution_result and getattr(ai_test_execution_result, "tests_failed", 0) > 0):
            for path in project_paths:
                if (path.startswith("tests/") or "test" in path) and not any(p == path for p, _ in priority_files):
                    priority_files.append((path, "Test suite file in failing test execution"))

        # 5. Fill remaining files up to limit if space permits
        for path in sorted(project_paths):
            if not any(p == path for p, _ in priority_files):
                priority_files.append((path, "Project source context"))

        # Format and bound
        selected: list[RelevantSourceFile] = []
        total_bytes = 0

        for path, reason in priority_files:
            if len(selected) >= MAX_FILES:
                break

            gen_file = file_map.get(path)
            if not gen_file:
                continue

            content = gen_file.content
            # Truncate individual file if necessary
            encoded = content.encode("utf-8")
            if len(encoded) > MAX_INDIVIDUAL_FILE_BYTES:
                content = content[:MAX_INDIVIDUAL_FILE_BYTES] + "\n... [TRUNCATED FILE CONTENT]"
                encoded = content.encode("utf-8")

            if total_bytes + len(encoded) > MAX_TOTAL_BYTES:
                # Can't fit this file
                continue

            total_bytes += len(encoded)

            # Format with line numbers: "1 | content"
            lines = content.splitlines()
            annotated_lines = [f"{i + 1:3d} | {line}" for i, line in enumerate(lines)]
            annotated_content = "\n".join(annotated_lines)

            selected.append(
                RelevantSourceFile(
                    path=path,
                    content=annotated_content,
                    line_start=1,
                    line_end=len(lines),
                    selection_reason=reason,
                )
            )

        return selected
