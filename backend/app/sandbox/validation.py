"""Deterministic Pre-Execution Validation for the Sandbox."""

import ast
import logging
from typing import Any

from app.agents.code_generation.contracts import (
    MAX_FILES,
    MAX_FILE_SIZE_BYTES,
    MAX_TOTAL_SIZE_BYTES,
    CodeGenerationOutput,
)
from app.agents.code_generation.validation import scan_for_secrets, validate_path_safety

logger = logging.getLogger(__name__)


def validate_artifact_for_execution(
    artifact: CodeGenerationOutput | dict[str, Any],
    test_target: str | None = None,
) -> list[str]:
    """Deterministically re-validate generated code before entering the sandbox.

    Guarantees:
    - Never assumes upstream validation is permanently trusted.
    - Re-checks path safety for all files.
    - Re-checks size limits and null bytes.
    - Re-scans for hardcoded credentials or API keys.
    - Re-checks Python AST syntax without execution.
    - Validates test_target path safety if specified.
    """
    errors: list[str] = []

    # 1. Parse into CodeGenerationOutput model if dict
    if isinstance(artifact, dict):
        try:
            output_obj = CodeGenerationOutput.model_validate(artifact)
        except Exception as exc:
            return [f"Malformed CodeGenerationOutput structure: {exc}"]
    elif isinstance(artifact, CodeGenerationOutput):
        output_obj = artifact
    else:
        return [f"Invalid artifact type: {type(artifact).__name__}. Expected CodeGenerationOutput."]

    # 2. File count check
    if not output_obj.generated_files:
        errors.append("Artifact contains no generated files.")
    elif len(output_obj.generated_files) > MAX_FILES:
        errors.append(
            f"Artifact contains {len(output_obj.generated_files)} files, exceeding limit of {MAX_FILES}."
        )

    # 3. Path safety, secrets, size, and syntax
    total_size = 0
    for f in output_obj.generated_files:
        try:
            validate_path_safety(f.path)
        except ValueError as exc:
            errors.append(f"File '{f.path}' violates path safety: {exc}")

        if "\0" in f.content:
            errors.append(f"Null byte detected in '{f.path}'.")

        utf8_bytes = f.content.encode("utf-8")
        actual_size = len(utf8_bytes)
        if actual_size > MAX_FILE_SIZE_BYTES:
            errors.append(
                f"File '{f.path}' size ({actual_size} bytes) exceeds limit of {MAX_FILE_SIZE_BYTES} bytes."
            )
        total_size += actual_size

        # Secret scanning
        secrets = scan_for_secrets(f.content, f.path)
        for s in secrets:
            errors.append(f"Secret detected in '{f.path}': {s}")

        # Python syntax validation (Static AST parse - NEVER exec)
        if f.path.endswith(".py"):
            try:
                tree = ast.parse(f.content, filename=f.path)
                for node in ast.walk(tree):
                    if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
                        if node.func.id in ("eval", "exec"):
                            errors.append(
                                f"Forbidden dynamic execution call '{node.func.id}()' in '{f.path}'."
                            )
            except SyntaxError as syn_err:
                errors.append(
                    f"Syntax error in '{f.path}': line {syn_err.lineno}: {syn_err.msg}"
                )

    if total_size > MAX_TOTAL_SIZE_BYTES:
        errors.append(
            f"Total project size ({total_size} bytes) exceeds limit of {MAX_TOTAL_SIZE_BYTES} bytes."
        )

    # 4. Validate test_target if requested
    if test_target:
        try:
            validate_path_safety(test_target)
            if not test_target.endswith(".py") and not test_target.endswith("/"):
                errors.append(
                    f"Test target '{test_target}' must be a python test file (.py) or directory."
                )
        except ValueError as exc:
            errors.append(f"Invalid test target path '{test_target}': {exc}")

    return errors
