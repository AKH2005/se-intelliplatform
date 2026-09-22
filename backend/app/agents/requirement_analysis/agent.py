"""Requirement Analysis Agent Implementation."""

import logging
from typing import Any
from pydantic import BaseModel

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
from app.agents.requirement_analysis.contracts import (
    RequirementAnalysisCandidate,
    RequirementAnalysisOutput,
)
from app.agents.requirement_analysis.prompts import (
    SYSTEM_PROMPT,
    build_analysis_prompt,
)
from app.agents.requirement_analysis.validation import (
    validate_requirement_analysis_output,
)
from app.schemas.context import ProjectContextResponse

logger = logging.getLogger(__name__)


class RequirementAnalysisAgent(AbstractBaseAgent[RequirementAnalysisOutput]):
    """AI Agent responsible for analyzing requirements in canonical Project Context.
    
    Identifies:
    - Ambiguities in requirement statements
    - Logical contradictions / conflicts between requirements
    - Missing engineering and architectural specifications
    - Constructive refinements and scope clarification questions
    
    Guarantees:
    - Strictly read-only: Never mutates or updates requirements in the database.
    - Deterministic metrics integrity: The LLM never calculates authoritative completion
      or count metrics; these are injected authoritatively from Phase 2 canonical context.
    - Single execution authority: Orchestrated exclusively through AgentExecutor.
    """

    @property
    def metadata(self) -> AgentMetadata:
        return AgentMetadata(
            agent_id="requirement-analysis",
            name="Requirement Analysis Agent",
            description="Analyzes canonical project requirements for ambiguity, conflicts, missing specifications, and refinements.",
            version="1.0.0",
            agent_type=AgentType.ANALYSIS,
        )

    @property
    def output_schema(self) -> type[RequirementAnalysisOutput]:
        return RequirementAnalysisOutput

    async def initialize(self) -> None:
        """Lifecycle Hook 1: Pre-execution initialization."""
        pass

    async def analyze(
        self,
        context: ProjectContextResponse,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Lifecycle Hook 2: Extract canonical requirements features for LLM prompt."""
        return {
            "project_id": str(context.project.id),
            "project_slug": context.project.slug,
            "project_name": context.project.name,
            "active_requirements_count": len(context.requirements),
            "context": context,
        }

    async def generate(
        self,
        analysis_result: dict[str, Any],
        provider: AbstractLLMProvider,
        **kwargs: Any,
    ) -> RequirementAnalysisOutput:
        """Lifecycle Hook 3: Invoke LLM to generate candidate qualitative findings,
        then authoritatively inject canonical Phase 2 deterministic metrics.
        """
        context: ProjectContextResponse = analysis_result["context"]
        user_prompt = build_analysis_prompt(context, analysis_result)

        from app.core.config import settings

        model_name = kwargs.get("model", settings.LLM_MODEL)
        request = LLMRequest(
            messages=[
                LLMMessage(role="system", content=SYSTEM_PROMPT),
                LLMMessage(role="user", content=user_prompt),
            ],
            model=model_name,
            temperature=kwargs.get("temperature", 0.0),
        )

        # 1. Request structured candidate from provider
        candidate_or_output = await provider.generate_structured(
            request=request,
            response_model=RequirementAnalysisCandidate,
        )

        # 2. Extract AI qualitative fields (handling candidate, output, or dict)
        if isinstance(candidate_or_output, RequirementAnalysisOutput):
            ai_data = candidate_or_output.model_dump(
                exclude={"completeness_score", "active_requirements_count", "total_requirements_count"}
            )
        elif isinstance(candidate_or_output, BaseModel):
            ai_data = candidate_or_output.model_dump()
        elif isinstance(candidate_or_output, dict):
            ai_data = {
                k: v for k, v in candidate_or_output.items()
                if k not in ("completeness_score", "active_requirements_count", "total_requirements_count")
            }
        else:
            ai_data = {}

        # 3. Authoritatively inject Phase 2 deterministic metrics (LLM cannot spoof or own these)
        authoritative_completeness = context.statistics.completion_percentage
        authoritative_active = context.statistics.active_requirements
        authoritative_total = context.statistics.total_requirements

        final_output = RequirementAnalysisOutput(
            summary=ai_data.get("summary", "Requirement analysis complete."),
            ambiguities=ai_data.get("ambiguities", []),
            conflicts=ai_data.get("conflicts", []),
            missing_information=ai_data.get("missing_information", []),
            refinements=ai_data.get("refinements", []),
            scope_clarifications=ai_data.get("scope_clarifications", []),
            completeness_score=authoritative_completeness,
            active_requirements_count=authoritative_active,
            total_requirements_count=authoritative_total,
        )

        return final_output

    def validate_output(
        self,
        output: RequirementAnalysisOutput,
        context: ProjectContextResponse,
    ) -> ValidationResult:
        """Lifecycle Hook 4: Deterministic domain validation hook."""
        return validate_requirement_analysis_output(output=output, context=context)
