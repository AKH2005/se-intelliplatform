"""Deterministic Validation, Path Safety, and Secret Scanning for Code Generation."""

import ast
import json
import logging
import os
import posixpath
import re
from typing import Any

from app.agents.code_generation.contracts import (
    MAX_FILES,
    MAX_FILE_SIZE_BYTES,
    MAX_PATH_LENGTH,
    MAX_TOTAL_SIZE_BYTES,
    SUPPORTED_DATABASES,
    SUPPORTED_FRAMEWORKS,
    SUPPORTED_LANGUAGES,
    SUPPORTED_PACKAGE_MANAGERS,
    CodeGenerationOutput,
    CodeGenerationPlan,
    FileType,
    is_fullstack_project,
)
from app.agents.contracts import ValidationResult
from app.schemas.context import ProjectContextResponse

logger = logging.getLogger(__name__)


# ==============================================================================
# 1. Path Safety & Limits
# ==============================================================================

def validate_path_safety(path: str) -> None:
    """Deterministically enforce path safety invariants.

    Rejects:
    - Null bytes
    - Windows backslashes
    - Absolute or drive-letter paths (e.g. C:, /etc/passwd)
    - Path traversal segments (.. or .)
    - Paths exceeding MAX_PATH_LENGTH
    """
    if not path or not isinstance(path, str):
        raise ValueError("File path must be a non-empty string.")

    if "\0" in path:
        raise ValueError(f"Null byte detected in path '{path}'.")

    if "\\" in path:
        raise ValueError(f"Backslash path separator forbidden in path '{path}'. Use '/' instead.")

    if path.startswith("/"):
        raise ValueError(f"Absolute path forbidden: '{path}'. Paths must be relative to project root.")

    if re.match(r"^[a-zA-Z]:", path):
        raise ValueError(f"Drive letter detected in path '{path}'. Absolute paths forbidden.")

    if path.startswith("//") or path.startswith("\\\\"):
        raise ValueError(f"UNC network path forbidden: '{path}'.")

    if len(path) > MAX_PATH_LENGTH:
        raise ValueError(
            f"Path '{path}' exceeds maximum allowed length ({len(path)} > {MAX_PATH_LENGTH})."
        )

    # Clean normalization check
    normalized = posixpath.normpath(path)
    if normalized.startswith("..") or "/../" in f"/{normalized}/" or normalized == "..":
        raise ValueError(f"Path traversal ('..') detected in path '{path}'.")

    parts = path.strip("/").split("/")
    for part in parts:
        if part in ("..", "."):
            raise ValueError(f"Path component '{part}' forbidden in path '{path}'.")
        if not part:
            raise ValueError(f"Empty directory segment forbidden in path '{path}'.")


# ==============================================================================
# 2. Secret Scanning
# ==============================================================================

SECRET_PATTERNS = [
    # Private / SSH keys
    (re.compile(r"-----BEGIN (?:[A-Z0-9_-]+ )?PRIVATE KEY-----"), "Private key header"),
    (re.compile(r"-----BEGIN OPENSSH PRIVATE KEY-----"), "OpenSSH private key"),
    (re.compile(r"-----BEGIN PGP PRIVATE KEY BLOCK-----"), "PGP private key block"),
    # Well-known API key patterns
    (re.compile(r"sk-[a-zA-Z0-9]{20,}"), "OpenAI API key pattern"),
    (re.compile(r"gsk_[a-zA-Z0-9]{20,}"), "Groq API key pattern"),
    (re.compile(r"AIzaSy[a-zA-Z0-9_-]{33}"), "Google API key pattern"),
    (re.compile(r"AKIA[0-9A-Z]{16}"), "AWS Access Key ID pattern"),
    # Generic hardcoded credentials in assignments (excluding empty or obvious placeholders)
    (
        re.compile(
            r"""(?:api_key|secret_key|private_key|auth_token|jwt_secret)\s*=\s*['"]([A-Za-z0-9_\-\.]{12,})['"]""",
            re.IGNORECASE,
        ),
        "Hardcoded API/Secret key assignment",
    ),
    # Database URIs with embedded passwords
    (
        re.compile(
            r"""(?:postgresql|postgres|mysql|mongodb|redis):\/\/[a-zA-Z0-9_\.\-]+:[^@\s'"]+@[a-zA-Z0-9_\.\-]+""",
            re.IGNORECASE,
        ),
        "Database URI with embedded password",
    ),
]


def scan_for_secrets(content: str, path: str) -> list[str]:
    """Scan file content for embedded credentials, API keys, and private keys."""
    findings: list[str] = []
    for pattern, description in SECRET_PATTERNS:
        match = pattern.search(content)
        if match:
            # Filter out harmless mock/test placeholders
            matched_text = match.group(0).lower()
            if any(p in matched_text for p in ["placeholder", "dummy", "test_secret", "your_api_key", "change_me", "user:pass", "localhost"]):
                continue
            findings.append(f"Secret detected in '{path}': {description}")
    return findings


# ==============================================================================
# 3. Plan Validation
# ==============================================================================

def validate_code_generation_plan(
    plan: CodeGenerationPlan,
    context: ProjectContextResponse,
    architecture_recommendation: Any | None = None,
) -> ValidationResult:
    """Deterministically validate a CodeGenerationPlan."""
    errors: list[str] = []

    # 1. Supported Stack Verification
    if plan.language.lower() not in SUPPORTED_LANGUAGES:
        errors.append(
            f"Unsupported language '{plan.language}'. Supported: {sorted(SUPPORTED_LANGUAGES)}"
        )
    if plan.framework.lower() not in SUPPORTED_FRAMEWORKS:
        errors.append(
            f"Unsupported framework '{plan.framework}'. Supported: {sorted(SUPPORTED_FRAMEWORKS)}"
        )
    if plan.database.lower() not in SUPPORTED_DATABASES:
        errors.append(
            f"Unsupported database '{plan.database}'. Supported: {sorted(SUPPORTED_DATABASES)}"
        )
    if plan.package_manager.lower() not in SUPPORTED_PACKAGE_MANAGERS:
        errors.append(
            f"Unsupported package manager '{plan.package_manager}'. Supported: {sorted(SUPPORTED_PACKAGE_MANAGERS)}"
        )

    # 2. File Count Limits
    if not plan.files:
        errors.append("CodeGenerationPlan must contain at least one planned file.")
    elif len(plan.files) > MAX_FILES:
        errors.append(
            f"CodeGenerationPlan contains {len(plan.files)} files, exceeding limit of {MAX_FILES}."
        )

    # 3. Path Safety & Duplicate Verification
    seen_paths: set[str] = set()
    for idx, f in enumerate(plan.files):
        try:
            validate_path_safety(f.path)
        except ValueError as exc:
            errors.append(f"File [{idx}] '{f.path}' violates path safety: {exc}")

        norm_path = f.path.lower()
        if norm_path in seen_paths:
            errors.append(f"Duplicate path in generation plan: '{f.path}'.")
        seen_paths.add(norm_path)

        if not f.purpose or len(f.purpose.strip()) < 5:
            errors.append(f"File '{f.path}' has insufficient purpose description.")

    # 4. Canonical Requirement Traceability
    canonical_req_ids = {str(r.id) for r in context.requirements}
    for f in plan.files:
        for req_id in f.requirement_ids:
            if req_id not in canonical_req_ids:
                errors.append(
                    f"File '{f.path}' references unknown requirement ID '{req_id}'."
                )

    # 5. Architecture Component Traceability
    if architecture_recommendation is not None:
        if isinstance(architecture_recommendation, dict):
            components_list = architecture_recommendation.get("components", [])
            declared_components = {
                c.get("name") if isinstance(c, dict) else getattr(c, "name", "")
                for c in components_list
            }
        elif hasattr(architecture_recommendation, "components") and architecture_recommendation.components:
            declared_components = {c.name for c in architecture_recommendation.components}
        else:
            declared_components = set()

        if declared_components:
            declared_lower = {c.lower(): c for c in declared_components if c}
            doc_aliases = {
                "documentation", "docs", "doc", "root", "project", "system",
                "general", "readme", "config", "build", "dependencies", "dependency"
            }

            for f in plan.files:
                if not f.architecture_component:
                    continue
                comp = f.architecture_component.strip()
                comp_lower = comp.lower()

                # Allow documentation and infrastructure aliases for README, dependency manifests, or config files
                is_manifest_or_doc = (
                    getattr(f, "file_type", None) in (FileType.DOCUMENTATION, FileType.DEPENDENCY, FileType.CONFIG)
                    or f.path.lower().startswith("readme")
                    or any(f.path.lower().endswith(x) for x in [
                        "requirements.txt", "package.json", ".gitignore", "dockerfile",
                        "tsconfig.json", "vite.config.ts", "readme.md"
                    ])
                )
                if is_manifest_or_doc and (comp_lower in doc_aliases or "doc" in comp_lower or "root" in comp_lower or "depend" in comp_lower):
                    continue

                if comp in declared_components or comp_lower in declared_lower:
                    continue
                # If substring match
                if any(comp_lower in d or d in comp_lower for d in declared_lower):
                    continue
                errors.append(
                    f"File '{f.path}' references undeclared architecture component '{f.architecture_component}'. "
                    f"Declared: {sorted(declared_components)}"
                )

    # 6. Full-Stack Invariant Verification
    if is_fullstack_project(context, architecture_recommendation):
        has_frontend_pkg = any("package.json" in f.path.lower() for f in plan.files)
        has_frontend_entry = any(
            any(f.path.lower().endswith(ext) for ext in ["main.tsx", "main.jsx", "index.html", "app.tsx", "app.jsx"])
            for f in plan.files
        )
        has_backend_entry = any(
            any(f.path.lower().endswith(ext) for ext in ["main.py", "requirements.txt", "api.py"])
            for f in plan.files
        )
        if not (has_frontend_pkg and has_frontend_entry):
            errors.append(
                "Project requires a full-stack application (React + FastAPI), "
                "but planned files lack required frontend components (e.g. package.json, App.tsx, index.html). "
                "Incomplete generation plan rejected."
            )
        if not has_backend_entry:
            errors.append(
                "Project requires a full-stack application (React + FastAPI), "
                "but planned files lack required backend services (main.py, requirements.txt). "
                "Incomplete generation plan rejected."
            )

    return ValidationResult(
        is_valid=len(errors) == 0,
        errors=errors,
        metadata={"total_planned_files": len(plan.files)},
    )


# ==============================================================================
# 4. Code Generation Output Validation
# ==============================================================================

def validate_code_generation_output(
    output: CodeGenerationOutput,
    plan: CodeGenerationPlan,
    context: ProjectContextResponse,
) -> ValidationResult:
    """Deterministically validate generated code files against the plan and safety rules."""
    errors: list[str] = []

    # 1. Manifest Consistency Verification
    planned_paths = {f.path for f in plan.files}
    generated_paths = {f.path for f in output.generated_files}

    unplanned_files = generated_paths - planned_paths
    if unplanned_files:
        errors.append(
            f"Generated output contains unplanned files: {sorted(unplanned_files)}. "
            f"Only files declared in the manifest are permitted."
        )

    missing_files = planned_paths - generated_paths
    if missing_files:
        errors.append(
            f"Generated output is missing required planned files: {sorted(missing_files)}."
        )

    # Full-Stack Completeness Verification
    if is_fullstack_project(context):
        has_frontend_pkg = any("package.json" in f.path.lower() for f in output.generated_files)
        has_frontend_entry = any(
            any(f.path.lower().endswith(ext) for ext in ["main.tsx", "main.jsx", "index.html", "app.tsx", "app.jsx"])
            for f in output.generated_files
        )
        has_backend_entry = any(
            any(f.path.lower().endswith(ext) for ext in ["main.py", "requirements.txt", "api.py"])
            for f in output.generated_files
        )
        if not (has_frontend_pkg and has_frontend_entry and has_backend_entry):
            errors.append(
                "Project requires a full-stack application (React + FastAPI), but generated files lack "
                "essential frontend components or backend services. Incomplete generation rejected."
            )

    # Check duplicates in output
    seen_paths: set[str] = set()
    for f in output.generated_files:
        if f.path in seen_paths:
            errors.append(f"Duplicate file in generated output: '{f.path}'.")
        seen_paths.add(f.path)

    # 2. File Size & Content Checks
    total_calculated_size = 0
    for f in output.generated_files:
        # Path safety check
        try:
            validate_path_safety(f.path)
        except ValueError as exc:
            errors.append(f"Generated file '{f.path}' violates path safety: {exc}")

        # Content must be text (no null bytes)
        if "\0" in f.content:
            errors.append(f"Null byte detected in content of '{f.path}'.")

        # Size consistency check
        utf8_bytes = f.content.encode("utf-8")
        actual_size = len(utf8_bytes)
        if actual_size > MAX_FILE_SIZE_BYTES:
            errors.append(
                f"File '{f.path}' size ({actual_size} bytes) exceeds limit of {MAX_FILE_SIZE_BYTES} bytes."
            )
        if f.size_bytes != actual_size:
            errors.append(
                f"File '{f.path}' declared size ({f.size_bytes}) does not match actual size ({actual_size})."
            )
        total_calculated_size += actual_size

        # 3. Secret Scanning Check
        secret_findings = scan_for_secrets(f.content, f.path)
        for s in secret_findings:
            errors.append(f"Secret detected in '{f.path}': {s}")

        # 4. JSON Validation Check
        if f.path.endswith(".json"):
            try:
                json.loads(f.content)
            except Exception as j_err:
                errors.append(f"Invalid JSON syntax in '{f.path}': {j_err}")

        # 5. HTML Validation Check
        if f.path.endswith(".html"):
            if "<" not in f.content or ">" not in f.content:
                errors.append(f"Malformed HTML structure in '{f.path}'.")

        # 6. Structural Python Syntax Check (No execution, static AST check only)
        if f.path.endswith(".py"):
            try:
                ast.parse(f.content, filename=f.path)
            except SyntaxError as syn_err:
                errors.append(
                    f"Syntax error in generated Python file '{f.path}': line {syn_err.lineno}: {syn_err.msg}"
                )

        # 7. Dangerous execution/eval scan
        if f.path.endswith(".py"):
            try:
                tree = ast.parse(f.content, filename=f.path)
                for node in ast.walk(tree):
                    if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
                        if node.func.id in ("eval", "exec"):
                            errors.append(
                                f"Forbidden dynamic execution call '{node.func.id}()' in '{f.path}'."
                            )
            except Exception:
                pass  # Syntax errors already handled above

    # 5. Total Project Size Check
    if total_calculated_size > MAX_TOTAL_SIZE_BYTES:
        errors.append(
            f"Total generated project size ({total_calculated_size} bytes) exceeds limit of {MAX_TOTAL_SIZE_BYTES} bytes."
        )

    if output.total_size_bytes != total_calculated_size:
        errors.append(
            f"Output total_size_bytes ({output.total_size_bytes}) does not match calculated total ({total_calculated_size})."
        )

    if output.total_files != len(output.generated_files):
        errors.append(
            f"Output total_files ({output.total_files}) does not match generated_files count ({len(output.generated_files)})."
        )

    return ValidationResult(
        is_valid=len(errors) == 0,
        errors=errors,
        metadata={
            "total_files": len(output.generated_files),
            "total_size_bytes": total_calculated_size,
        },
    )
