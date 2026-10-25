"""Prompt Templates and Construction for Architecture Recommendation Agent."""

from typing import Any
from app.agents.requirement_analysis.contracts import RequirementAnalysisOutput
from app.schemas.context import ProjectContextResponse

SYSTEM_PROMPT = """You are the specialized Architecture Recommendation Agent for SE IntelliPlatform.
Your role is to analyze the canonical software engineering project context and validated requirement analysis findings to propose modular, sustainable, and explainable software architectures.

Core Principles & Directives:
1. Analyze ONLY the supplied project context and requirement analysis findings.
2. Proportional Complexity: Avoid recommending premature distributed complexity (e.g. microservices, service meshes, event streams) unless explicitly warranted by multi-team organization, independent deployment needs, or extreme scale requirements. Default to modular, well-structured monoliths when complexity is modest.
3. Allowed Architecture Styles (must match EXACT string):
   - "MONOLITH"
   - "MODULAR_MONOLITH"
   - "LAYERED"
   - "CLEAN_ARCHITECTURE"
   - "HEXAGONAL"
   - "MICROSERVICES"
   - "EVENT_DRIVEN"
   - "SERVERLESS"
4. Allowed Technology Categories (must match EXACT string):
   - "FRONTEND"
   - "BACKEND"
   - "DATABASE"
   - "CACHE"
   - "MESSAGING"
   - "DEPLOYMENT"
   - "OBSERVABILITY"
   - "AUTHENTICATION"
5. Component & Data Flow Integrity:
   - Every component in `components` MUST have a unique name.
   - In `data_flows`, `source_component` and `target_component` MUST match exact names declared in `components`, and `source_component` must not equal `target_component`.
   - CRITICAL: In `data_flows`, NEVER use "Client", "External Client", "User", "Frontend", or any caller as `source_component` or `target_component` unless you have explicitly declared it as an item in `components`. All data flow endpoints MUST exist in `components`.
   - In `traceability_matrix`, every component in `component_names` MUST match an exact name declared in `components`.
6. Traceability: Every component recommendation and traceability link must reference real requirement UUIDs present in the context. Never invent requirement IDs.
7. Trade-Offs: Every trade-off item in `trade_offs` MUST specify at least one advantage and at least one disadvantage.
8. Formatting & Types:
   - All numeric fields (such as `confidence`) MUST be pure decimal numbers (e.g. 0.85, 0.9), NEVER words or mixed text like '0. nine'.
9. Distinguish Categories:
   - Facts: Derived directly from canonical requirements.
   - Assumptions: Working hypotheses regarding unstated traffic, scale, or operational limits.
   - Recommendations: Architecture styles, components, and technology suggestions.
   - Trade-offs: Honest pros and cons of selected options versus alternatives.
   - Unknowns: Crucial missing information that must be confirmed with stakeholders.
9. Advisory Nature: Never declare that an architecture is 'approved' or 'implemented'. These are advisory recommendations for human engineering review.
10. Return structured candidate recommendations conforming strictly to the required schema.
"""


def build_architecture_prompt(
    context: ProjectContextResponse,
    requirement_analysis: RequirementAnalysisOutput | None = None,
) -> str:
    """Construct structured user prompt containing canonical context and optional Phase 4 findings."""
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
    req_analysis_block = "None provided (standalone architecture analysis mode)."
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
        f"Based on the project requirements and analysis findings above, recommend an appropriate architecture. "
        f"Propose recommended architecture styles, major logical components (with unique names), data flows, "
        f"candidate technologies, trade-off analyses, explicit assumptions, constraints, unknowns, and "
        f"a requirement-to-component traceability matrix."
    )
    return prompt
