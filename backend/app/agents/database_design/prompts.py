"""Prompt Templates and Construction for Database Design Agent."""

from typing import Any
from app.agents.architecture_recommendation.contracts import ArchitectureRecommendationOutput
from app.agents.requirement_analysis.contracts import RequirementAnalysisOutput
from app.schemas.context import ProjectContextResponse

SYSTEM_PROMPT = """You are the specialized Database Design Agent for SE IntelliPlatform.
Your role is to analyze canonical software requirements, optional requirement analysis findings, and optional architecture recommendations to propose structured, modular, and explainable logical database designs.

Core Principles & Directives:
1. Analyze ONLY the supplied project context, requirement analysis findings, and architecture recommendations.
2. Logical Design ONLY: Propose vendor-neutral logical entities and attributes. NEVER produce executable SQL, DDL (`CREATE TABLE`), or migration scripts.
3. Allowed Enums (must match EXACT string):
   - DatabaseParadigm: "RELATIONAL", "DOCUMENT", "KEY_VALUE", "GRAPH", "SEARCH"
   - DataType: "STRING", "INTEGER", "DECIMAL", "BOOLEAN", "DATE", "DATETIME", "TIMESTAMP", "UUID", "JSON", "TEXT", "BINARY"
   - RelationshipType: "ONE_TO_ONE", "ONE_TO_MANY", "MANY_TO_ONE", "MANY_TO_MANY"
   - ConstraintType: "UNIQUE", "NOT_NULL", "CHECK", "PRIMARY_KEY", "FOREIGN_KEY"
4. Entity & Primary Key Integrity:
   - Every entity in `entities` MUST have a unique name.
   - Within each entity, attribute names MUST be unique.
   - Attribute Default Values: If an attribute has NO default value, set `default_value` to `null` (or omit the field). NEVER output an empty string `""` for `default_value`. If a default value is intended, provide a valid, non-empty expression (e.g. '0', 'CURRENT_TIMESTAMP', 'uuid_generate_v4()'). Never invent artificial defaults when none is intended.
   - MANDATORY: EVERY SINGLE entity in `entities` (including audit, log, history, or associative entities) MUST explicitly include the `primary_key` object: `{"attributes": ["<id_attribute>"], "is_composite": false}`. Never omit `primary_key` from any entity.
   - If `primary_key.attributes` has more than 1 attribute, set `is_composite=True`.
5. Explicit Foreign-Key Ownership:
   - For every relationship in `relationships`:
     - `source_entity` and `target_entity` must exist in declared `entities`.
     - `foreign_key_entity` and `referenced_entity` must be among `{source_entity, target_entity}` (or `junction_entity`).
     - `foreign_key_attributes` MUST exist as declared attributes in `foreign_key_entity`.
     - `referenced_attributes` MUST exist as declared attributes in `referenced_entity`.
     - `len(foreign_key_attributes)` MUST equal `len(referenced_attributes)`.
6. Indexes & Constraints:
   - In `indexes`, `entity` and its `attributes` MUST exist in declared entities. Index names must be unique.
   - In `constraints`, `entity` and its `attributes` MUST exist in declared entities.
7. Traceability:
   - In `requirement_traceability`, every `requirement_id` must be an exact UUID from the canonical requirements, and `entity_names` must be a non-empty list of entity names declared in `entities` (each entry must contain at least one entity name). Only trace requirements that are realized or stored by persistent entities.
   - In `architecture_traceability`, ONLY include architecture components that directly manage, store, or query persistent database entities:
     - Each entry in `architecture_traceability` MUST contain `architecture_component` matching an exact component name from the architecture input, and `entity_names` MUST be a non-empty list containing AT LEAST ONE declared entity name (e.g. `["User"]`).
     - NEVER output an empty list `[]` for `entity_names`.
     - Non-persistence components (such as frontend UI, browser clients, web pages, or API routers) that do not manage database entities MUST NOT be included in `architecture_traceability`.
     - If no architecture recommendations were provided, keep `architecture_traceability` empty `[]`.
8. Trade-Offs: Every trade-off item in `trade_offs` MUST specify at least one advantage and at least one disadvantage.
9. Distinguish Categories:
   - Facts: Derived directly from requirements.
   - Assumptions: Working hypotheses regarding volume, concurrency, or access patterns.
   - Trade-offs: Honest pros and cons of selected data models versus alternatives.
   - Unknowns: Open questions regarding retention, encryption, or auditing requiring stakeholder answers.
10. Advisory Nature: Never declare that a schema has been migrated, deployed, or executed. These are advisory recommendations for human engineering review.
11. Return structured candidate recommendations conforming strictly to the required schema. Ensure all required fields have valid, non-empty values.
"""


def build_database_design_prompt(
    context: ProjectContextResponse,
    requirement_analysis: RequirementAnalysisOutput | None = None,
    architecture_recommendation: ArchitectureRecommendationOutput | None = None,
) -> str:
    """Construct structured user prompt containing canonical context and optional Phase 4 & Phase 5 inputs."""
    project = context.project
    requirements = context.requirements

    # 1. Format Requirements
    req_lines: list[str] = []
    if not requirements:
        req_lines.append("No active requirements recorded for this project.")
    else:
        for idx, req in enumerate(requirements, start=1):
            desc = req.description.strip()
            if len(desc) > 250:
                desc = desc[:247] + "..."
            req_lines.append(
                f"[{idx}] UUID: {req.id}\n"
                f"    Title: {req.title}\n"
                f"    Type: {req.type.value} | Priority: {req.priority.value}\n"
                f"    Description: {desc}\n"
            )
    requirements_block = "\n".join(req_lines)

    # 2. Format Phase 4 Findings if injected
    req_analysis_block = "None provided (standalone database design mode)."
    if requirement_analysis is not None:
        analysis_parts: list[str] = [f"Summary: {requirement_analysis.summary}"]
        if requirement_analysis.conflicts:
            analysis_parts.append(f"Identified Conflicts ({len(requirement_analysis.conflicts)}):")
            for c in requirement_analysis.conflicts[:3]:
                analysis_parts.append(f"  - Between {c.requirement_id} and {c.related_requirement_id}: {c.issue}")
        if requirement_analysis.ambiguities:
            analysis_parts.append(f"Identified Ambiguities ({len(requirement_analysis.ambiguities)}):")
            for a in requirement_analysis.ambiguities[:3]:
                analysis_parts.append(f"  - Req {a.requirement_id}: {a.issue}")
        if requirement_analysis.missing_information:
            analysis_parts.append(f"Missing Specifications ({len(requirement_analysis.missing_information)}):")
            for m in requirement_analysis.missing_information[:3]:
                analysis_parts.append(f"  - Area '{m.area}': {m.description}")
        req_analysis_block = "\n".join(analysis_parts)

    # 3. Format Phase 5 Findings if injected
    arch_block = "None provided (standalone database design mode)."
    if architecture_recommendation is not None:
        arch_parts: list[str] = [f"Summary: {architecture_recommendation.summary}"]
        if architecture_recommendation.architecture_styles:
            arch_parts.append("Proposed Architecture Styles:")
            for s in architecture_recommendation.architecture_styles[:2]:
                arch_parts.append(f"  - Style: {s.style.value} (confidence: {s.confidence}) - {s.rationale[:120]}")
        if architecture_recommendation.components:
            arch_parts.append("Logical Architecture Components:")
            for c in architecture_recommendation.components:
                c_resp = c.responsibility[:150] if len(c.responsibility) > 150 else c.responsibility
                arch_parts.append(f"  - Component: {c.name}: {c_resp}")
            arch_parts.append(
                "\n  * IMPORTANT RULE for architecture_traceability: Only include components that directly manage or persist database entities. "
                "Every entry in `architecture_traceability` MUST have `entity_names` containing at least one declared entity name. "
                "Do NOT include non-persistent components (like UI or Frontend), and NEVER output an empty list `[]` for entity_names."
            )
        arch_block = "\n".join(arch_parts)

    prompt = (
        f"Project: {project.name} (slug: {project.slug})\n"
        f"Project Status: {project.status.value}\n"
        f"Project Description: {project.description or 'None provided'}\n\n"
        f"--- CANONICAL REQUIREMENTS ({len(requirements)} active) ---\n"
        f"{requirements_block}\n"
        f"--- END REQUIREMENTS ---\n\n"
        f"--- PHASE 4 REQUIREMENT ANALYSIS FINDINGS ---\n"
        f"{req_analysis_block}\n"
        f"--- END REQUIREMENT ANALYSIS FINDINGS ---\n\n"
        f"--- PHASE 5 ARCHITECTURE RECOMMENDATIONS ---\n"
        f"{arch_block}\n"
        f"--- END ARCHITECTURE RECOMMENDATIONS ---\n\n"
        f"Based on the project context and upstream inputs above, recommend a logical database design. "
        f"Propose recommended database paradigm, logical entities, attributes with data types, primary keys, "
        f"relationships with explicit foreign key ownership, performance indexes, domain constraints, "
        f"trade-off analyses, assumptions, unknowns, requirement traceability, and architecture component traceability.\n\n"
        f"CRITICAL SCHEMA RULES:\n"
        f"- For attribute default values: Set `default_value` to null (or omit it) when no default is intended. Never use empty string \"\".\n"
        f"- For architecture_traceability: Include only components that own database entities, and ensure `entity_names` has at least one entity name. Never use empty list []."
    )
    return prompt
