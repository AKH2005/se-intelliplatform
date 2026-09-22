"""Deterministic Business Validation Hook for Requirement Analysis Agent."""

import math
from app.agents.contracts import ValidationResult
from app.agents.requirement_analysis.contracts import RequirementAnalysisOutput
from app.models.requirement import RequirementPriority, RequirementType
from app.schemas.context import ProjectContextResponse


def validate_requirement_analysis_output(
    output: RequirementAnalysisOutput,
    context: ProjectContextResponse,
) -> ValidationResult:
    """Authoritative deterministic validation hook for RequirementAnalysisOutput.
    
    Verifies:
    1. Requirement ID existence: All referenced IDs must exist in canonical context.
    2. Active requirements constraint: Only active context requirements may be referenced.
    3. Conflict validity: Both IDs in a conflict pair must exist, be distinct, and be active.
    4. Domain Enum conformance: Any suggested types and priorities must be valid Phase 2 enums.
    5. Deterministic completeness integrity: Completeness score must match context.statistics.completion_percentage.
    6. Deterministic counts integrity: Active and total requirement counts must match context.statistics.
    """
    errors: list[str] = []

    # 1. Canonical active requirement ID index
    valid_active_ids = {req.id for req in context.requirements}

    # 2. Validate Ambiguity References
    for idx, ambiguity in enumerate(output.ambiguities):
        if ambiguity.requirement_id not in valid_active_ids:
            errors.append(
                f"Ambiguity [{idx}] references nonexistent or inactive requirement ID: {ambiguity.requirement_id}"
            )

    # 3. Validate Conflict References
    for idx, conflict in enumerate(output.conflicts):
        if conflict.requirement_id not in valid_active_ids:
            errors.append(
                f"Conflict [{idx}] primary requirement_id does not exist or is inactive: {conflict.requirement_id}"
            )
        if conflict.related_requirement_id not in valid_active_ids:
            errors.append(
                f"Conflict [{idx}] related_requirement_id does not exist or is inactive: {conflict.related_requirement_id}"
            )
        if conflict.requirement_id == conflict.related_requirement_id:
            errors.append(
                f"Conflict [{idx}] cannot reference the same requirement ID for both peers: {conflict.requirement_id}"
            )

    # 4. Validate Refinement References and Enums
    for idx, refinement in enumerate(output.refinements):
        if refinement.requirement_id not in valid_active_ids:
            errors.append(
                f"Refinement [{idx}] references nonexistent or inactive requirement ID: {refinement.requirement_id}"
            )
        if refinement.suggested_type is not None and not isinstance(refinement.suggested_type, RequirementType):
            errors.append(
                f"Refinement [{idx}] suggested_type '{refinement.suggested_type}' is not a valid RequirementType."
            )
        if refinement.suggested_priority is not None and not isinstance(refinement.suggested_priority, RequirementPriority):
            errors.append(
                f"Refinement [{idx}] suggested_priority '{refinement.suggested_priority}' is not a valid RequirementPriority."
            )

    # 5. Deterministic Completeness Verification
    expected_completion = context.statistics.completion_percentage
    if not math.isclose(output.completeness_score, expected_completion, abs_tol=1e-2):
        errors.append(
            f"Completeness score violation: output contains {output.completeness_score}, but canonical "
            f"deterministic completion_percentage is {expected_completion}."
        )

    # 6. Deterministic Counts Verification
    expected_active = context.statistics.active_requirements
    if output.active_requirements_count != expected_active:
        errors.append(
            f"Active requirements count violation: output contains {output.active_requirements_count}, "
            f"expected {expected_active}."
        )

    expected_total = context.statistics.total_requirements
    if output.total_requirements_count != expected_total:
        errors.append(
            f"Total requirements count violation: output contains {output.total_requirements_count}, "
            f"expected {expected_total}."
        )

    return ValidationResult(
        is_valid=len(errors) == 0,
        errors=errors,
    )
