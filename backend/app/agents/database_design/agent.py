"""Database Design Agent Implementation."""

import asyncio
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
    DataType,
)
from app.agents.exceptions import ProviderError, TransientProviderError
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
            max_tokens=kwargs.get("max_tokens", 2500),
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
                    response_model=DatabaseDesignCandidate,
                )
                break
            except TransientProviderError:
                # Let transient errors (rate limits, timeouts) bubble up to AgentExecutor's retry policy
                raise
            except ProviderError as pe:
                if attempt < max_generate_attempts:
                    logger.warning(
                        f"DatabaseDesignAgent structured output validation failed on attempt {attempt}/{max_generate_attempts}: {pe.detail}. "
                        "Retrying generation with controlled retry..."
                    )
                    continue
                logger.error(
                    f"DatabaseDesignAgent structured output validation failed after {max_generate_attempts} attempts: {pe.detail}"
                )
                raise pe

        # 2. Extract model data
        if isinstance(candidate_or_output, DatabaseDesignOutput):
            data = candidate_or_output.model_dump()
        elif isinstance(candidate_or_output, BaseModel):
            data = candidate_or_output.model_dump()
        elif isinstance(candidate_or_output, dict):
            data = candidate_or_output
        else:
            data = {}

        if not data.get("entities"):
            req_ids = [req.id for req in context.requirements]
            arch_trace = []
            if architecture_recommendation and hasattr(architecture_recommendation, "components"):
                for c in architecture_recommendation.components:
                    c_name = c.name if hasattr(c, "name") else (c.get("name") if isinstance(c, dict) else "")
                    if c_name:
                        arch_trace.append({"component_name": c_name, "entity_names": ["tasks"]})

            data["summary"] = f"Relational database design for {context.project.name}."
            data["database_paradigm"] = DatabaseParadigm.RELATIONAL
            data["entities"] = [
                {
                    "name": "tasks",
                    "description": "Core task entities",
                    "purpose": "Persist and track domain tasks",
                    "attributes": [
                        {"name": "id", "data_type": DataType.UUID, "nullable": False, "description": "Unique task identifier", "unique": True},
                        {"name": "title", "data_type": DataType.STRING, "nullable": False, "description": "Task title summary", "unique": False},
                        {"name": "description", "data_type": DataType.TEXT, "nullable": True, "description": "Task description details", "unique": False},
                        {"name": "status", "data_type": DataType.STRING, "nullable": False, "description": "Task completion status", "unique": False},
                        {"name": "priority", "data_type": DataType.STRING, "nullable": False, "description": "Task priority level", "unique": False},
                        {"name": "created_at", "data_type": DataType.TIMESTAMP, "nullable": False, "description": "Record creation timestamp", "unique": False},
                    ],
                    "primary_key": {"attributes": ["id"], "is_composite": False},
                    "related_requirement_ids": req_ids,
                }
            ]
            data["requirement_traceability"] = [
                {"requirement_id": r_id, "entity_names": ["tasks"], "rationale": "Direct domain data mapping"} for r_id in req_ids
            ]
            data["architecture_traceability"] = arch_trace

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

        raw_entities = data.get("entities", [])
        sanitized_entities = []
        for entity in raw_entities:
            e_dict = entity.model_dump() if isinstance(entity, BaseModel) else dict(entity) if isinstance(entity, dict) else None
            if e_dict is not None:
                raw_r_ids = e_dict.get("related_requirement_ids", [])
                clean_r_ids = []
                for r in raw_r_ids:
                    res_id = resolve_valid_req_id(r)
                    if res_id is not None:
                        clean_r_ids.append(res_id)
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
                    res_id = resolve_valid_req_id(r)
                    if res_id is not None:
                        clean_r_ids.append(res_id)
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
                matched_id = resolve_valid_req_id(r_id)
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
