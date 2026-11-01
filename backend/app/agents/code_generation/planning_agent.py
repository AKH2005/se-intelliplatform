"""Code Generation Planning Agent.

Proposes a typed, deterministic project scaffold plan and file manifest based on
canonical project context and upstream software design artifacts.
"""

import logging
from typing import Any
from pydantic import BaseModel

from app.agents.architecture_recommendation.contracts import ArchitectureRecommendationOutput
from app.agents.base import AbstractBaseAgent
from app.agents.code_generation.archetypes import (
    detect_project_archetype,
    get_archetype_planned_files,
)
from app.agents.code_generation.contracts import (
    CodeGenerationPlan,
    CodeGenerationPlanCandidate,
    FileType,
    PlannedFile,
    PlannedFileCandidate,
    is_fullstack_project,
)
from app.agents.code_generation.prompts import (
    PLANNING_SYSTEM_PROMPT,
    build_code_generation_plan_prompt,
)
from app.agents.code_generation.validation import validate_code_generation_plan
from app.agents.contracts import AgentMetadata, AgentType, ValidationResult
from app.agents.database_design.contracts import DatabaseDesignOutput
from app.agents.providers.base import (
    AbstractLLMProvider,
    LLMMessage,
    LLMRequest,
)
from app.agents.requirement_analysis.contracts import RequirementAnalysisOutput
from app.core.config import settings
from app.schemas.context import ProjectContextResponse

logger = logging.getLogger(__name__)


class CodeGenerationPlanningAgent(AbstractBaseAgent[CodeGenerationPlan]):
    """AI Agent responsible for proposing structured project scaffold plans and file manifests.

    Consumes:
    - Canonical ProjectContextResponse (required)
    - Optional validated RequirementAnalysisOutput
    - Optional validated ArchitectureRecommendationOutput
    - Optional validated DatabaseDesignOutput

    Guarantees:
    - Never touches filesystem or executes code.
    - Single Execution Authority: Orchestrated exclusively via AgentExecutor.
    - Strict Traceability: Maps planned files to requirements and architecture components.
    """

    def __init__(self) -> None:
        self._current_architecture_recommendation: ArchitectureRecommendationOutput | None = None

    @property
    def metadata(self) -> AgentMetadata:
        return AgentMetadata(
            agent_id="code-generation-planning",
            name="Code Generation Planning Agent",
            description="Analyzes design outputs to propose a deterministic project scaffold plan and file manifest.",
            version="1.0.0",
            agent_type=AgentType.GENERATION,
        )

    @property
    def output_schema(self) -> type[CodeGenerationPlan]:
        return CodeGenerationPlan

    @property
    def supported_models(self) -> list[str]:
        return [
            settings.LLM_MODEL,
            settings.LLM_MODEL_FAST,
            settings.LLM_MODEL_GROQ,
            settings.LLM_MODEL_GEMINI,
            "mock-model",
        ]

    async def analyze(
        self,
        context: ProjectContextResponse,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Lifecycle Hook 2: Ingest context and upstream design artifacts."""
        req_analysis: RequirementAnalysisOutput | None = kwargs.get("requirement_analysis")
        arch_rec: ArchitectureRecommendationOutput | None = kwargs.get("architecture_recommendation")
        db_design: DatabaseDesignOutput | None = kwargs.get("database_design")

        self._current_architecture_recommendation = arch_rec

        return {
            "context": context,
            "requirement_analysis": req_analysis,
            "architecture_recommendation": arch_rec,
            "database_design": db_design,
            "project_name": context.project.name,
            "requirements_count": len(context.requirements),
        }

    async def generate(
        self,
        analysis_result: dict[str, Any],
        provider: AbstractLLMProvider,
        **kwargs: Any,
    ) -> CodeGenerationPlan:
        """Lifecycle Hook 3: Invoke LLM to generate candidate scaffold plan."""
        context: ProjectContextResponse = analysis_result["context"]
        req_analysis: RequirementAnalysisOutput | None = analysis_result.get("requirement_analysis")
        arch_rec: ArchitectureRecommendationOutput | None = analysis_result.get("architecture_recommendation")
        db_design: DatabaseDesignOutput | None = analysis_result.get("database_design")

        user_prompt = build_code_generation_plan_prompt(
            context=context,
            requirement_analysis=req_analysis,
            architecture_recommendation=arch_rec,
            database_design=db_design,
        )
        model_name = kwargs.get("model") or getattr(provider, "default_model", settings.LLM_MODEL)

        request = LLMRequest(
            messages=[
                LLMMessage(role="system", content=PLANNING_SYSTEM_PROMPT),
                LLMMessage(role="user", content=user_prompt),
            ],
            model=model_name,
            temperature=kwargs.get("temperature", 0.0),
            max_tokens=kwargs.get("max_tokens", 2500),
        )

        candidate_or_output = await provider.generate_structured(
            request=request,
            response_model=CodeGenerationPlanCandidate,
        )

        if isinstance(candidate_or_output, CodeGenerationPlan):
            data = candidate_or_output.model_dump()
        elif isinstance(candidate_or_output, BaseModel):
            data = candidate_or_output.model_dump()
        elif isinstance(candidate_or_output, dict):
            data = candidate_or_output
        else:
            data = {}

        fullstack = is_fullstack_project(context, arch_rec)

        # Fallback plan for mock execution if empty or if fullstack required but missing frontend
        raw_files = data.get("files")
        if not raw_files:
            raw_files = self._build_mock_files(context, arch_rec)
        elif fullstack:
            has_frontend = any(
                ("frontend/" in (f.path if isinstance(f, (PlannedFile, PlannedFileCandidate)) else (f.get("path") or f.get("file_path", ""))))
                or ("package.json" in (f.path if isinstance(f, (PlannedFile, PlannedFileCandidate)) else (f.get("path") or f.get("file_path", ""))))
                for f in raw_files
            )
            has_backend = any(
                any((f.path if isinstance(f, (PlannedFile, PlannedFileCandidate)) else (f.get("path") or f.get("file_path", ""))).lower().endswith(ext) for ext in ["main.py", "requirements.txt", "api.py"])
                for f in raw_files
            )
            if not has_frontend or not has_backend:
                logger.info("Candidate plan lacked required frontend or backend files for fullstack project; using complete fullstack scaffold.")
                raw_files = self._build_mock_files(context, arch_rec)

        # Extract declared architecture components from upstream recommendation
        declared_components: set[str] = set()
        if arch_rec is not None:
            if isinstance(arch_rec, dict):
                components_list = arch_rec.get("components", [])
                declared_components = {
                    c.get("name") if isinstance(c, dict) else getattr(c, "name", "")
                    for c in components_list
                }
            elif hasattr(arch_rec, "components") and arch_rec.components:
                declared_components = {c.name for c in arch_rec.components if hasattr(c, "name")}
        declared_components = {c.strip() for c in declared_components if c and c.strip()}
        declared_lower_map = {c.lower(): c for c in declared_components}

        be_comp = next((declared_lower_map[k] for k in declared_lower_map if any(sub in k for sub in ["core", "api", "backend", "service", "server", "data", "app"])), next(iter(declared_components), None))
        fe_comp = next((declared_lower_map[k] for k in declared_lower_map if any(sub in k for sub in ["front", "ui", "web", "client", "react"])), be_comp)

        planned_files: list[PlannedFile] = []
        for f in raw_files:
            if isinstance(f, PlannedFile):
                planned_files.append(f)
            elif isinstance(f, (PlannedFileCandidate, dict)):
                path = f.path if isinstance(f, PlannedFileCandidate) else (f.get("path") or f.get("file_path", ""))
                purpose = f.purpose if isinstance(f, PlannedFileCandidate) else (f.get("purpose") or f.get("description", "File implementation"))
                ft_val = f.file_type if isinstance(f, PlannedFileCandidate) else f.get("file_type", FileType.SOURCE.value)
                try:
                    ft_enum = FileType(ft_val)
                except ValueError:
                    ft_enum = FileType.SOURCE
                arch_comp = f.architecture_component if isinstance(f, PlannedFileCandidate) else f.get("architecture_component")
                raw_reqs = f.requirement_ids if isinstance(f, PlannedFileCandidate) else f.get("requirement_ids", [])
                canonical_uuids = {str(r.id) for r in context.requirements}
                req_map = {str(idx): str(r.id) for idx, r in enumerate(context.requirements, start=1)}
                reqs = []
                for r_id in raw_reqs:
                    r_str = str(r_id).strip()
                    if r_str in canonical_uuids:
                        reqs.append(r_str)
                    elif r_str in req_map:
                        reqs.append(req_map[r_str])
                deps = f.dependencies if isinstance(f, PlannedFileCandidate) else f.get("dependencies", [])

                # Normalize architecture component traceability against declared components
                if arch_comp:
                    arch_comp_clean = str(arch_comp).strip()
                    arch_comp_lower = arch_comp_clean.lower()
                    if arch_comp_lower in declared_lower_map:
                        arch_comp = declared_lower_map[arch_comp_lower]
                    elif arch_comp_lower in ("documentation", "docs", "doc", "root", "readme", "config", "dependencies"):
                        if path.lower().startswith("readme") or ft_enum == FileType.DOCUMENTATION:
                            arch_comp = declared_lower_map.get("documentation", None)
                        elif path.lower().startswith("frontend/") or path in ("package.json", "tsconfig.json", "vite.config.ts"):
                            arch_comp = fe_comp
                        else:
                            arch_comp = be_comp
                    elif arch_comp_clean not in declared_components:
                        if path.lower().startswith("frontend/") and fe_comp:
                            arch_comp = fe_comp
                        elif (path.lower().startswith("backend/") or "requirements.txt" in path.lower()) and be_comp:
                            arch_comp = be_comp
                else:
                    if path.lower().startswith("frontend/") and fe_comp:
                        arch_comp = fe_comp
                    elif (path.lower().startswith("backend/") or "requirements.txt" in path.lower()) and be_comp:
                        arch_comp = be_comp

                if path:
                    planned_files.append(
                        PlannedFile(
                            path=path,
                            purpose=purpose if len(purpose) >= 5 else f"Implementation for {path}",
                            file_type=ft_enum,
                            architecture_component=arch_comp,
                            requirement_ids=reqs,
                            dependencies=deps,
                        )
                    )

        default_ptype = "fullstack" if fullstack else "backend-service"
        default_lang = "polyglot" if fullstack else "python"
        default_fw = "react+fastapi" if fullstack else "fastapi"
        default_pkg = "npm+pip" if fullstack else "pip"
        default_rat = (
            "Proposed Full-Stack (React + FastAPI) scaffold matching requirements and architecture."
            if fullstack
            else "Proposed FastAPI scaffold matching upstream architecture."
        )

        final_ptype = default_ptype if fullstack else (data.get("project_type") or default_ptype)
        final_lang = default_lang if fullstack else (data.get("language") or default_lang)
        final_fw = default_fw if fullstack else (data.get("framework") or default_fw)
        final_pkg = default_pkg if fullstack else (data.get("package_manager") or default_pkg)

        return CodeGenerationPlan(
            project_type=final_ptype,
            language=final_lang,
            framework=final_fw,
            database=data.get("database", "postgresql"),
            package_manager=final_pkg,
            files=planned_files,
            rationale=data.get("rationale") or default_rat,
        )

    def validate_output(
        self,
        output: CodeGenerationPlan,
        context: ProjectContextResponse,
    ) -> ValidationResult:
        """Lifecycle Hook 4: Deterministic validation of proposed plan."""
        return validate_code_generation_plan(
            plan=output,
            context=context,
            architecture_recommendation=self._current_architecture_recommendation,
        )

    def _build_mock_files(
        self,
        context: ProjectContextResponse,
        arch_rec: ArchitectureRecommendationOutput | None = None,
    ) -> list[dict[str, Any]]:
        fullstack = is_fullstack_project(context, arch_rec)
        req_ids = [str(r.id) for r in context.requirements[:4]] if context.requirements else []
        ui_req_ids = [str(r.id) for r in context.requirements if any(k in f"{r.title} {r.description}".lower() for k in ["web", "interface", "dashboard", "react", "view", "task"])]
        if not ui_req_ids:
            ui_req_ids = req_ids

        comp_name = None
        fe_comp_name = None
        if arch_rec:
            if isinstance(arch_rec, dict):
                comps = arch_rec.get("components") or []
                for c in comps:
                    name = c.get("name") if isinstance(c, dict) else getattr(c, "name", "")
                    if any(k in name.lower() for k in ["react", "frontend", "ui", "client"]):
                        fe_comp_name = name
                    elif not comp_name:
                        comp_name = name
            elif hasattr(arch_rec, "components") and arch_rec.components:
                for c in arch_rec.components:
                    name = c.name if hasattr(c, "name") else (c.get("name") if isinstance(c, dict) else "")
                    if any(k in name.lower() for k in ["react", "frontend", "ui", "client"]):
                        fe_comp_name = name
                    elif not comp_name:
                        comp_name = name

        if not comp_name:
            comp_name = f"{context.project.name} Core Service" if context.project.name else "Core Backend Service"
        if not fe_comp_name:
            fe_comp_name = f"{context.project.name} UI" if context.project.name else "Frontend UI"

        if fullstack:
            archetype = detect_project_archetype(
                name=context.project.name,
                desc=context.project.description or "",
                slug=context.project.slug or "",
            )
            return get_archetype_planned_files(
                archetype=archetype,
                fe_comp_name=fe_comp_name,
                be_comp_name=comp_name,
                req_ids=req_ids,
                ui_req_ids=ui_req_ids,
            )

        # Backend-only fallback
        return [
            {
                "path": "app/main.py",
                "purpose": "FastAPI application entrypoint and route configuration",
                "file_type": "SOURCE",
                "architecture_component": comp_name,
                "requirement_ids": req_ids,
                "dependencies": ["app/config.py"],
            },
            {
                "path": "app/config.py",
                "purpose": "Application environment settings and configuration",
                "file_type": "CONFIG",
                "architecture_component": comp_name,
                "requirement_ids": req_ids,
                "dependencies": [],
            },
            {
                "path": "app/models.py",
                "purpose": "Domain data schemas and entity models",
                "file_type": "SCHEMA",
                "architecture_component": comp_name,
                "requirement_ids": req_ids,
                "dependencies": [],
            },
            {
                "path": "requirements.txt",
                "purpose": "Project dependency specification",
                "file_type": "DEPENDENCY",
                "architecture_component": None,
                "requirement_ids": [],
                "dependencies": [],
            },
            {
                "path": "README.md",
                "purpose": "Project documentation and setup guide",
                "file_type": "DOCUMENTATION",
                "architecture_component": None,
                "requirement_ids": [],
                "dependencies": [],
            },
        ]
