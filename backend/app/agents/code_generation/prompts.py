"""System and User Prompts for Code Generation Planning and Code Generation Agents."""

from typing import Any
from app.agents.architecture_recommendation.contracts import ArchitectureRecommendationOutput
from app.agents.code_generation.contracts import CodeGenerationPlan
from app.agents.database_design.contracts import DatabaseDesignOutput
from app.agents.requirement_analysis.contracts import RequirementAnalysisOutput
from app.schemas.context import ProjectContextResponse


# ==============================================================================
# 1. Code Generation Planning Prompts
# ==============================================================================

PLANNING_SYSTEM_PROMPT = """You are the Senior Software Architect and Code Generation Planner for SE IntelliPlatform.
Your role is to propose a minimal, robust, modular project scaffold plan for a production service.

AUTHORITATIVE TARGET STACK:
- Language: python
- Framework: fastapi
- Database: postgresql
- Package Manager: pip

ARCHITECTURAL PRINCIPLES:
1. Conservative Scaffold Size: Propose between 3 and 6 core files that form a coherent skeleton.
   Typical structure:
   - `app/main.py`: FastAPI application entrypoint and route mounting.
   - `app/config.py`: Environment configuration using Pydantic Settings.
   - `app/models.py`: Database models or domain schemas grounded in the logical database design.
   - `app/api.py`: REST endpoint router handling domain operations.
   - `requirements.txt`: Python package dependencies.
   - `README.md`: Architecture overview and setup guide.
2. Path Safety: Every file path MUST be relative, using forward slashes (e.g., 'app/main.py').
   NEVER use absolute paths, Windows drive letters, or '..' path traversals.
3. Traceability:
   - Map each file's `requirement_ids` to the exact UUIDs of the canonical requirements it addresses.
   - Map `architecture_component` to the exact name of an upstream architecture component.
4. Completeness: Every planned file must have a clear, descriptive `purpose` (at least 5 characters).
5. Output: Return structured JSON matching the CodeGenerationPlan schema.
"""


def build_code_generation_plan_prompt(
    context: ProjectContextResponse,
    requirement_analysis: RequirementAnalysisOutput | None = None,
    architecture_recommendation: ArchitectureRecommendationOutput | None = None,
    database_design: DatabaseDesignOutput | None = None,
) -> str:
    """Construct prompt for the Code Generation Planning agent."""
    project = context.project
    requirements = context.requirements

    # Requirements block
    req_lines = [
        f"Requirement ID: {r.id} | Title: {r.title} | Priority: {r.priority.value}\n    Description: {r.description.strip()}"
        for r in requirements
    ]
    req_block = "\n".join(req_lines) if req_lines else "None recorded."

    # Architecture block
    arch_block = "None provided."
    if architecture_recommendation:
        if isinstance(architecture_recommendation, dict):
            summary = architecture_recommendation.get("summary", "None provided.")
            styles = architecture_recommendation.get("architecture_styles", [])
            comps = architecture_recommendation.get("components", [])
            arch_lines = [f"Summary: {summary}"]
            if styles:
                style_names = [s.get("style", "") if isinstance(s, dict) else getattr(s, "style", "") for s in styles]
                arch_lines.append(f"Styles: {', '.join(str(s) for s in style_names if s)}")
            if comps:
                arch_lines.append("Components:")
                for c in comps:
                    c_name = c.get("name", "") if isinstance(c, dict) else getattr(c, "name", "")
                    c_resp = c.get("responsibility", "") if isinstance(c, dict) else getattr(c, "responsibility", "")
                    arch_lines.append(f"  - {c_name}: {c_resp}")
            arch_block = "\n".join(arch_lines)
        else:
            arch_lines = [f"Summary: {architecture_recommendation.summary}"]
            if architecture_recommendation.architecture_styles:
                arch_lines.append(f"Styles: {', '.join(s.style.value for s in architecture_recommendation.architecture_styles)}")
            if architecture_recommendation.components:
                arch_lines.append("Components:")
                for c in architecture_recommendation.components:
                    arch_lines.append(f"  - {c.name}: {c.responsibility}")
            arch_block = "\n".join(arch_lines)

    # Database block
    db_block = "None provided."
    if database_design:
        if isinstance(database_design, dict):
            paradigm = database_design.get("database_paradigm", "relational")
            entities = database_design.get("entities", [])
            db_lines = [f"Paradigm: {paradigm}"]
            if entities:
                db_lines.append("Logical Entities:")
                for e in entities:
                    e_name = e.get("name", "") if isinstance(e, dict) else getattr(e, "name", "")
                    attrs = e.get("attributes", []) if isinstance(e, dict) else getattr(e, "attributes", [])
                    attr_strs = []
                    for a in attrs[:6]:
                        a_name = a.get("name", "") if isinstance(a, dict) else getattr(a, "name", "")
                        a_type = a.get("data_type", "") if isinstance(a, dict) else getattr(a, "data_type", "")
                        attr_strs.append(f"{a_name} ({a_type})")
                    joined_attrs = ", ".join(attr_strs)
                    db_lines.append(f"  - {e_name}: [{joined_attrs}]")
            db_block = "\n".join(db_lines)
        else:
            db_lines = [f"Paradigm: {database_design.database_paradigm.value}"]
            if database_design.entities:
                db_lines.append("Logical Entities:")
                for e in database_design.entities:
                    attrs = ", ".join(f"{a.name} ({a.data_type.value})" for a in e.attributes[:6])
                    db_lines.append(f"  - {e.name}: [{attrs}]")
            db_block = "\n".join(db_lines)

    return f"""Project: {project.name} (slug: {project.slug})
Description: {project.description or 'None provided'}

--- CANONICAL REQUIREMENTS ({len(requirements)} active) ---
{req_block}
--- END REQUIREMENTS ---

--- UPSTREAM ARCHITECTURE DESIGN ---
{arch_block}
--- END ARCHITECTURE DESIGN ---

--- UPSTREAM DATABASE DESIGN ---
{db_block}
--- END DATABASE DESIGN ---

Based on the canonical project context, architecture components, and database entities above,
generate a CodeGenerationPlan proposing a concise, production-ready Python/FastAPI project scaffold.
Ensure all file paths are safe, relative, and cleanly map to the upstream architecture components and requirements."""


# ==============================================================================
# 2. Code Generation Prompts
# ==============================================================================

GENERATION_SYSTEM_PROMPT = """You are the Senior Code Generation Engineer for SE IntelliPlatform.
Your role is to generate production-quality, clean, secure source code for each planned file in the manifest.

CRITICAL INVARIANTS:
1. THE CODE GENERATION PLAN IS AUTHORITATIVE:
   - You MUST generate code for EVERY file listed in the plan's manifest.
   - You MUST NOT generate any file that is NOT declared in the plan.
   - Keep file paths identical to the manifest.
2. ABSOLUTE ZERO SECRETS POLICY:
   - NEVER hardcode API keys, tokens, passwords, or connection credentials.
   - Always read credentials from environment variables using `os.getenv(...)` or Pydantic `BaseSettings`.
3. SYNTACTIC & STRUCTURAL INTEGRITY:
   - All Python code MUST be syntactically valid and parseable with Python's AST compiler.
   - Do NOT emit Markdown code blocks (```python) inside the JSON string values.
   - Do NOT emit placeholders like '... implement here ...'. Provide concrete, working skeleton implementations.
4. TRACEABILITY:
   - Implement routes, models, and logic that reflect the upstream architecture and database entities.
5. NO ARBITRARY SHELL EXECUTION:
   - Never generate shell scripts, deployment scripts, or executable system commands.
6. FORMAT:
   - Return a valid JSON object matching the CodeGenerationOutput candidate schema.
"""


def build_code_generation_prompt(
    context: ProjectContextResponse,
    plan: CodeGenerationPlan,
    architecture_recommendation: ArchitectureRecommendationOutput | None = None,
    database_design: DatabaseDesignOutput | None = None,
) -> str:
    """Construct prompt for the Code Generation agent."""
    project = context.project

    # Planned files manifest
    manifest_lines = [
        f"File {idx}: '{f.path}' ({f.file_type.value})\n"
        f"  Purpose: {f.purpose}\n"
        f"  Component: {f.architecture_component or 'General'}\n"
        f"  Requirements: {', '.join(f.requirement_ids) or 'None'}\n"
        f"  Dependencies: {', '.join(f.dependencies) or 'None'}"
        for idx, f in enumerate(plan.files, start=1)
    ]
    manifest_block = "\n".join(manifest_lines)

    # Database summary
    db_summary = "None provided."
    if database_design:
        if isinstance(database_design, dict):
            entities = database_design.get("entities", [])
            if entities:
                names = [e.get("name", "") if isinstance(e, dict) else getattr(e, "name", "") for e in entities]
                db_summary = f"Entities: {', '.join(n for n in names if n)}"
        elif database_design.entities:
            db_summary = f"Entities: {', '.join(e.name for e in database_design.entities)}"

    return f"""Project: {project.name}
Target Stack: {plan.language} / {plan.framework} / {plan.database} ({plan.package_manager})
Plan Rationale: {plan.rationale}
Database Context: {db_summary}

--- AUTHORITATIVE FILE MANIFEST ({len(plan.files)} files planned) ---
{manifest_block}
--- END MANIFEST ---

Generate complete, clean source code for all {len(plan.files)} planned files listed above.
Do not omit any planned file. Do not invent unplanned files.
Do not include any secrets, passwords, or API keys."""
