"""Deterministic Validation Hook for Database Design Agent."""

from app.agents.architecture_recommendation.contracts import ArchitectureRecommendationOutput
from app.agents.contracts import ValidationResult
from app.agents.database_design.contracts import (
    ConstraintType,
    DatabaseDesignOutput,
    DatabaseParadigm,
    DataType,
    RelationshipType,
)
from app.schemas.context import ProjectContextResponse


def validate_database_design_output(
    output: DatabaseDesignOutput,
    context: ProjectContextResponse,
    architecture_recommendation: ArchitectureRecommendationOutput | None = None,
) -> ValidationResult:
    """Authoritative deterministic validation hook for DatabaseDesignOutput.
    
    Verifies:
    1. Entity Uniqueness: Entity names must be globally unique across the design.
    2. Attribute Uniqueness: Attribute names must be unique within each entity.
    3. Primary Key Consistency: Every entity must have non-empty primary key attributes
       that exist in the entity's declared attributes.
    4. Explicit Foreign-Key Ownership:
       - foreign_key_entity and referenced_entity must exist.
       - foreign_key_attributes must exist in foreign_key_entity.
       - referenced_attributes must exist in referenced_entity.
       - foreign_key_entity and referenced_entity must match the relationship peers.
       - Attribute count parity between foreign_key_attributes and referenced_attributes.
    5. Index Integrity:
       - Target entity must exist.
       - Indexed attributes must exist in target entity.
       - Index names must be globally unique.
    6. Constraint Integrity & Non-Contradiction:
       - Target entity must exist and attributes must exist in target entity.
       - Additional PRIMARY_KEY constraints must NOT contradict entity.primary_key.
    7. Requirement Traceability:
       - All requirement UUIDs must exist as active requirements in canonical context.
       - All entity names in requirement traces must exist.
    8. Architecture Traceability:
       - Referenced architecture components must exist in supplied Phase 5 recommendations.
       - When Phase 5 input is absent, architecture components cannot be invented.
       - All entity names in architecture traces must exist.
    """
    errors: list[str] = []

    # 0. Validate Database Paradigm
    if not isinstance(output.database_paradigm, DatabaseParadigm):
        errors.append(f"Database paradigm '{output.database_paradigm}' is not a valid DatabaseParadigm.")

    # 1. Index declared entities and attributes
    declared_entity_names: set[str] = set()
    normalized_entity_names: set[str] = set()
    entity_attributes_map: dict[str, set[str]] = {}
    entity_pk_map: dict[str, list[str]] = {}

    for idx, entity in enumerate(output.entities):
        norm_name = entity.name.strip().lower()
        if norm_name in normalized_entity_names:
            errors.append(f"Entity [{idx}] has duplicate name: '{entity.name}'. Entity names must be unique.")
        normalized_entity_names.add(norm_name)
        declared_entity_names.add(entity.name)

        # Attribute validation within entity
        attr_set: set[str] = set()
        norm_attr_set: set[str] = set()
        for a_idx, attr in enumerate(entity.attributes):
            norm_a = attr.name.strip().lower()
            if norm_a in norm_attr_set:
                errors.append(
                    f"Entity '{entity.name}' has duplicate attribute [{a_idx}]: '{attr.name}'."
                )
            norm_attr_set.add(norm_a)
            attr_set.add(attr.name)
            if not isinstance(attr.data_type, DataType):
                errors.append(
                    f"Attribute '{attr.name}' in entity '{entity.name}' has invalid DataType: '{attr.data_type}'."
                )

        entity_attributes_map[entity.name] = attr_set

        # Primary Key validation
        pk = entity.primary_key
        if not pk.attributes:
            errors.append(f"Entity '{entity.name}' primary_key attributes list cannot be empty.")
        for pk_attr in pk.attributes:
            if pk_attr not in attr_set:
                errors.append(
                    f"Entity '{entity.name}' primary_key references undeclared attribute: '{pk_attr}'."
                )
        if len(pk.attributes) > 1 and not pk.is_composite:
            errors.append(
                f"Entity '{entity.name}' has {len(pk.attributes)} primary key attributes but is_composite is False."
            )
        entity_pk_map[entity.name] = pk.attributes

    # 2. Validate Relationships with Explicit Foreign-Key Ownership
    for idx, rel in enumerate(output.relationships):
        # Entity existence
        if rel.source_entity not in declared_entity_names:
            errors.append(f"Relationship [{idx}] unknown source_entity: '{rel.source_entity}'.")
        if rel.target_entity not in declared_entity_names:
            errors.append(f"Relationship [{idx}] unknown target_entity: '{rel.target_entity}'.")
        if rel.foreign_key_entity not in declared_entity_names:
            errors.append(f"Relationship [{idx}] unknown foreign_key_entity: '{rel.foreign_key_entity}'.")
        if rel.referenced_entity not in declared_entity_names:
            errors.append(f"Relationship [{idx}] unknown referenced_entity: '{rel.referenced_entity}'.")
        if rel.junction_entity and rel.junction_entity not in declared_entity_names:
            errors.append(f"Relationship [{idx}] unknown junction_entity: '{rel.junction_entity}'.")

        # FK Ownership logic
        rel_entities = {rel.source_entity, rel.target_entity}
        if rel.junction_entity:
            rel_entities.add(rel.junction_entity)

        if rel.foreign_key_entity not in rel_entities:
            errors.append(
                f"Relationship [{idx}] foreign_key_entity '{rel.foreign_key_entity}' is not one of relationship peers {rel_entities}."
            )
        if rel.referenced_entity not in rel_entities:
            errors.append(
                f"Relationship [{idx}] referenced_entity '{rel.referenced_entity}' is not one of relationship peers {rel_entities}."
            )

        # Attribute existence for FK and referenced attributes
        if rel.foreign_key_entity in entity_attributes_map:
            fk_attrs = entity_attributes_map[rel.foreign_key_entity]
            for attr in rel.foreign_key_attributes:
                if attr not in fk_attrs:
                    errors.append(
                        f"Relationship [{idx}] foreign_key_attribute '{attr}' does not exist in foreign_key_entity '{rel.foreign_key_entity}'."
                    )

        if rel.referenced_entity in entity_attributes_map:
            ref_attrs = entity_attributes_map[rel.referenced_entity]
            for attr in rel.referenced_attributes:
                if attr not in ref_attrs:
                    errors.append(
                        f"Relationship [{idx}] referenced_attribute '{attr}' does not exist in referenced_entity '{rel.referenced_entity}'."
                    )

        if len(rel.foreign_key_attributes) != len(rel.referenced_attributes):
            errors.append(
                f"Relationship [{idx}] parity mismatch: {len(rel.foreign_key_attributes)} foreign key attributes "
                f"vs {len(rel.referenced_attributes)} referenced attributes."
            )

        if not isinstance(rel.relationship_type, RelationshipType):
            errors.append(f"Relationship [{idx}] invalid RelationshipType: '{rel.relationship_type}'.")

    # 3. Validate Indexes
    declared_index_names: set[str] = set()
    for idx, index_rec in enumerate(output.indexes):
        norm_idx_name = index_rec.index_name.strip().lower()
        if norm_idx_name in declared_index_names:
            errors.append(f"Duplicate index name: '{index_rec.index_name}'. Index names must be unique.")
        declared_index_names.add(norm_idx_name)

        if index_rec.entity not in declared_entity_names:
            errors.append(f"Index [{idx}] '{index_rec.index_name}' references unknown entity: '{index_rec.entity}'.")
        else:
            e_attrs = entity_attributes_map[index_rec.entity]
            if not index_rec.attributes:
                errors.append(f"Index [{idx}] '{index_rec.index_name}' attributes list cannot be empty.")
            for attr in index_rec.attributes:
                if attr not in e_attrs:
                    errors.append(
                        f"Index [{idx}] '{index_rec.index_name}' references undeclared attribute '{attr}' in entity '{index_rec.entity}'."
                    )

    # 4. Validate Constraints & Check for Contradictions
    for idx, constraint in enumerate(output.constraints):
        if constraint.entity not in declared_entity_names:
            errors.append(f"Constraint [{idx}] references unknown entity: '{constraint.entity}'.")
        else:
            e_attrs = entity_attributes_map[constraint.entity]
            for attr in constraint.attributes:
                if attr not in e_attrs:
                    errors.append(
                        f"Constraint [{idx}] references undeclared attribute '{attr}' in entity '{constraint.entity}'."
                    )

            # Contradiction check: Primary Key
            if constraint.constraint_type == ConstraintType.PRIMARY_KEY:
                authoritative_pk = entity_pk_map.get(constraint.entity, [])
                if set(constraint.attributes) != set(authoritative_pk):
                    errors.append(
                        f"Constraint [{idx}] defines contradictory PRIMARY_KEY {constraint.attributes} "
                        f"for entity '{constraint.entity}' (authoritative primary_key is {authoritative_pk})."
                    )

        if not isinstance(constraint.constraint_type, ConstraintType):
            errors.append(f"Constraint [{idx}] invalid ConstraintType: '{constraint.constraint_type}'.")

    # 5. Validate Requirement Traceability
    valid_active_req_ids = {req.id for req in context.requirements}

    # Entity requirement references
    for entity in output.entities:
        for r_id in entity.related_requirement_ids:
            if r_id not in valid_active_req_ids:
                errors.append(f"Entity '{entity.name}' references nonexistent or inactive requirement ID: {r_id}")

    # Relationship requirement references
    for idx, rel in enumerate(output.relationships):
        for r_id in rel.related_requirement_ids:
            if r_id not in valid_active_req_ids:
                errors.append(f"Relationship [{idx}] references nonexistent or inactive requirement ID: {r_id}")

    # Traceability matrix
    for idx, trace in enumerate(output.requirement_traceability):
        if trace.requirement_id not in valid_active_req_ids:
            errors.append(
                f"Requirement trace [{idx}] references nonexistent or inactive requirement ID: {trace.requirement_id}"
            )
        for e_name in trace.entity_names:
            if e_name not in declared_entity_names:
                errors.append(
                    f"Requirement trace [{idx}] for req {trace.requirement_id} references unknown entity: '{e_name}'"
                )

    # 6. Validate Architecture Traceability (CTO Correction 4)
    if architecture_recommendation is not None:
        valid_arch_components = {comp.name for comp in architecture_recommendation.components}
        for idx, arch_trace in enumerate(output.architecture_traceability):
            if arch_trace.architecture_component not in valid_arch_components:
                errors.append(
                    f"Architecture trace [{idx}] references unknown component: '{arch_trace.architecture_component}'. "
                    f"Valid components: {valid_arch_components}"
                )
            for e_name in arch_trace.entity_names:
                if e_name not in declared_entity_names:
                    errors.append(
                        f"Architecture trace [{idx}] for component '{arch_trace.architecture_component}' references unknown entity: '{e_name}'"
                    )
    else:
        # Architecture recommendation was NOT supplied
        if output.architecture_traceability:
            errors.append(
                f"Architecture traceability cannot reference architecture components because no Phase 5 "
                f"ArchitectureRecommendationOutput was supplied as input."
            )

    return ValidationResult(
        is_valid=len(errors) == 0,
        errors=errors,
    )
