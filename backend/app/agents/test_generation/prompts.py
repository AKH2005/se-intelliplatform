"""Prompts and System Instructions for AI Test Generation Agent."""

from app.agents.test_generation.contracts import TestGenerationInput

SYSTEM_PROMPT = """You are a Senior Software Quality Assurance & Test Generation Engineer.
Your task is to generate meaningful, rigorous, and deterministic pytest test cases for a generated Python software project.

CRITICAL SECURITY AND SAFETY CONSTRAINTS:
1. All generated tests are UNTRUSTED code that will undergo strict deterministic AST parsing and security verification before execution.
2. DO NOT use or import dangerous modules: os, sys, subprocess, shutil, socket, requests, urllib, http, aiohttp, httpx, pty, ctypes.
3. DO NOT generate shell commands, system calls, network connections, or file system escapes.
4. DO NOT access or generate secrets, credentials, or API keys.
5. All test code must be valid Python pytest code.
6. Every test function name MUST begin with 'test_'.
7. Every test function MUST contain at least one meaningful assertion (using 'assert' or 'pytest.raises').
8. DO NOT write trivial tests like 'assert True' or empty test functions.
9. ONLY target files that exist in the supplied project manifest. DO NOT invent files.
10. ONLY use requirement IDs from the supplied project requirements list. DO NOT invent requirement IDs.
11. Return strictly structured JSON matching the requested schema.
"""


def build_test_generation_prompt(test_input: TestGenerationInput) -> str:
    """Construct structured user prompt providing bounded project context and files."""
    manifest_str = "\n".join(f"- {p}" for p in test_input.manifest)

    # Format available requirements
    if test_input.available_requirement_ids:
        reqs_str = "\n".join(f"- {rid}" for rid in test_input.available_requirement_ids)
    else:
        reqs_str = "- None specified (general functional testing permitted)"

    # Format available architecture components
    if test_input.available_architecture_components:
        arch_str = "\n".join(f"- {comp}" for comp in test_input.available_architecture_components)
    else:
        arch_str = "- None specified"

    # Format available database entities
    if test_input.available_database_entities:
        db_str = "\n".join(f"- {ent}" for ent in test_input.available_database_entities)
    else:
        db_str = "- None specified"

    # Format bounded source code
    files_str_parts = []
    for path, content in test_input.files.items():
        # Truncate large files if needed to keep prompt bounded
        bounded_content = content[:3000]
        if len(content) > 3000:
            bounded_content += "\n... [truncated for context limit]"
        files_str_parts.append(f"### File: {path}\n```python\n{bounded_content}\n```")
    files_str = "\n\n".join(files_str_parts)

    # Static analysis findings if available
    analysis_str = "None"
    if test_input.static_analysis_result:
        diag_summaries = [
            f"[{d.severity.value}] {d.code}: {d.message} in {d.file_path or 'unknown'}"
            for d in test_input.static_analysis_result.diagnostics[:5]
        ]
        analysis_str = "\n".join(diag_summaries) if diag_summaries else "Static analysis passed with no issues."

    # Failure diagnosis if available
    diag_str = "None"
    if test_input.failure_diagnosis:
        diag_str = f"{test_input.failure_diagnosis.title}: {test_input.failure_diagnosis.root_cause}"

    categories_str = ", ".join(c.value for c in test_input.allowed_categories)

    return f"""Analyze the following verified software project artifact and generate a structured suite of pytest test cases.

=== PROJECT MANIFEST ===
{manifest_str}

=== VERIFIED PROJECT SOURCE CODE ===
{files_str}

=== AVAILABLE REQUIREMENT IDENTIFIERS ===
{reqs_str}

=== ARCHITECTURE COMPONENTS ===
{arch_str}

=== DATABASE ENTITIES ===
{db_str}

=== STATIC ANALYSIS CONTEXT ===
{analysis_str}

=== PREVIOUS FAILURE CONTEXT ===
{diag_str}

=== INSTRUCTIONS ===
1. Generate between 2 and 5 targeted, high-value pytest tests.
2. Covered categories may include: {categories_str}.
3. CRITICAL FIELD MAPPINGS:
   - 'name': The exact Python test function name starting with 'test_' and containing only letters, numbers, and underscores (e.g. 'test_calculator_add_positive'). NEVER put spaces, punctuation, or sentences here.
   - 'test_id': Short identifier like 'TEST-001' or 'TC001'.
   - 'description': Human-readable title or explanation (e.g. 'Verify addition of positive integers').
4. Focus on:
   - Happy path: verifying functions produce correct outputs for typical inputs.
   - Edge cases: boundary conditions, empty collections, zero values.
   - Validation & Error Handling: verifying exceptions are raised for invalid inputs using 'pytest.raises'.
5. In each test's 'code' field, write the complete python function, e.g.:
```python
def test_calculator_add_positive():
    from app.calculator import add
    result = add(2, 3)
    assert result == 5
```
6. Ensure imports inside test functions or at top level target valid project files (e.g. 'from app.calculator import ...').
7. Do NOT use mocks that hide real logic unless external services are involved.
8. Return strictly valid JSON matching the AITestSuiteCandidate schema.
"""
