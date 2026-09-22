"""Database Design Agent Implementation."""

import logging
from typing import Any
from pydantic import BaseModel

from app.agents.architecture_recommendation.contracts import ArchitectureRecommendationOutput
from app.agents.base import AbstractBaseAgent
from app.agents.contracts import (
    AgentMetadata,
    AgentType,
    ValidationResult,
)
from app.agents.database_design.contracts import (
    DatabaseDesignCandidate,
    DatabaseDesignOutput,
    DatabaseParadigm,
)
from app.agents.database_design.prompts import (
    SYSTEM_PROMPT,
    build_database_design_prompt,
)
from app.agents.database_design.validation import (
    validate_database_design_output,
)
from app.agents.providers.base import (
    AbstractLLMProvider,
    LLMMessage,
    LLMRequest,
)
from app.agents.requirement_analysis.contracts import RequirementAnalysisOutput
from app.core.config import settings
from app.schemas.context import ProjectContextResponse

logger = logging.getLogger(__name__)


class DatabaseDesignAgent(AbstractBaseAgent[DatabaseDesignOutput]):
    """AI Agent responsible for proposing modular, sustainable logical database designs.
    
    Consumes:
    - Canonical Phase 2 ProjectContextResponse (required)
    - Optional validated Phase 4 RequirementAnalysisOutput (injected as input dependency)
    - Optional validated Phase 5 ArchitectureRecommendationOutput (injected as input dependency)
    
    Guarantees:
    - Read-Only / Advisory Guarantee: Never creates database tables, executes DDL, or generates Alembic migrations.
    - Single Execution Authority: Orchestrated exclusively via AgentExecutor; never invokes upstream agents internally.
    - Zero Pseudo-Quality Scoring: Does not invent arbitrary numerical database quality scores.
    - Strict Traceability: Entities, primary keys, relationships, indexes, and constraints are deterministically validated.
    """

    def __init__(self) -> None:
        self._current_architecture_recommendation: ArchitectureRecommendationOutput | None = None

    @property
    def metadata(self) -> AgentMetadata:
        return AgentMetadata(
            agent_id="database-design",
            name="Database Design Agent",
            description="Analyzes canonical requirements, requirement analysis, and architecture recommendations to propose structured database designs.",
            version="1.0.0",
            agent_type=AgentType.RECOMMENDATION,
        )

    @property
    def output_schema(self) -> type[DatabaseDesignOutput]:
        return DatabaseDesignOutput

    async def initialize(self) -> None:
        """Lifecycle Hook 1: Pre-execution initialization."""
        self._current_architecture_recommendation = None

    async def analyze(
        self,
        context: ProjectContextResponse,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Lifecycle Hook 2: Extract project features and optional injected Phase 4 & Phase 5 findings.
        
        CRITICAL ARCHITECTURAL BOUNDARY:
        This method consumes `requirement_analysis` and `architecture_recommendation` if provided.
        It NEVER internally instantiates or executes upstream agents.
        """
        requirement_analysis: RequirementAnalysisOutput | None = kwargs.get("requirement_analysis")
        architecture_recommendation: ArchitectureRecommendationOutput | None = kwargs.get(
            "architecture_recommendation"
        )
        self._current_architecture_recommendation = architecture_recommendation

        return {
            "context": context,
            "requirement_analysis": requirement_analysis,
            "architecture_recommendation": architecture_recommendation,
            "project_id": str(context.project.id),
            "project_name": context.project.name,
            "active_requirements_count": len(context.requirements),
        }

    async def generate(
        self,
        analysis_result: dict[str, Any],
        provider: AbstractLLMProvider,
        **kwargs: Any,
    ) -> DatabaseDesignOutput:
        """Lifecycle Hook 3: Invoke LLM to generate candidate database design proposal."""
        context: ProjectContextResponse = analysis_result["context"]
        requirement_analysis: RequirementAnalysisOutput | None = analysis_result.get("requirement_analysis")
        architecture_recommendation: ArchitectureRecommendationOutput | None = analysis_result.get(
            "architecture_recommendation"
        )

        user_prompt = build_database_design_prompt(
            context=context,
            requirement_analysis=requirement_analysis,
            architecture_recommendation=architecture_recommendation,
        )
        model_name = kwargs.get("model", settings.LLM_MODEL)

        request = LLMRequest(
            messages=[
                LLMMessage(role="system", content=SYSTEM_PROMPT),
                LLMMessage(role="user", content=user_prompt),
            ],
            model=model_name,
            temperature=kwargs.get("temperature", 0.0),
        )

        # 1. Generate structured candidate from provider
        candidate_or_output = await provider.generate_structured(
            request=request,
            response_model=DatabaseDesignCandidate,
        )

        # 2. Extract model data
        if isinstance(candidate_or_output, DatabaseDesignOutput):
            data = candidate_or_output.model_dump()
        elif isinstance(candidate_or_output, BaseModel):
            data = candidate_or_output.model_dump()
        elif isinstance(candidate_or_output, dict):
            data = candidate_or_output
        else:
            data = {}

        # 3. Construct authoritative DatabaseDesignOutput
        final_output = DatabaseDesignOutput(
            summary=data.get("summary", "Logical database design proposed."),
            database_paradigm=data.get("database_paradigm", DatabaseParadigm.RELATIONAL),
            entities=data.get("entities", []),
            relationships=data.get("relationships", []),
            indexes=data.get("indexes", []),
            constraints=data.get("constraints", []),
            trade_offs=data.get("trade_offs", []),
            assumptions=data.get("assumptions", []),
            constraints_notes=data.get("constraints_notes", []),
            unknowns=data.get("unknowns", []),
            requirement_traceability=data.get("requirement_traceability", []),
            architecture_traceability=data.get("architecture_traceability", []),
        )
        return final_output

    def validate_output(
        self,
        output: DatabaseDesignOutput,
        context: ProjectContextResponse,
    ) -> ValidationResult:
        """Lifecycle Hook 4: Deterministic domain validation hook."""
        return validate_database_design_output(
            output=output,
            context=context,
            architecture_recommendation=self._current_architecture_recommendation,
        )
