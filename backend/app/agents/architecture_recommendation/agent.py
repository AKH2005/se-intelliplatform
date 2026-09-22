"""Architecture Recommendation Agent Implementation."""

import logging
from typing import Any
from pydantic import BaseModel

from app.agents.architecture_recommendation.contracts import (
    ArchitectureRecommendationCandidate,
    ArchitectureRecommendationOutput,
)
from app.agents.architecture_recommendation.prompts import (
    SYSTEM_PROMPT,
    build_architecture_prompt,
)
from app.agents.architecture_recommendation.validation import (
    validate_architecture_recommendation_output,
)
from app.agents.base import AbstractBaseAgent
from app.agents.contracts import (
    AgentMetadata,
    AgentType,
    ValidationResult,
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


class ArchitectureRecommendationAgent(AbstractBaseAgent[ArchitectureRecommendationOutput]):
    """AI Agent responsible for proposing modular, sustainable software architectures.
    
    Consumes:
    - Canonical Phase 2 ProjectContextResponse
    - Optional validated Phase 4 RequirementAnalysisOutput (injected as an input dependency, never executed internally)
    
    Guarantees:
    - Read-Only / Advisory Guarantee: Never mutates project requirements, commits code, or deploys architecture.
    - Zero Pseudo-Quality Scoring: Does not invent arbitrary numerical architecture ratings.
    - Strict Traceability: Components and traces reference real canonical requirement UUIDs.
    - Single Execution Authority: Orchestrated exclusively via AgentExecutor.
    """

    @property
    def metadata(self) -> AgentMetadata:
        return AgentMetadata(
            agent_id="architecture-recommendation",
            name="Architecture Recommendation Agent",
            description="Analyzes canonical requirements and requirement analysis findings to recommend structured software architectures.",
            version="1.0.0",
            agent_type=AgentType.RECOMMENDATION,
        )

    @property
    def output_schema(self) -> type[ArchitectureRecommendationOutput]:
        return ArchitectureRecommendationOutput

    async def initialize(self) -> None:
        """Lifecycle Hook 1: Pre-execution initialization."""
        pass

    async def analyze(
        self,
        context: ProjectContextResponse,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Lifecycle Hook 2: Extract project features and optional injected Phase 4 findings.
        
        CRITICAL ARCHITECTURAL BOUNDARY:
        This method consumes `requirement_analysis` if provided by the caller.
        It NEVER internally instantiates or executes RequirementAnalysisAgent.
        """
        requirement_analysis: RequirementAnalysisOutput | None = kwargs.get("requirement_analysis")

        return {
            "context": context,
            "requirement_analysis": requirement_analysis,
            "project_id": str(context.project.id),
            "project_name": context.project.name,
            "active_requirements_count": len(context.requirements),
        }

    async def generate(
        self,
        analysis_result: dict[str, Any],
        provider: AbstractLLMProvider,
        **kwargs: Any,
    ) -> ArchitectureRecommendationOutput:
        """Lifecycle Hook 3: Invoke LLM to generate candidate architecture recommendation."""
        context: ProjectContextResponse = analysis_result["context"]
        requirement_analysis: RequirementAnalysisOutput | None = analysis_result.get("requirement_analysis")

        user_prompt = build_architecture_prompt(context, requirement_analysis)
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
            response_model=ArchitectureRecommendationCandidate,
        )

        # 2. Extract model data
        if isinstance(candidate_or_output, ArchitectureRecommendationOutput):
            data = candidate_or_output.model_dump()
        elif isinstance(candidate_or_output, BaseModel):
            data = candidate_or_output.model_dump()
        elif isinstance(candidate_or_output, dict):
            data = candidate_or_output
        else:
            data = {}

        # 3. Construct authoritative ArchitectureRecommendationOutput
        final_output = ArchitectureRecommendationOutput(
            summary=data.get("summary", "Architecture recommendation generated."),
            architecture_styles=data.get("architecture_styles", []),
            components=data.get("components", []),
            data_flows=data.get("data_flows", []),
            technologies=data.get("technologies", []),
            trade_offs=data.get("trade_offs", []),
            assumptions=data.get("assumptions", []),
            constraints=data.get("constraints", []),
            unknowns=data.get("unknowns", []),
            traceability_matrix=data.get("traceability_matrix", []),
        )
        return final_output

    def validate_output(
        self,
        output: ArchitectureRecommendationOutput,
        context: ProjectContextResponse,
    ) -> ValidationResult:
        """Lifecycle Hook 4: Deterministic domain validation hook."""
        return validate_architecture_recommendation_output(output=output, context=context)
