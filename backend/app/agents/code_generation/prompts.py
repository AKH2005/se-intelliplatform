"""System and User Prompts for Code Generation Planning and Code Generation Agents."""

from typing import Any
from app.agents.architecture_recommendation.contracts import ArchitectureRecommendationOutput
from app.agents.code_generation.contracts import CodeGenerationPlan, is_fullstack_project
from app.agents.database_design.contracts import DatabaseDesignOutput
from app.agents.requirement_analysis.contracts import RequirementAnalysisOutput
from app.schemas.context import ProjectContextResponse


# ==============================================================================
# 1. Code Generation Planning Prompts
# ==============================================================================

PLANNING_SYSTEM_PROMPT = """You are the Senior Software Architect and Code Generation Planner for SE IntelliPlatform.
Your role is to propose a minimal, robust, modular project scaffold plan for a production application.

SUPPORTED TARGET STACKS:
1. Backend Service (when no web UI or frontend is requested):
   - Language: python | Framework: fastapi | Database: postgresql/sqlite | Package Manager: pip
   - Files: app/main.py, app/config.py, app/models.py, app/api.py, app/persistence.py, requirements.txt, README.md
2. Full-Stack Application (when React, web interface, frontend, or dashboard is requested):
   - Language: polyglot | Framework: react+fastapi | Package Manager: npm+pip
   - Frontend files:
     - `frontend/package.json`: Dependencies for Vite, React, TypeScript.
     - `frontend/index.html`: Web entry HTML.
     - `frontend/src/main.tsx`: React mounting entrypoint.
     - `frontend/src/App.tsx`: Main React application component with task list, create, complete, and delete.
     - `frontend/src/components/TaskCard.tsx`: Task card component.
     - `frontend/src/components/TaskForm.tsx`: Task form component.
     - `frontend/src/services/api.ts`: API client connecting to FastAPI backend with env URL fallback.
     - `frontend/src/styles/App.css`: Modern styling.
   - Backend files:
     - `backend/requirements.txt`: Python package dependencies (fastapi, uvicorn, pydantic).
     - `backend/app/main.py`: FastAPI application entrypoint with CORS middleware.
     - `backend/app/config.py`: Environment configuration and allowed origins.
     - `backend/app/models.py`: Database models and Pydantic schemas.
     - `backend/app/api.py`: REST endpoint router handling domain operations.
     - `backend/app/persistence.py`: Thread-safe persistence repository.
   - Root documentation:
     - `README.md`: Architecture overview and setup guides for frontend and backend.

ARCHITECTURAL PRINCIPLES:
1. Full-Stack Invariant: If the project context, requirements, or architecture components specify a frontend (e.g. React, web UI, dashboard), you MUST propose the complete full-stack structure with both frontend/ and backend/ directories. Never generate a backend-only scaffold for a project that requires a React frontend.
2. Path Safety: Every file path MUST be relative, using forward slashes (e.g., 'frontend/src/App.tsx', 'backend/app/main.py'). NEVER use absolute paths, Windows drive letters, or '..' path traversals.
3. Traceability:
   - Map each file's `requirement_ids` to the exact UUIDs of the canonical requirements it addresses.
   - Map `architecture_component` to the exact name of an upstream architecture component.
     * Backend source and dependency files (e.g., `backend/requirements.txt`, `backend/app/main.py`) MUST map to the declared backend component (e.g., 'CoreService', 'Backend API', or similar). Never assign `requirements.txt` to 'Documentation'.
     * Frontend files (e.g., `frontend/src/App.tsx`, `frontend/package.json`) MUST map to the declared frontend component (e.g., 'Frontend', 'React UI', or similar).
     * Root documentation files (e.g., `README.md`) may have `architecture_component` set to null or match a declared component.
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

    fullstack = is_fullstack_project(context, architecture_recommendation)
    if fullstack:
        plan_instruction = (
            "The project explicitly requires a FULL-STACK application (React frontend + FastAPI backend).\n"
            "You MUST propose a complete full-stack scaffold including both 'frontend/' (package.json, index.html, "
            "src/main.tsx, src/App.tsx, src/components/TaskCard.tsx, src/components/TaskForm.tsx, src/services/api.ts, src/styles/App.css) and 'backend/' "
            "(requirements.txt, app/main.py with CORS, app/config.py, app/models.py, app/api.py, app/persistence.py), and 'README.md'.\n"
            "Set project_type='fullstack', language='polyglot', framework='react+fastapi', package_manager='npm+pip'."
        )
    else:
        plan_instruction = (
            "The project requires a backend service (Python/FastAPI).\n"
            "Generate a CodeGenerationPlan proposing a concise, production-ready Python/FastAPI project scaffold.\n"
            "Set project_type='backend-service', language='python', framework='fastapi', package_manager='pip'."
        )

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

{plan_instruction}
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
   - All JSON files (such as package.json) MUST be valid, parseable JSON without trailing commas.
   - All TypeScript / TSX and HTML files MUST be complete, well-formed, and functional.
   - Do NOT emit Markdown code blocks (```python, ```typescript) inside the JSON string values.
   - Do NOT emit placeholders like '... implement here ...'. Provide concrete, working implementations.
4. FULL-STACK COHESION:
   - When generating a full-stack project, ensure the FastAPI backend (`backend/app/main.py`) includes CORSMiddleware so the React frontend can communicate with it.
   - Serve the frontend entrypoint (`frontend/index.html`) at root `GET /` (e.g. via FileResponse) and mount static files if present.
   - Expose the health check endpoint `@app.get("/health")`.
   - Ensure the REST endpoints are accessible (e.g. `/api/tasks` and `/tasks`) and the frontend API client connects cleanly to the backend, handling errors and loading states.
5. TRACEABILITY:
   - Implement routes, models, and UI that reflect the upstream architecture, requirements, and database entities.
6. NO ARBITRARY SHELL EXECUTION:
   - Never generate shell scripts, deployment scripts, or executable system commands.
7. FORMAT:
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
