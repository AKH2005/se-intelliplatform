"""Prompt Templates for Test Case Generation Agent."""

from typing import Any
from app.schemas.context import ProjectContextResponse
from app.schemas.requirement import RequirementResponse

SYSTEM_PROMPT = """You are a Principal Quality Assurance & Test Engineering Architect for SE IntelliPlatform.
Your role is to analyze software project requirements and design comprehensive, structured test suites.

Guidelines for Test Case Design:
1. TRACEABILITY: Every generated test case MUST cite one or more real requirement IDs provided in the context. Never invent fake requirement IDs.
2. COVERAGE: Generate balanced test coverage across:
   - FUNCTIONAL: Core happy path and expected user workflows
   - NEGATIVE: Invalid input handling, error scenarios, and authentication/authorization boundaries
   - EDGE_CASE: Boundary values, extreme loads, null/empty conditions, and concurrent race limits
   - VALIDATION: Data format compliance, validation constraints, and business logic rules
3. STRUCTURE: Each test case must have:
   - Unique test_case_id (e.g. TC-001, TC-002)
   - Descriptive title and clear description
   - Appropriate test_type and priority
   - Preconditions
   - Sequential, numbered steps starting from 1 (each with an action and expected behavior)
   - Final expected_result
   - requirement_ids mapping to provided requirement UUIDs
4. DETERMINISTIC FIDELITY: Rely strictly on stated requirements and acceptance criteria. Do not speculate or make unsupported architectural assumptions.
"""


def build_test_case_prompt(
    context: ProjectContextResponse,
    analysis_result: dict[str, Any],
) -> str:
    """Format canonical project context and active requirements into an LLM user prompt."""
    project = context.project
    active_requirements: list[RequirementResponse] = analysis_result.get("active_requirements", [])

    req_lines = []
    for req in active_requirements:
        req_lines.append(
            f"- Requirement ID: {req.id}\n"
            f"  Title: {req.title}\n"
            f"  Type: {req.type.value if hasattr(req.type, 'value') else req.type}\n"
            f"  Priority: {req.priority.value if hasattr(req.priority, 'value') else req.priority}\n"
            f"  Description: {req.description}\n"
        )

    requirements_text = "\n".join(req_lines) if req_lines else "(No active requirements available in context)"

    prompt = f"""PROJECT CONTEXT:
Name: {project.name}
Description: {project.description or 'No description provided.'}
Total Active Requirements: {len(active_requirements)}

ACTIVE REQUIREMENTS:
{requirements_text}

INSTRUCTIONS:
1. Analyze the active requirements above.
2. Formulate a comprehensive test suite of structured test cases.
3. For each test case, ensure requirement_ids contains ONLY UUIDs from the Active Requirements listed above.
4. Ensure test steps are sequentially numbered (step 1, step 2, ...) with actionable descriptions.
5. Provide a clear summary of the overall testing approach and key risk areas addressed.
"""
    return prompt
