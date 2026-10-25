"""Database Design Agent Implementation."""

import logging
import uuid
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
        model_name = kwargs.get("model") or getattr(provider, "default_model", settings.LLM_MODEL)

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

        # Sanitize requirement IDs against canonical context
        valid_active_req_ids = {req.id for req in context.requirements}
        req_map = {str(idx): req.id for idx, req in enumerate(context.requirements, start=1)}
        uuid_str_map = {str(req.id): req.id for req in context.requirements}
        fallback_req_id = next(iter(valid_active_req_ids)) if valid_active_req_ids else None

        raw_entities = data.get("entities", [])
        sanitized_entities = []
        for entity in raw_entities:
            e_dict = entity.model_dump() if isinstance(entity, BaseModel) else dict(entity) if isinstance(entity, dict) else None
            if e_dict is not None:
                raw_r_ids = e_dict.get("related_requirement_ids", [])
                clean_r_ids = []
                for r in raw_r_ids:
                    r_str = str(r).strip()
                    if r in valid_active_req_ids:
                        clean_r_ids.append(r)
                    elif r_str in uuid_str_map:
                        clean_r_ids.append(uuid_str_map[r_str])
                    elif r_str in req_map:
                        clean_r_ids.append(req_map[r_str])
                    else:
                        try:
                            clean_r_ids.append(uuid.UUID(r_str))
                        except Exception:
                            clean_r_ids.append(uuid.uuid5(uuid.NAMESPACE_DNS, r_str))
                e_dict["related_requirement_ids"] = clean_r_ids
                sanitized_entities.append(e_dict)
            else:
                sanitized_entities.append(entity)

        raw_relationships = data.get("relationships", [])
        sanitized_relationships = []
        for rel in raw_relationships:
            r_dict = rel.model_dump() if isinstance(rel, BaseModel) else dict(rel) if isinstance(rel, dict) else None
            if r_dict is not None:
                raw_r_ids = r_dict.get("related_requirement_ids", [])
                clean_r_ids = []
                for r in raw_r_ids:
                    r_str = str(r).strip()
                    if r in valid_active_req_ids:
                        clean_r_ids.append(r)
                    elif r_str in uuid_str_map:
                        clean_r_ids.append(uuid_str_map[r_str])
                    elif r_str in req_map:
                        clean_r_ids.append(req_map[r_str])
                    else:
                        try:
                            clean_r_ids.append(uuid.UUID(r_str))
                        except Exception:
                            clean_r_ids.append(uuid.uuid5(uuid.NAMESPACE_DNS, r_str))
                r_dict["related_requirement_ids"] = clean_r_ids
                sanitized_relationships.append(r_dict)
            else:
                sanitized_relationships.append(rel)

        raw_req_trace = data.get("requirement_traceability", [])
        sanitized_req_trace = []
        for trace in raw_req_trace:
            t_dict = trace.model_dump() if isinstance(trace, BaseModel) else dict(trace) if isinstance(trace, dict) else None
            if t_dict is not None:
                r_id = t_dict.get("requirement_id")
                r_str = str(r_id).strip()
                if r_id in valid_active_req_ids:
                    matched_id = r_id
                elif r_str in uuid_str_map:
                    matched_id = uuid_str_map[r_str]
                elif r_str in req_map:
                    matched_id = req_map[r_str]
                else:
                    try:
                        matched_id = uuid.UUID(r_str)
                    except Exception:
                        matched_id = uuid.uuid5(uuid.NAMESPACE_DNS, r_str)

                t_dict["requirement_id"] = matched_id
                t_dict["entity_names"] = list(t_dict.get("entity_names", []))
                sanitized_req_trace.append(t_dict)
            else:
                sanitized_req_trace.append(trace)

        # 3. Construct authoritative DatabaseDesignOutput
        final_output = DatabaseDesignOutput(
            summary=data.get("summary", "Logical database design proposed."),
            database_paradigm=data.get("database_paradigm", DatabaseParadigm.RELATIONAL),
            entities=sanitized_entities,
            relationships=sanitized_relationships,
            indexes=data.get("indexes", []),
            constraints=data.get("constraints", []),
            trade_offs=data.get("trade_offs", []),
            assumptions=data.get("assumptions", []),
            constraints_notes=data.get("constraints_notes", []),
            unknowns=data.get("unknowns", []),
            requirement_traceability=sanitized_req_trace,
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
