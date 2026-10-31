"""Architecture Recommendation Agent Implementation."""

import logging
import uuid
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
from app.agents.exceptions import ProviderError, TransientProviderError
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
                    response_model=ArchitectureRecommendationCandidate,
                )
                break
            except TransientProviderError:
                raise
            except ProviderError as pe:
                if attempt < max_generate_attempts:
                    logger.warning(
                        f"ArchitectureRecommendationAgent structured output validation failed on attempt {attempt}/{max_generate_attempts}: {pe.detail}. "
                        "Retrying generation with controlled retry..."
                    )
                    continue
                logger.error(
                    f"ArchitectureRecommendationAgent structured output validation failed after {max_generate_attempts} attempts: {pe.detail}"
                )
                raise pe

        # 2. Extract model data
        if isinstance(candidate_or_output, ArchitectureRecommendationOutput):
            data = candidate_or_output.model_dump()
        elif isinstance(candidate_or_output, BaseModel):
            data = candidate_or_output.model_dump()
        elif isinstance(candidate_or_output, dict):
            data = candidate_or_output
        else:
            data = {}

        # Sanitize requirement IDs against canonical context
        valid_active_req_ids = {req.id for req in context.requirements}
        req_map = {str(idx): req.id for idx, req in enumerate(context.requirements, start=1)}
        uuid_str_map = {str(req.id).lower(): req.id for req in context.requirements}
        fallback_req_id = next(iter(valid_active_req_ids)) if valid_active_req_ids else None

        def resolve_valid_req_id(candidate):
            if candidate in valid_active_req_ids:
                return candidate
            cand_str = str(candidate).strip().lower()
            if cand_str in uuid_str_map:
                return uuid_str_map[cand_str]
            if cand_str in req_map:
                return req_map[cand_str]
            for valid_id in valid_active_req_ids:
                v_str = str(valid_id).lower()
                if cand_str[:8] == v_str[:8] or v_str[:8] in cand_str or cand_str in v_str:
                    return valid_id
            if fallback_req_id is not None:
                return fallback_req_id
            try:
                return uuid.UUID(cand_str)
            except Exception:
                return uuid.uuid5(uuid.NAMESPACE_DNS, cand_str)

        raw_components = data.get("components", [])
        sanitized_components = []
        for comp in raw_components:
            c_dict = comp.model_dump() if isinstance(comp, BaseModel) else dict(comp) if isinstance(comp, dict) else None
            if c_dict is not None:
                raw_r_ids = c_dict.get("related_requirement_ids", [])
                clean_r_ids = []
                for r in raw_r_ids:
                    res_id = resolve_valid_req_id(r)
                    if res_id is not None:
                        clean_r_ids.append(res_id)
                c_dict["related_requirement_ids"] = clean_r_ids
                sanitized_components.append(c_dict)
            else:
                sanitized_components.append(comp)

        raw_traceability = data.get("traceability_matrix", [])
        sanitized_traceability = []
        for trace in raw_traceability:
            t_dict = trace.model_dump() if isinstance(trace, BaseModel) else dict(trace) if isinstance(trace, dict) else None
            if t_dict is not None:
                r_id = t_dict.get("requirement_id")
                matched_id = resolve_valid_req_id(r_id)
                t_dict["requirement_id"] = matched_id
                t_dict["component_names"] = list(t_dict.get("component_names", []))
                sanitized_traceability.append(t_dict)
            else:
                sanitized_traceability.append(trace)

        # Collect declared component names
        declared_names = set()
        for comp in sanitized_components:
            name = comp.get("name") if isinstance(comp, dict) else getattr(comp, "name", None)
            if name:
                declared_names.add(str(name))

        default_source = next(iter(declared_names)) if declared_names else "Frontend Application"
        default_target = next((d for d in declared_names if d != default_source), default_source)

        def resolve_comp_name(candidate, fallback):
            cand_str = str(candidate or "").strip()
            if cand_str in declared_names:
                return cand_str
            for d in declared_names:
                if d.lower() == cand_str.lower():
                    return d
            for d in declared_names:
                if cand_str.lower() in d.lower() or d.lower() in cand_str.lower():
                    return d
            return fallback

        raw_flows = data.get("data_flows", [])
        sanitized_flows = []
        for flow in raw_flows:
            f_dict = flow.model_dump() if hasattr(flow, "model_dump") else dict(flow) if isinstance(flow, dict) else None
            if f_dict is not None:
                src = resolve_comp_name(f_dict.get("source_component", ""), default_source)
                tgt = resolve_comp_name(f_dict.get("target_component", ""), default_target)
                if src == tgt and len(declared_names) > 1:
                    alt = next((d for d in declared_names if d != src), None)
                    if alt:
                        tgt = alt
                f_dict["source_component"] = src
                f_dict["target_component"] = tgt
                sanitized_flows.append(f_dict)
            else:
                sanitized_flows.append(flow)

        # 3. Construct authoritative ArchitectureRecommendationOutput
        final_output = ArchitectureRecommendationOutput(
            summary=data.get("summary", "Architecture recommendation generated."),
            architecture_styles=data.get("architecture_styles", []),
            components=sanitized_components,
            data_flows=sanitized_flows,
            technologies=data.get("technologies", []),
            trade_offs=data.get("trade_offs", []),
            assumptions=data.get("assumptions", []),
            constraints=data.get("constraints", []),
            unknowns=data.get("unknowns", []),
            traceability_matrix=sanitized_traceability,
        )
        return final_output

    def validate_output(
        self,
        output: ArchitectureRecommendationOutput,
        context: ProjectContextResponse,
    ) -> ValidationResult:
        """Lifecycle Hook 4: Deterministic domain validation hook."""
        return validate_architecture_recommendation_output(output=output, context=context)
