"""Code Generation Planning Agent.

Proposes a typed, deterministic project scaffold plan and file manifest based on
canonical project context and upstream software design artifacts.
"""

import logging
from typing import Any
from pydantic import BaseModel

from app.agents.architecture_recommendation.contracts import ArchitectureRecommendationOutput
from app.agents.base import AbstractBaseAgent
from app.agents.code_generation.contracts import (
    CodeGenerationPlan,
    CodeGenerationPlanCandidate,
    FileType,
    PlannedFile,
    PlannedFileCandidate,
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

        # Fallback plan for mock execution if empty
        raw_files = data.get("files")
        if not raw_files:
            raw_files = self._build_mock_files(context, arch_rec)

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

        return CodeGenerationPlan(
            project_type=data.get("project_type", "backend-service"),
            language=data.get("language", "python"),
            framework=data.get("framework", "fastapi"),
            database=data.get("database", "postgresql"),
            package_manager=data.get("package_manager", "pip"),
            files=planned_files,
            rationale=data.get("rationale", "Proposed FastAPI scaffold matching upstream architecture."),
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
        req_ids = [str(r.id) for r in context.requirements[:2]]
        comp_name = None
        if arch_rec:
            if isinstance(arch_rec, dict):
                comps = arch_rec.get("components") or []
                if comps and isinstance(comps[0], dict):
                    comp_name = comps[0].get("name")
                elif comps and hasattr(comps[0], "name"):
                    comp_name = comps[0].name
            elif hasattr(arch_rec, "components") and arch_rec.components:
                first = arch_rec.components[0]
                comp_name = first.name if hasattr(first, "name") else (first.get("name") if isinstance(first, dict) else None)

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
