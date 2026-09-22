"""Deterministic Validation Hook for Architecture Recommendation Agent."""

from app.agents.architecture_recommendation.contracts import (
    ArchitectureRecommendationOutput,
    ArchitectureStyle,
    TechnologyCategory,
)
from app.agents.contracts import ValidationResult
from app.schemas.context import ProjectContextResponse


def validate_architecture_recommendation_output(
    output: ArchitectureRecommendationOutput,
    context: ProjectContextResponse,
) -> ValidationResult:
    """Authoritative deterministic validation hook for ArchitectureRecommendationOutput.
    
    Verifies:
    1. Requirement Traceability: All requirement UUIDs referenced by components or the
       traceability matrix must exist as active requirements in canonical context.
    2. Component Uniqueness: Component names must be unique across the recommendation.
    3. Data-Flow Referential Integrity: Every source_component and target_component in
       data_flows must match a declared component name, and source != target.
    4. Traceability Component Integrity: Every component named in the traceability matrix
       must match a declared component name.
    5. Domain Enums: Validates allowed ArchitectureStyle and TechnologyCategory values.
    6. Trade-off Completeness: Ensures non-empty trade-off evaluations.
    """
    errors: list[str] = []

    # 1. Index valid active requirement IDs from canonical context
    valid_active_req_ids = {req.id for req in context.requirements}

    # 2. Validate Component Uniqueness
    declared_component_names: set[str] = set()
    normalized_names: set[str] = set()

    for idx, comp in enumerate(output.components):
        norm = comp.name.strip().lower()
        if norm in normalized_names:
            errors.append(
                f"Component [{idx}] has duplicate name: '{comp.name}'. Component names must be unique."
            )
        normalized_names.add(norm)
        declared_component_names.add(comp.name)

        # Validate component related requirement IDs
        for req_id in comp.related_requirement_ids:
            if req_id not in valid_active_req_ids:
                errors.append(
                    f"Component '{comp.name}' references nonexistent or inactive requirement ID: {req_id}"
                )

    # 3. Validate Data Flows
    for idx, flow in enumerate(output.data_flows):
        if flow.source_component not in declared_component_names:
            errors.append(
                f"Data flow [{idx}] references unknown source_component: '{flow.source_component}'"
            )
        if flow.target_component not in declared_component_names:
            errors.append(
                f"Data flow [{idx}] references unknown target_component: '{flow.target_component}'"
            )
        if flow.source_component == flow.target_component:
            errors.append(
                f"Data flow [{idx}] has identical source and target component: '{flow.source_component}'"
            )

    # 4. Validate Traceability Matrix
    for idx, trace in enumerate(output.traceability_matrix):
        if trace.requirement_id not in valid_active_req_ids:
            errors.append(
                f"Traceability item [{idx}] references nonexistent or inactive requirement ID: {trace.requirement_id}"
            )
        for c_name in trace.component_names:
            if c_name not in declared_component_names:
                errors.append(
                    f"Traceability item [{idx}] for req {trace.requirement_id} references unknown component: '{c_name}'"
                )

    # 5. Validate Architecture Styles
    for idx, style_rec in enumerate(output.architecture_styles):
        if not isinstance(style_rec.style, ArchitectureStyle):
            errors.append(
                f"Architecture style [{idx}] '{style_rec.style}' is not a valid ArchitectureStyle."
            )

    # 6. Validate Technology Categories
    for idx, tech in enumerate(output.technologies):
        if not isinstance(tech.category, TechnologyCategory):
            errors.append(
                f"Technology [{idx}] '{tech.technology}' has invalid category: '{tech.category}'."
            )

    # 7. Validate Trade-Offs
    for idx, trade_off in enumerate(output.trade_offs):
        if not trade_off.advantages:
            errors.append(f"Trade-off [{idx}] '{trade_off.decision_area}' must specify at least one advantage.")
        if not trade_off.disadvantages:
            errors.append(f"Trade-off [{idx}] '{trade_off.decision_area}' must specify at least one disadvantage.")

    return ValidationResult(
        is_valid=len(errors) == 0,
        errors=errors,
    )
