"""Prompt Templates and Construction for Database Design Agent."""

from typing import Any
from app.agents.architecture_recommendation.contracts import ArchitectureRecommendationOutput
from app.agents.requirement_analysis.contracts import RequirementAnalysisOutput
from app.schemas.context import ProjectContextResponse

SYSTEM_PROMPT = """You are the specialized Database Design Agent for SE IntelliPlatform.
Your role is to analyze canonical software requirements, optional requirement analysis findings, and optional architecture recommendations to propose structured, modular, and explainable logical database designs.

Core Principles & Directives:
1. Analyze ONLY the supplied project context, requirement analysis findings, and architecture recommendations.
2. Architecture components are advisory contextual input, NOT 1:1 database tables. Persist data entities implied by requirements and domain boundaries, not execution/gateway components.
3. Explicit Foreign-Key Ownership: Every relationship MUST unambiguously declare which entity holds the foreign key (`foreign_key_entity` and `foreign_key_attributes`) and which entity is referenced (`referenced_entity` and `referenced_attributes`).
4. Primary Keys: Every entity MUST declare explicit primary key attribute(s) that exist in its attribute list.
5. Traceability: Every entity and relationship requirement link must reference real requirement UUIDs present in the context. Never invent requirement IDs.
6. Distinguish Categories:
   - Facts: Derived directly from requirements.
   - Assumptions: Working hypotheses regarding volume, concurrency, or access patterns.
   - Trade-offs: Honest pros and cons of selected data models versus alternatives.
   - Unknowns: Open questions regarding retention, encryption, or auditing requiring stakeholder answers.
7. Advisory Nature: Never declare that a schema has been migrated, deployed, or executed. These are advisory recommendations for human engineering review.
8. Return structured candidate recommendations conforming strictly to the required schema.
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
            req_lines.append(
                f"[{idx}] UUID: {req.id}\n"
                f"    Title: {req.title}\n"
                f"    Type: {req.type.value} | Priority: {req.priority.value}\n"
                f"    Description: {req.description.strip()}\n"
            )
    requirements_block = "\n".join(req_lines)

    # 2. Format Phase 4 Findings if injected
    req_analysis_block = "None provided (standalone database design mode)."
    if requirement_analysis is not None:
        analysis_parts: list[str] = [f"Summary: {requirement_analysis.summary}"]
        if requirement_analysis.conflicts:
            analysis_parts.append(f"Identified Conflicts ({len(requirement_analysis.conflicts)}):")
            for c in requirement_analysis.conflicts:
                analysis_parts.append(f"  - Between {c.requirement_id} and {c.related_requirement_id}: {c.issue}")
        if requirement_analysis.ambiguities:
            analysis_parts.append(f"Identified Ambiguities ({len(requirement_analysis.ambiguities)}):")
            for a in requirement_analysis.ambiguities:
                analysis_parts.append(f"  - Req {a.requirement_id}: {a.issue}")
        if requirement_analysis.missing_information:
            analysis_parts.append(f"Missing Specifications ({len(requirement_analysis.missing_information)}):")
            for m in requirement_analysis.missing_information:
                analysis_parts.append(f"  - Area '{m.area}': {m.description}")
        req_analysis_block = "\n".join(analysis_parts)

    # 3. Format Phase 5 Findings if injected
    arch_block = "None provided (standalone database design mode)."
    if architecture_recommendation is not None:
        arch_parts: list[str] = [f"Summary: {architecture_recommendation.summary}"]
        if architecture_recommendation.architecture_styles:
            arch_parts.append("Proposed Architecture Styles:")
            for s in architecture_recommendation.architecture_styles:
                arch_parts.append(f"  - Style: {s.style.value} (confidence: {s.confidence}) - {s.rationale}")
        if architecture_recommendation.components:
            arch_parts.append("Logical Architecture Components:")
            for c in architecture_recommendation.components:
                arch_parts.append(f"  - Component: {c.name}: {c.responsibility}")
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
        f"trade-off analyses, assumptions, unknowns, requirement traceability, and architecture component traceability."
    )
    return prompt
