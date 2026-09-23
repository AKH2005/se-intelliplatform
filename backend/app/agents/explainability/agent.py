"""Explainability & Engineering Insights Agent Implementation."""

import logging
from typing import Any

from app.agents.base import AbstractBaseAgent
from app.agents.contracts import (
    AgentMetadata,
    AgentType,
    ValidationResult,
)
from app.agents.exceptions import AgentValidationError
from app.agents.explainability.contracts import (
    ClaimType,
    EngineeringInsight,
    ExplainabilityCandidate,
    ExplainabilityInput,
    ExplainabilityOutput,
    ExplainabilitySummary,
    InsightCategory,
    SourceReference,
)
from app.agents.explainability.prompts import (
    SYSTEM_PROMPT,
    build_explainability_prompt,
)
from app.agents.explainability.validation import (
    PLATFORM_EXPLAINABILITY_LIMITATIONS,
    build_source_fact_index,
    validate_explainability_input,
    validate_explainability_output,
)
from app.agents.providers.base import (
    AbstractLLMProvider,
    LLMMessage,
    LLMRequest,
)
from app.core.config import settings
from app.schemas.context import ProjectContextResponse

logger = logging.getLogger(__name__)


class ExplainabilityAgent(AbstractBaseAgent[ExplainabilityOutput]):
    """AI Agent responsible for grounded explainability and cross-domain engineering insights.

    Role:
    - Explanatory Synthesizer across existing upstream agent outputs.
    - Preserves upstream facts, metrics, risk bands, predictions, and code review findings.
    - Deterministically validates all citations (Zero Phantom Citations).
    - Enforces epistemic boundaries between FACT, INTERPRETATION, RECOMMENDATION, and LIMITATION.
    - Normalizes insight IDs and authoritatively computes summary metrics.
    """

    def __init__(self) -> None:
        self._source_index: dict[str, Any] = {}

    @property
    def metadata(self) -> AgentMetadata:
        return AgentMetadata(
            agent_id="explainability-insights",
            name="Explainability & Engineering Insights Agent",
            description="Consumes validated outputs from platform agents to produce grounded explanations, cross-domain insights, and actionable guidance.",
            version="1.0.0",
            agent_type=AgentType.ANALYSIS,
        )

    @property
    def output_schema(self) -> type[ExplainabilityOutput]:
        return ExplainabilityOutput

    async def initialize(self) -> None:
        """Lifecycle Hook 1: Pre-execution initialization."""
        self._source_index.clear()

    async def analyze(
        self,
        context: ProjectContextResponse,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Lifecycle Hook 2: Deterministic input extraction, validation, and fact indexing."""
        raw_input = kwargs.get("explainability_input") or kwargs.get("input")
        if raw_input is None:
            raise AgentValidationError(
                message="ExplainabilityAgent requires 'explainability_input' containing upstream agent outputs.",
                validation_errors=["Missing required 'explainability_input' argument in agent execution."],
            )

        if isinstance(raw_input, ExplainabilityInput):
            input_data = raw_input
        elif isinstance(raw_input, dict):
            try:
                input_data = ExplainabilityInput.model_validate(raw_input)
            except Exception as e:
                raise AgentValidationError(
                    message=f"Invalid ExplainabilityInput payload: {e}",
                    validation_errors=[str(e)],
                ) from e
        else:
            raise AgentValidationError(
                message="Argument 'explainability_input' must be an ExplainabilityInput instance or valid dictionary.",
                validation_errors=["Invalid input type for ExplainabilityInput."],
            )

        # Enforce deterministic input preconditions
        validate_explainability_input(input_data)

        # Extract deterministic source & fact index from supplied outputs
        source_index = build_source_fact_index(input_data)
        self._source_index = source_index

        return {
            "context": context,
            "input_data": input_data,
            "source_index": source_index,
        }

    async def generate(
        self,
        analysis_result: dict[str, Any],
        provider: AbstractLLMProvider,
        **kwargs: Any,
    ) -> ExplainabilityOutput:
        """Lifecycle Hook 3: Invoke LLM provider, filter citations, normalize IDs, and build authoritative output."""
        context: ProjectContextResponse = analysis_result["context"]
        input_data: ExplainabilityInput = analysis_result["input_data"]
        source_index: dict[str, Any] = analysis_result["source_index"]

        user_prompt = build_explainability_prompt(
            context=context,
            input_data=input_data,
            source_index=source_index,
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

        # 1. Request structured candidate from LLM provider
        candidate_or_output = await provider.generate_structured(
            request=request,
            response_model=ExplainabilityCandidate,
        )

        # 2. Extract candidate fields safely
        if isinstance(candidate_or_output, (ExplainabilityCandidate, ExplainabilityOutput)):
            candidate_summary = candidate_or_output.summary
            candidate_insights = candidate_or_output.insights
        elif isinstance(candidate_or_output, dict):
            candidate_summary = candidate_or_output.get("summary", "Explainability synthesis completed.")
            raw_insights = candidate_or_output.get("insights", [])
            candidate_insights = [
                i if isinstance(i, EngineeringInsight) else EngineeringInsight.model_validate(i)
                for i in raw_insights
            ]
        else:
            candidate_summary = "Explainability synthesis completed."
            candidate_insights = []

        available_agents: set[str] = source_index.get("available_agents", set())
        valid_entities_by_agent: dict[str, set[str]] = source_index.get("valid_entities_by_agent", {})
        valid_fields_by_agent: dict[str, set[str]] = source_index.get("valid_fields_by_agent", {})

        # 3. Deterministically Filter and Validate Source References (Zero Phantom Citations)
        valid_insights: list[EngineeringInsight] = []
        seen_fingerprints: set[tuple[str, str]] = set()

        for cand_insight in candidate_insights:
            # Check basic field completeness
            title = cand_insight.title.strip()
            summary = cand_insight.summary.strip()
            explanation = cand_insight.explanation.strip()
            if not title or not summary or not explanation:
                continue

            # Duplicate insight check
            fingerprint = (cand_insight.category.value, title.lower())
            if fingerprint in seen_fingerprints:
                continue

            validated_refs: list[SourceReference] = []
            for ref in cand_insight.source_references:
                clean_agent_id = ref.agent_id.strip()
                # 3a. Agent authority
                if clean_agent_id not in available_agents:
                    logger.warning(
                        f"Discarding phantom source reference to unsupplied agent '{clean_agent_id}'"
                    )
                    continue

                # 3b. Entity authority
                if ref.source_entity_id:
                    entity_clean = ref.source_entity_id.strip()
                    allowed_entities = valid_entities_by_agent.get(clean_agent_id, set())
                    if (
                        allowed_entities
                        and entity_clean not in allowed_entities
                        and entity_clean.lower() not in {e.lower() for e in allowed_entities}
                    ):
                        logger.warning(
                            f"Discarding phantom source entity '{ref.source_entity_id}' for agent '{clean_agent_id}'"
                        )
                        continue

                # 3c. Field authority
                if ref.source_field:
                    field_clean = ref.source_field.strip()
                    allowed_fields = valid_fields_by_agent.get(clean_agent_id, set())
                    if allowed_fields and field_clean not in allowed_fields:
                        logger.warning(
                            f"Discarding phantom source field '{ref.source_field}' for agent '{clean_agent_id}'"
                        )
                        continue

                validated_refs.append(ref)

            # Insight is only retained if it has at least one valid source reference
            if validated_refs:
                seen_fingerprints.add(fingerprint)
                valid_insights.append(
                    cand_insight.model_copy(
                        update={"source_references": validated_refs}
                    )
                )

        # 4. Enforce Invariant: At least one grounded insight must survive validation
        if not valid_insights:
            raise AgentValidationError(
                message="Explainability generation failed deterministic validation: No valid grounded insights produced from candidate.",
                validation_errors=[
                    "All candidate insights failed deterministic source validation against supplied upstream outputs."
                ],
            )

        # 5. Deterministic Sequential ID Normalization (INSIGHT-001, INSIGHT-002, ...)
        finalized_insights: list[EngineeringInsight] = []
        for idx, ins in enumerate(valid_insights, start=1):
            normalized_ins = ins.model_copy(
                update={"insight_id": f"INSIGHT-{idx:03d}"}
            )
            finalized_insights.append(normalized_ins)

        # 6. Authoritative Summary Metrics Calculation
        computed_by_category: dict[str, int] = {c.value: 0 for c in InsightCategory}
        computed_by_claim_type: dict[str, int] = {t.value: 0 for t in ClaimType}

        for ins in finalized_insights:
            computed_by_category[ins.category.value] = (
                computed_by_category.get(ins.category.value, 0) + 1
            )
            for ref in ins.source_references:
                computed_by_claim_type[ref.claim_type.value] = (
                    computed_by_claim_type.get(ref.claim_type.value, 0) + 1
                )

        summary_metrics = ExplainabilitySummary(
            analyzed_agents=sorted(list(available_agents)),
            total_insights=len(finalized_insights),
            insights_by_category=computed_by_category,
            claims_count_by_type=computed_by_claim_type,
        )

        # 7. Aggregate Limitations (Source-driven + Canonical Platform Limitations)
        combined_limitations: list[str] = []
        for lim in source_index.get("upstream_limitations", []):
            if lim not in combined_limitations:
                combined_limitations.append(lim)
        for lim in PLATFORM_EXPLAINABILITY_LIMITATIONS:
            if lim not in combined_limitations:
                combined_limitations.append(lim)

        return ExplainabilityOutput(
            agent_id=self.metadata.agent_id,
            agent_version=self.metadata.version,
            summary=candidate_summary,
            insights=finalized_insights,
            metrics=summary_metrics,
            limitations=combined_limitations,
        )

    def validate_output(
        self,
        output: ExplainabilityOutput,
        context: ProjectContextResponse,
    ) -> ValidationResult:
        """Lifecycle Hook 4: Deterministic output validation hook."""
        return validate_explainability_output(
            output=output,
            source_index=self._source_index,
            context=context,
        )
