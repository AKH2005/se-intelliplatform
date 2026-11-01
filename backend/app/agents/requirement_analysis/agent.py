"""Requirement Analysis Agent Implementation."""

import logging
import uuid
from typing import Any, Optional
from pydantic import BaseModel

from app.agents.base import AbstractBaseAgent
from app.agents.contracts import (
    AgentMetadata,
    AgentType,
    ValidationResult,
)
from app.agents.exceptions import ProviderError, TransientProviderError
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

        model_name = kwargs.get("model") or getattr(provider, "default_model", settings.LLM_MODEL)
        request = LLMRequest(
            messages=[
                LLMMessage(role="system", content=SYSTEM_PROMPT),
                LLMMessage(role="user", content=user_prompt),
            ],
            model=model_name,
            temperature=kwargs.get("temperature", 0.0),
        )

        max_generate_attempts = kwargs.get(
            "max_generate_attempts",
            1 if getattr(provider, "provider_name", "") == "mock" else 2,
        )
        candidate_or_output = None
        for attempt in range(1, max_generate_attempts + 1):
            try:
                candidate_or_output = await provider.generate_structured(
                    request=request,
                    response_model=RequirementAnalysisCandidate,
                )
                break
            except TransientProviderError:
                raise
            except ProviderError as pe:
                if attempt < max_generate_attempts:
                    logger.warning(
                        f"RequirementAnalysisAgent structured output validation failed on attempt {attempt}/{max_generate_attempts}: {pe.detail}. "
                        "Retrying generation with controlled retry..."
                    )
                    continue
                logger.error(
                    f"RequirementAnalysisAgent structured output validation failed after {max_generate_attempts} attempts: {pe.detail}"
                )
                raise pe

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

        # 3. Sanitize requirement IDs against canonical context
        valid_active_ids = {req.id for req in context.requirements}
        uuid_str_map = {str(req.id): req.id for req in context.requirements}
        req_map = {str(idx): req.id for idx, req in enumerate(context.requirements, start=1)}
        fallback_req_id = next(iter(valid_active_ids)) if valid_active_ids else None

        def match_req_id(raw_val: Any) -> Optional[uuid.UUID]:
            if not raw_val:
                return fallback_req_id
            if isinstance(raw_val, uuid.UUID):
                return raw_val if raw_val in valid_active_ids else fallback_req_id
            raw_s = str(raw_val).strip()
            if raw_s in uuid_str_map:
                return uuid_str_map[raw_s]
            if raw_s in req_map:
                return req_map[raw_s]
            # Try fuzzy substring match if UUID was slightly prefixed/truncated by LLM
            for u_str, u_id in uuid_str_map.items():
                if u_str in raw_s or raw_s in u_str:
                    return u_id
            if fallback_req_id:
                return fallback_req_id
            try:
                return uuid.UUID(raw_s)
            except Exception:
                return uuid.uuid5(uuid.NAMESPACE_DNS, raw_s)

        # Sanitize ambiguities (only retain valid canonical references)
        raw_ambiguities = ai_data.get("ambiguities", [])
        sanitized_ambiguities = []
        for item in raw_ambiguities:
            d = item.model_dump() if isinstance(item, BaseModel) else dict(item) if isinstance(item, dict) else None
            if d:
                matched_id = match_req_id(d.get("requirement_id"))
                if matched_id in valid_active_ids:
                    d["requirement_id"] = matched_id
                    sanitized_ambiguities.append(d)

        # Sanitize conflicts (both distinct and active)
        raw_conflicts = ai_data.get("conflicts", [])
        sanitized_conflicts = []
        for item in raw_conflicts:
            d = item.model_dump() if isinstance(item, BaseModel) else dict(item) if isinstance(item, dict) else None
            if d:
                req_id = match_req_id(d.get("requirement_id"))
                rel_id = match_req_id(d.get("related_requirement_id"))
                if req_id and rel_id and req_id != rel_id and req_id in valid_active_ids and rel_id in valid_active_ids:
                    d["requirement_id"] = req_id
                    d["related_requirement_id"] = rel_id
                    sanitized_conflicts.append(d)

        # Sanitize refinements (only retain valid canonical references)
        raw_refinements = ai_data.get("refinements", [])
        sanitized_refinements = []
        for item in raw_refinements:
            d = item.model_dump() if isinstance(item, BaseModel) else dict(item) if isinstance(item, dict) else None
            if d:
                matched_id = match_req_id(d.get("requirement_id"))
                if matched_id in valid_active_ids:
                    d["requirement_id"] = matched_id
                    sanitized_refinements.append(d)

        # 4. Authoritatively inject Phase 2 deterministic metrics (LLM cannot spoof or own these)
        authoritative_completeness = context.statistics.completion_percentage
        authoritative_active = context.statistics.active_requirements
        authoritative_total = context.statistics.total_requirements

        final_output = RequirementAnalysisOutput(
            summary=ai_data.get("summary", "Requirement analysis complete."),
            ambiguities=sanitized_ambiguities,
            conflicts=sanitized_conflicts,
            missing_information=ai_data.get("missing_information", []),
            refinements=sanitized_refinements,
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
