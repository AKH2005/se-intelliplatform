"""Deterministic Ruff Linting Integration via the Isolated Sandbox Runtime."""

import json
import logging
from typing import Any

from app.agents.code_generation.contracts import CodeGenerationOutput
from app.sandbox.base import AbstractSandboxExecutor
from app.sandbox.contracts import (
    ExecutionRequest,
    ExecutionStatus,
    ExecutionType,
    ResourceLimits,
)
from app.sandbox.static_analysis.contracts import (
    DiagnosticCategory,
    DiagnosticSeverity,
    StaticDiagnostic,
)

logger = logging.getLogger(__name__)


class RuffAnalyzer:
    """Invokes Ruff within the existing Docker sandbox boundary and normalizes output."""

    def __init__(self, executor: AbstractSandboxExecutor) -> None:
        self.executor = executor

    def _map_rule_severity(self, code: str) -> tuple[DiagnosticCategory, DiagnosticSeverity]:
        """Deterministically map Ruff rule codes to category and severity."""
        code_upper = code.upper()

        # Syntax / Parse errors from Ruff
        if code_upper.startswith("E9") or code_upper == "SYNTAX":
            return DiagnosticCategory.SYNTAX, DiagnosticSeverity.ERROR

        # Undefined names / references (definite runtime errors)
        if code_upper in ("F821", "F822", "F823"):
            return DiagnosticCategory.LINT, DiagnosticSeverity.ERROR

        # Unused imports / variables (warnings)
        if code_upper in ("F401", "F841"):
            return DiagnosticCategory.LINT, DiagnosticSeverity.WARNING

        # Security-related rules (flake8-bandit 'S' codes if enabled)
        if code_upper.startswith("S"):
            return DiagnosticCategory.SECURITY, DiagnosticSeverity.WARNING

        # Standard lint warnings (E and W rules)
        if code_upper.startswith(("E", "F", "W")):
            return DiagnosticCategory.LINT, DiagnosticSeverity.WARNING

        return DiagnosticCategory.LINT, DiagnosticSeverity.INFO

    async def analyze(
        self,
        request: ExecutionRequest,
        code_output: CodeGenerationOutput,
    ) -> list[StaticDiagnostic]:
        """Execute containerized Ruff analysis and parse machine-readable JSON findings."""
        lint_req = request.model_copy(
            update={
                "execution_type": ExecutionType.LINT,
                "limits": ResourceLimits(timeout_seconds=20),
            }
        )

        exec_result = await self.executor.execute(lint_req, code_output)
        diagnostics: list[StaticDiagnostic] = []

        if exec_result.status == ExecutionStatus.SANDBOX_UNAVAILABLE:
            diagnostics.append(
                StaticDiagnostic(
                    category=DiagnosticCategory.STRUCTURE,
                    severity=DiagnosticSeverity.INFO,
                    code="LINT_SANDBOX_UNAVAILABLE",
                    message="Docker runtime unavailable. Containerized Ruff analysis was skipped.",
                    source="ruff",
                )
            )
            return diagnostics

        if not exec_result.stdout:
            return diagnostics

        try:
            findings_data = json.loads(exec_result.stdout)
            if not isinstance(findings_data, list):
                return diagnostics
        except Exception as json_err:
            logger.warning(f"Failed to parse Ruff JSON output: {json_err}. Raw stdout: {exec_result.stdout[:200]}")
            return diagnostics

        for item in findings_data:
            if not isinstance(item, dict):
                continue

            raw_file = item.get("filename", "")
            # Normalize path: strip /workspace/ prefix and leading slashes
            clean_path = raw_file.replace("/workspace/", "").strip("/")

            rule_code = item.get("code", "RUFF")
            message = item.get("message", "Lint finding")
            location = item.get("location", {})
            row = location.get("row") if isinstance(location, dict) else None
            col = location.get("column") if isinstance(location, dict) else None

            category, severity = self._map_rule_severity(rule_code)

            diagnostics.append(
                StaticDiagnostic(
                    category=category,
                    severity=severity,
                    code=rule_code,
                    message=message,
                    file_path=clean_path if clean_path else None,
                    line=row,
                    column=col,
                    source="ruff",
                    evidence=item.get("fix", {}).get("message") if isinstance(item.get("fix"), dict) else None,
                    metadata={"url": item.get("url")},
                )
            )

        return diagnostics
