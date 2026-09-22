"""Prompt Templates and Construction for Requirement Analysis Agent."""

from typing import Any
from app.schemas.context import ProjectContextResponse


SYSTEM_PROMPT = """You are the specialized Requirement Analysis Agent for SE IntelliPlatform.
Your role is to perform rigorous software engineering analysis on requirements provided in the canonical Project Context.

Core Instructions:
1. Analyze ONLY the supplied requirements. Do not assume or invent facts outside the provided context.
2. Identify ambiguous, vague, or untestable statements in requirements.
3. Identify potential contradictions or conflicts between pairs of requirements.
4. Identify missing engineering information (e.g. error handling, scale constraints, auth requirements).
5. Suggest constructive refinements to improve clarity, testability, and feasibility.
6. Suggest scope clarifications where boundary conditions are unspecified.
7. NEVER invent requirement IDs. Every referenced requirement_id must be an exact UUID from the supplied requirements.
8. NEVER calculate authoritative project completion scores or statistics. Deterministic metrics are managed exclusively by the backend platform.
9. Distinguish observations from advisory suggestions. Suggestions are advisory only and will never automatically mutate requirements.
10. Return valid structured output conforming to the required schema.
"""


def build_analysis_prompt(
    context: ProjectContextResponse,
    analysis_features: dict[str, Any],
) -> str:
    """Build the structured user prompt containing canonical context for the LLM."""
    project = context.project
    requirements = context.requirements

    req_lines: list[str] = []
    if not requirements:
        req_lines.append("No active requirements recorded for this project.")
    else:
        for idx, req in enumerate(requirements, start=1):
            req_lines.append(
                f"[{idx}] UUID: {req.id}\n"
                f"    Title: {req.title}\n"
                f"    Type: {req.type.value} | Priority: {req.priority.value} | Status: {req.status.value}\n"
                f"    Description: {req.description.strip()}\n"
            )

    requirements_block = "\n".join(req_lines)

    prompt = (
        f"Project: {project.name} (slug: {project.slug})\n"
        f"Project Status: {project.status.value}\n"
        f"Project Description: {project.description or 'None provided'}\n\n"
        f"--- CANONICAL REQUIREMENTS ({len(requirements)} active) ---\n"
        f"{requirements_block}\n"
        f"--- END REQUIREMENTS ---\n\n"
        f"Please analyze these requirements according to your instructions. "
        f"Identify all ambiguities, conflicts between specific requirement UUIDs, missing architectural specifications, "
        f"advisory refinements, and scope clarification questions. "
        f"Ensure every referenced requirement_id matches an exact UUID listed above."
    )
    return prompt
