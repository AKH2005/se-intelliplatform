"""Deterministic Validation for AI Code Review Agent."""

import os
from typing import Any
from app.agents.code_review.contracts import (
    MAX_FILES,
    MAX_LINES_PER_FILE,
    MAX_TOTAL_SIZE_BYTES,
    SUPPORTED_LANGUAGES,
    CodeFile,
    CodeReviewFinding,
    CodeReviewInput,
    CodeReviewOutput,
    FindingCategory,
    FindingSeverity,
    FindingSource,
)
from app.agents.contracts import ValidationResult
from app.agents.exceptions import AgentValidationError
from app.schemas.context import ProjectContextResponse


def validate_code_review_input(code_input: CodeReviewInput) -> None:
    """Enforce strict deterministic input bounds and security constraints on CodeReviewInput.

    Raises AgentValidationError if constraints are violated.
    """
    errors: list[str] = []

    # 1. Bounded file count
    if not code_input.files:
        errors.append("CodeReviewInput must contain at least one file to review.")
    elif len(code_input.files) > MAX_FILES:
        errors.append(
            f"Number of files ({len(code_input.files)}) exceeds maximum allowed ({MAX_FILES})."
        )

    # 2. Cumulative size check
    total_size = sum(len(f.content.encode("utf-8")) for f in code_input.files)
    if total_size > MAX_TOTAL_SIZE_BYTES:
        errors.append(
            f"Cumulative source code size ({total_size} bytes) exceeds maximum limit "
            f"of {MAX_TOTAL_SIZE_BYTES} bytes (100 KB)."
        )

    seen_paths: set[str] = set()

    for idx, f in enumerate(code_input.files):
        prefix = f"File {idx + 1} ('{f.file_path}')"

        # Unique paths
        normalized_path = f.file_path.strip().replace("\\", "/")
        if normalized_path in seen_paths:
            errors.append(f"{prefix}: Duplicate file path '{f.file_path}' in input.")
        seen_paths.add(normalized_path)

        # Path traversal and security checks
        if not f.file_path.strip():
            errors.append(f"File {idx + 1}: file_path cannot be blank.")
        else:
            if ".." in f.file_path or f.file_path.startswith("/") or f.file_path.startswith("\\"):
                errors.append(
                    f"{prefix}: Absolute paths and path traversal ('..') are strictly forbidden."
                )
            if ":" in f.file_path:  # Windows drive letters (C:) or stream syntax
                errors.append(f"{prefix}: Drive letters or colons are forbidden in file_path.")

        # Supported language check
        lang_clean = f.language.strip().lower()
        if lang_clean not in SUPPORTED_LANGUAGES:
            errors.append(
                f"{prefix}: Unsupported language '{f.language}'. "
                f"Supported languages in Phase 8.1 are: {sorted(list(SUPPORTED_LANGUAGES))}."
            )

        # Non-empty content
        if not f.content.strip():
            errors.append(f"{prefix}: Content cannot be empty or whitespace only.")

        # Line count limit
        lines = f.content.splitlines()
        if len(lines) > MAX_LINES_PER_FILE:
            errors.append(
                f"{prefix}: Line count ({len(lines)}) exceeds maximum limit of "
                f"{MAX_LINES_PER_FILE} lines per file."
            )

    if errors:
        raise AgentValidationError(
            message="Input validation failed for CodeReviewInput.",
            validation_errors=errors,
        )


def validate_code_review_output(
    output: CodeReviewOutput,
    context: ProjectContextResponse,
    file_contents_map: dict[str, str] | None = None,
) -> ValidationResult:
    """Perform rigorous deterministic validation on CodeReviewOutput.

    Enforces:
      1. Structural consistency: files_analyzed_count and total_findings match actual lists.
      2. Unique finding IDs: No duplicate finding_id in the review.
      3. Field completeness: Titles, descriptions, evidence, and recommendations non-empty.
      4. Line bounds and evidence verification against actual file contents:
         - 1 <= line_start <= line_end <= total_file_lines
         - Evidence string must actually appear in the designated lines.
      5. File authority: Every finding must reference a file in files_reviewed.
      6. Duplicate prevention: No duplicate findings with identical file, line range, and title/rule.
      7. Summary metrics mathematical invariants:
         - static_findings_count == sum(source == STATIC_ANALYSIS)
         - ai_findings_count == sum(source == AI_REVIEW)
         - findings_by_severity and findings_by_category sum correctly.
      8. Limitations: Non-empty list documenting review bounds (>= 3 items).
    """
    errors: list[str] = []

    # 1. Summary check
    if not output.summary.strip():
        errors.append("summary cannot be empty or whitespace only.")

    # 2. Files reviewed check
    if not output.files_reviewed:
        errors.append("files_reviewed list cannot be empty.")

    valid_files_set = set(output.files_reviewed)

    # 3. Structural metrics consistency
    metrics = output.metrics
    if metrics.files_analyzed_count != len(output.files_reviewed):
        errors.append(
            f"metrics.files_analyzed_count ({metrics.files_analyzed_count}) mismatch with "
            f"files_reviewed count ({len(output.files_reviewed)})."
        )

    if metrics.total_findings != len(output.findings):
        errors.append(
            f"metrics.total_findings ({metrics.total_findings}) mismatch with "
            f"actual findings count ({len(output.findings)})."
        )

    # 4. Tracking for uniqueness, duplication, and metric sums
    seen_finding_ids: set[str] = set()
    seen_fingerprints: set[tuple[str, int, int, str]] = set()

    computed_by_severity: dict[str, int] = {s.value: 0 for s in FindingSeverity}
    computed_by_category: dict[str, int] = {c.value: 0 for c in FindingCategory}
    computed_static = 0
    computed_ai = 0

    for idx, finding in enumerate(output.findings):
        finding_prefix = f"Finding [{finding.finding_id or f'index {idx}'}]"

        # Unique finding ID
        raw_id = finding.finding_id.strip()
        if not raw_id:
            errors.append(f"{finding_prefix}: finding_id cannot be blank.")
        elif raw_id in seen_finding_ids:
            errors.append(f"Duplicate finding_id '{raw_id}' detected in review output.")
        else:
            seen_finding_ids.add(raw_id)

        # File path authority
        if finding.file_path not in valid_files_set:
            errors.append(
                f"{finding_prefix}: references file '{finding.file_path}' which is not in files_reviewed."
            )

        # Field completeness
        if not finding.title.strip():
            errors.append(f"{finding_prefix}: title cannot be empty.")
        if not finding.description.strip():
            errors.append(f"{finding_prefix}: description cannot be empty.")
        if not finding.evidence.strip():
            errors.append(f"{finding_prefix}: evidence cannot be empty.")
        if not finding.recommendation.strip():
            errors.append(f"{finding_prefix}: recommendation cannot be empty.")

        # Line bounds check
        if finding.line_start < 1:
            errors.append(f"{finding_prefix}: line_start must be >= 1.")
        if finding.line_end < finding.line_start:
            errors.append(
                f"{finding_prefix}: line_end ({finding.line_end}) cannot be less than "
                f"line_start ({finding.line_start})."
            )

        # File content & evidence verification
        if file_contents_map and finding.file_path in file_contents_map:
            file_text = file_contents_map[finding.file_path]
            file_lines = file_text.splitlines()
            total_lines = len(file_lines) if file_lines else 1

            if finding.line_end > total_lines:
                errors.append(
                    f"{finding_prefix}: line_end ({finding.line_end}) exceeds total file lines "
                    f"({total_lines}) in '{finding.file_path}'."
                )
            else:
                # Evidence check: verify evidence snippet exists in lines[line_start-1:line_end]
                target_slice = "\n".join(file_lines[finding.line_start - 1 : finding.line_end])
                normalized_slice = "".join(target_slice.split())
                normalized_evidence = "".join(finding.evidence.split())

                # Allow evidence match against target slice or single-word token match
                if normalized_evidence and normalized_evidence not in normalized_slice:
                    errors.append(
                        f"{finding_prefix}: evidence text does not match actual source lines "
                        f"{finding.line_start}-{finding.line_end} in '{finding.file_path}'."
                    )

        # Duplicate finding check
        fingerprint = (
            finding.file_path,
            finding.line_start,
            finding.line_end,
            (finding.rule_id or finding.title).strip().lower(),
        )
        if fingerprint in seen_fingerprints:
            errors.append(
                f"{finding_prefix}: duplicate finding detected for '{finding.file_path}' "
                f"lines {finding.line_start}-{finding.line_end}."
            )
        else:
            seen_fingerprints.add(fingerprint)

        # Tally metrics
        computed_by_severity[finding.severity.value] = (
            computed_by_severity.get(finding.severity.value, 0) + 1
        )
        computed_by_category[finding.category.value] = (
            computed_by_category.get(finding.category.value, 0) + 1
        )

        if finding.source == FindingSource.STATIC_ANALYSIS:
            computed_static += 1
        elif finding.source == FindingSource.AI_REVIEW:
            computed_ai += 1
        elif finding.source == FindingSource.HYBRID:
            # Hybrid findings count as static + AI hybrid
            pass

    # 5. Verify computed metrics match metrics object
    if metrics.static_findings_count != computed_static:
        errors.append(
            f"metrics.static_findings_count ({metrics.static_findings_count}) does not match "
            f"actual static findings count ({computed_static})."
        )

    if metrics.ai_findings_count != computed_ai:
        errors.append(
            f"metrics.ai_findings_count ({metrics.ai_findings_count}) does not match "
            f"actual AI findings count ({computed_ai})."
        )

    for sev_name, expected_count in computed_by_severity.items():
        actual_count = metrics.findings_by_severity.get(sev_name, 0)
        if actual_count != expected_count:
            errors.append(
                f"metrics.findings_by_severity['{sev_name}'] mismatch: expected {expected_count}, got {actual_count}."
            )

    for cat_name, expected_count in computed_by_category.items():
        actual_count = metrics.findings_by_category.get(cat_name, 0)
        if actual_count != expected_count:
            errors.append(
                f"metrics.findings_by_category['{cat_name}'] mismatch: expected {expected_count}, got {actual_count}."
            )

    # 6. Limitations invariant
    if not output.limitations:
        errors.append("limitations list cannot be empty.")
    elif len(output.limitations) < 3:
        errors.append("limitations list must comprehensively document code review scope constraints (>= 3 items).")

    return ValidationResult(
        is_valid=len(errors) == 0,
        errors=errors,
    )
