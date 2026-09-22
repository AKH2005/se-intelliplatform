"""Deterministic Domain Validation for Test Case Generation Agent."""

import re
from typing import Any
import uuid

from app.agents.contracts import ValidationResult
from app.agents.test_case_generation.contracts import (
    TestCase,
    TestCaseGenerationOutput,
    TestPriority,
    TestType,
)
from app.models.requirement import RequirementStatus
from app.schemas.context import ProjectContextResponse


def get_active_requirement_ids(context: ProjectContextResponse) -> set[str]:
    """Extract set of active requirement UUID strings from canonical context.

    Active requirements are those in DRAFT, APPROVED, or IMPLEMENTED status.
    DEFERRED and REJECTED requirements are excluded.
    """
    active_ids: set[str] = set()
    for req in context.requirements:
        status_val = req.status.value if hasattr(req.status, "value") else str(req.status)
        if status_val not in (RequirementStatus.DEFERRED.value, RequirementStatus.REJECTED.value, "DEFERRED", "REJECTED"):
            active_ids.add(str(req.id))
    return active_ids


def get_all_context_requirement_ids(context: ProjectContextResponse) -> dict[str, str]:
    """Map all context requirement UUID strings to their lifecycle status."""
    return {
        str(req.id): (req.status.value if hasattr(req.status, "value") else str(req.status))
        for req in context.requirements
    }


def validate_test_case_generation_output(
    output: TestCaseGenerationOutput,
    context: ProjectContextResponse,
) -> ValidationResult:
    """Perform rigorous deterministic validation on TestCaseGenerationOutput.

    Enforces:
      1. Structural consistency: total_test_cases matches actual list length.
      2. Unique test case IDs: No duplicate test_case_id in the suite.
      3. Field completeness: Titles, descriptions, and expected results must be non-empty.
      4. Step sequencing: At least 1 step; step_number strictly sequential 1, 2, 3...
      5. Requirement traceability:
         - Every test case must reference at least one requirement.
         - Referenced requirement IDs must exist in canonical context.
         - Referenced requirements must be active (DEFERRED/REJECTED are forbidden).
      6. Duplicate prevention: Semantic duplicates (identical title and actions) rejected.
      7. Authoritative coverage: Deterministic validation of backend-calculated coverage metrics.
      8. Limitations: Non-empty list documenting empirical scope constraints.
    """
    errors: list[str] = []

    # 1. Total count invariant
    if output.total_test_cases != len(output.test_cases):
        errors.append(
            f"total_test_cases ({output.total_test_cases}) does not match "
            f"actual number of test cases ({len(output.test_cases)})."
        )

    # 2. Context requirements lookup
    active_req_ids = get_active_requirement_ids(context)
    all_req_status = get_all_context_requirement_ids(context)

    # Tracking for uniqueness and coverage
    seen_ids: set[str] = set()
    seen_semantic_fingerprints: set[tuple[str, tuple[str, ...], tuple[str, ...]]] = set()
    covered_active_req_ids: set[str] = set()

    for idx, tc in enumerate(output.test_cases):
        case_prefix = f"Test case [{tc.test_case_id or f'index {idx}'}]"

        # Unique test case ID
        raw_id = tc.test_case_id.strip()
        if not raw_id:
            errors.append(f"{case_prefix}: test_case_id cannot be blank.")
        elif raw_id in seen_ids:
            errors.append(f"Duplicate test_case_id '{raw_id}' detected in test suite.")
        else:
            seen_ids.add(raw_id)

        # Non-empty title, description, expected_result
        if not tc.title.strip():
            errors.append(f"{case_prefix}: title cannot be empty or whitespace only.")
        if not tc.description.strip():
            errors.append(f"{case_prefix}: description cannot be empty or whitespace only.")
        if not tc.expected_result.strip():
            errors.append(f"{case_prefix}: expected_result cannot be empty or whitespace only.")

        # Enum validity
        if not isinstance(tc.test_type, TestType):
            try:
                TestType(str(tc.test_type))
            except ValueError:
                errors.append(f"{case_prefix}: invalid test_type '{tc.test_type}'.")

        if not isinstance(tc.priority, TestPriority):
            try:
                TestPriority(str(tc.priority))
            except ValueError:
                errors.append(f"{case_prefix}: invalid priority '{tc.priority}'.")

        # Steps validation
        if not tc.steps:
            errors.append(f"{case_prefix}: must contain at least one test step.")
        else:
            for step_idx, step in enumerate(tc.steps, start=1):
                if step.step_number != step_idx:
                    errors.append(
                        f"{case_prefix}: step numbering must be sequential starting from 1. "
                        f"Expected step_number {step_idx}, got {step.step_number}."
                    )
                if not step.action.strip():
                    errors.append(f"{case_prefix}, step {step_idx}: action cannot be empty.")
                if not step.expected_behavior.strip():
                    errors.append(f"{case_prefix}, step {step_idx}: expected_behavior cannot be empty.")

        # Requirement traceability validation
        if not tc.requirement_ids:
            errors.append(f"{case_prefix}: requirement_ids cannot be empty; every test case must trace to a requirement.")
        else:
            for req_id_str in tc.requirement_ids:
                req_id_clean = str(req_id_str).strip()
                if req_id_clean not in all_req_status:
                    errors.append(
                        f"{case_prefix}: references non-existent requirement ID '{req_id_clean}'."
                    )
                elif req_id_clean not in active_req_ids:
                    status_name = all_req_status.get(req_id_clean, "UNKNOWN")
                    errors.append(
                        f"{case_prefix}: references requirement '{req_id_clean}' with inactive status '{status_name}'. "
                        f"DEFERRED and REJECTED requirements cannot be tested."
                    )
                else:
                    covered_active_req_ids.add(req_id_clean)

        # Semantic duplicate detection
        normalized_title = tc.title.strip().lower()
        normalized_reqs = tuple(sorted(str(r).strip() for r in tc.requirement_ids))
        normalized_actions = tuple(s.action.strip().lower() for s in tc.steps)
        semantic_fingerprint = (normalized_title, normalized_reqs, normalized_actions)

        if semantic_fingerprint in seen_semantic_fingerprints:
            errors.append(
                f"{case_prefix}: semantic duplicate test case detected with identical title, requirements, and actions."
            )
        else:
            seen_semantic_fingerprints.add(semantic_fingerprint)

    # 3. Coverage calculation validation
    cov = output.coverage
    expected_total_active = len(active_req_ids)
    expected_covered = len(covered_active_req_ids)
    expected_uncovered = expected_total_active - expected_covered
    expected_pct = (
        round((expected_covered / expected_total_active) * 100.0, 2)
        if expected_total_active > 0
        else 0.0
    )

    if cov.total_active_requirements != expected_total_active:
        errors.append(
            f"coverage.total_active_requirements mismatch: expected {expected_total_active}, "
            f"got {cov.total_active_requirements}."
        )

    if cov.requirements_with_tests != expected_covered:
        errors.append(
            f"coverage.requirements_with_tests mismatch: expected {expected_covered}, "
            f"got {cov.requirements_with_tests}."
        )

    if cov.requirements_without_tests != expected_uncovered:
        errors.append(
            f"coverage.requirements_without_tests mismatch: expected {expected_uncovered}, "
            f"got {cov.requirements_without_tests}."
        )

    if abs(cov.coverage_percentage - expected_pct) > 0.01:
        errors.append(
            f"coverage.coverage_percentage mismatch: expected {expected_pct:.2f}%, "
            f"got {cov.coverage_percentage:.2f}%."
        )

    # 4. Limitations invariant
    if not output.limitations:
        errors.append("limitations list cannot be empty.")
    elif len(output.limitations) < 3:
        errors.append("limitations list must comprehensively document testing scope constraints.")

    return ValidationResult(
        is_valid=len(errors) == 0,
        errors=errors,
    )
