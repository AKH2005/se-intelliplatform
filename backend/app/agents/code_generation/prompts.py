"""System and User Prompts for Code Generation Planning and Code Generation Agents."""

from typing import Any
from app.agents.architecture_recommendation.contracts import ArchitectureRecommendationOutput
from app.agents.code_generation.contracts import CodeGenerationPlan, is_fullstack_project
from app.agents.code_generation.specification import extract_application_specification
from app.agents.database_design.contracts import DatabaseDesignOutput
from app.agents.requirement_analysis.contracts import RequirementAnalysisOutput
from app.schemas.context import ProjectContextResponse


# ==============================================================================
# 1. Code Generation Planning Prompts
# ==============================================================================

PLANNING_SYSTEM_PROMPT = """You are the Senior Software Architect and Code Generation Planner for SE IntelliPlatform.
Your role is to propose a robust, modular, domain-tailored project scaffold plan for a production web application.

APPLICATION COMPLEXITY TARGETS:
1. Level 1: Basic (Utility apps, simple single-view calculators, basic portfolios).
2. Level 2: Medium (PRIMARY TARGET: E-commerce, Inventory Management, Learning Management System, Event Management, Full-Featured Games, Task Platforms).
   - Complete connected multi-page workflows.
   - Genuine database entity models and persistence.
   - Domain-tailored UI/UX design systems.
   - Input validation and proper error handling.
3. Level 3: Advanced (Enterprise distributed systems, real-time multiplayer).
   - Explicit scope assessments and feature boundaries.

SUPPORTED TARGET STACKS:
1. Backend Service (when no web UI or frontend is requested):
   - Language: python | Framework: fastapi | Database: postgresql/sqlite | Package Manager: pip
   - Files: app/main.py, app/config.py, app/models.py, app/api.py, app/persistence.py, requirements.txt, README.md
2. Full-Stack Application (when React, web interface, frontend, dashboard, or game is requested):
   - Language: polyglot | Framework: react+fastapi | Package Manager: npm+pip
   - Frontend files:
     - `frontend/package.json`: Dependencies for Vite, React, TypeScript, and Lucide icons.
     - `frontend/index.html`: Web entry HTML with domain-specific title and mounting container.
     - `frontend/src/main.tsx`: React mounting entrypoint.
     - `frontend/src/App.tsx`: Main React application coordinating navigation and views.
     - Domain feature components tailored to the application's actual workflows (e.g. Catalog, Cart, Checkout, CoursePlayer, InventoryTable, BookingModal).
     - `frontend/src/services/api.ts`: API client connecting to FastAPI backend with env URL fallback.
     - `frontend/src/styles/App.css`: Professional domain design system styling.
   - Backend files:
     - `backend/requirements.txt`: Python package dependencies (fastapi, uvicorn, pydantic).
     - `backend/app/main.py`: FastAPI application entrypoint with CORS middleware and preview serving.
     - `backend/app/config.py`: Environment configuration and allowed origins.
     - `backend/app/models.py`: Database models and Pydantic schemas reflecting domain entities.
     - `backend/app/api.py`: REST endpoint router handling domain operations.
     - `backend/app/persistence.py`: Thread-safe database persistence repository.
   - Root documentation:
     - `README.md`: Architecture overview and setup guides for frontend and backend.

ARCHITECTURAL PRINCIPLES:
1. Domain Tailoring: Propose components and routes that directly address the specific domain (Hospital, E-commerce, Inventory, LMS, EventHub, or Game). Never force unrelated applications into a generic task manager or placeholder dashboard.
2. Full-Stack Invariant: If the project requires a frontend, propose the complete full-stack structure with both frontend/ and backend/ directories.
3. Path Safety: Every file path MUST be relative, using forward slashes (e.g., 'frontend/src/App.tsx', 'backend/app/main.py'). NEVER use absolute paths, Windows drive letters, or '..' path traversals.
4. Traceability: Map each file's `requirement_ids` to canonical requirements and `architecture_component` to declared components.
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

    # Extract internal application specification
    app_spec = extract_application_specification(
        name=project.name,
        desc=project.description or "",
        requirements=requirements,
    )

    # Requirements block
    req_lines = [
        f"Requirement ID: {r.id} | Title: {r.title} | Priority: {r.priority.value}\n    Description: {r.description.strip()}"
        for r in requirements
    ]
    req_block = "\n".join(req_lines) if req_lines else "None recorded."

    # Domain workflows block
    wf_lines = [
        f"Workflow '{wf.workflow_name}': {' -> '.join(wf.steps)} (Data: {wf.data_flow})"
        for wf in app_spec.user_workflows
    ]
    wf_block = "\n".join(wf_lines) if wf_lines else "Standard domain navigation."

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
        pages_summary = ", ".join(p.title for p in app_spec.pages_and_navigation)
        plan_instruction = (
            f"The project requires a FULL-STACK {app_spec.complexity_level.value} application (React frontend + FastAPI backend).\n"
            f"Target Domain Purpose: {app_spec.purpose}\n"
            f"Domain Workflows:\n{wf_block}\n"
            f"Target Views/Pages: {pages_summary}\n"
            "Propose tailored domain components (NOT generic task cards unless task management was explicitly requested).\n"
            "Set project_type='fullstack', language='polyglot', framework='react+fastapi', package_manager='npm+pip', "
            f"complexity_level='{app_spec.complexity_level.value}'."
        )
    else:
        plan_instruction = (
            f"The project requires a backend service (Python/FastAPI) of complexity {app_spec.complexity_level.value}.\n"
            "Generate a CodeGenerationPlan proposing a production-ready Python/FastAPI project scaffold.\n"
            f"Set project_type='backend-service', language='python', framework='fastapi', package_manager='pip', complexity_level='{app_spec.complexity_level.value}'."
        )

    return f"""Project: {project.name} (slug: {project.slug})
Description: {project.description or 'None provided'}
Target Complexity Level: {app_spec.complexity_level.value}

--- APPLICATION SPECIFICATION & WORKFLOWS ---
Purpose: {app_spec.purpose}
Workflows:
{wf_block}
--- END APPLICATION SPECIFICATION ---

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
    requirements = context.requirements

    app_spec = extract_application_specification(
        name=project.name,
        desc=project.description or "",
        requirements=requirements,
    )

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

    workflow_summary = "\n".join(
        f"- {wf.workflow_name}: {' -> '.join(wf.steps)}" for wf in app_spec.user_workflows
    ) or "Standard domain flow."

    return f"""Project: {project.name}
Target Complexity: {getattr(plan, 'complexity_level', 'MEDIUM')}
Domain Purpose: {app_spec.purpose}
Target Stack: {plan.language} / {plan.framework} / {plan.database} ({plan.package_manager})
Plan Rationale: {plan.rationale}
Database Context: {db_summary}

--- DOMAIN WORKFLOWS ---
{workflow_summary}
--- END WORKFLOWS ---

--- AUTHORITATIVE FILE MANIFEST ({len(plan.files)} files planned) ---
{manifest_block}
--- END MANIFEST ---

Generate complete, clean, professional source code for all {len(plan.files)} planned files listed above.
Do not omit any planned file. Do not invent unplanned files.
Implement actual interactive domain components and working endpoints, not generic task list placeholders.
Do not include any secrets, passwords, or API keys."""
