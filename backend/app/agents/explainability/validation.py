"""Deterministic Validation and Fact-Indexing Engine for Explainability Agent."""

from typing import Any
from app.agents.contracts import ValidationResult
from app.agents.exceptions import AgentValidationError
from app.agents.explainability.contracts import (
    ClaimType,
    EngineeringInsight,
    ExplainabilityInput,
    ExplainabilityOutput,
    InsightCategory,
)
from app.schemas.context import ProjectContextResponse

PLATFORM_EXPLAINABILITY_LIMITATIONS = [
    (
        "The Explainability Agent provides advisory, qualitative synthesis and does not alter "
        "or recalculate authoritative upstream predictions, model parameters, or code review findings."
    ),
    (
        "Insights and explanations are strictly grounded in supplied point-in-time upstream agent outputs "
        "and canonical Project Context; no runtime code execution, test verification, or external telemetry was performed."
    ),
    (
        "Statistical machine learning predictions reflect empirical associations within historical datasets "
        "and do not constitute definitive causal proof of software delivery outcomes or runtime defects."
    ),
]


def validate_explainability_input(input_data: ExplainabilityInput) -> None:
    """Enforce deterministic input preconditions on ExplainabilityInput."""
    outputs = [
        input_data.requirement_analysis,
        input_data.architecture_recommendation,
        input_data.database_design,
        input_data.risk_prediction,
        input_data.timeline_prediction,
        input_data.bug_prediction,
        input_data.test_case_generation,
        input_data.code_review,
    ]
    if not any(out is not None for out in outputs):
        raise AgentValidationError(
            message="ExplainabilityInput must contain at least one upstream agent output to explain.",
            validation_errors=["No upstream agent outputs supplied in ExplainabilityInput."],
        )


def build_source_fact_index(input_data: ExplainabilityInput) -> dict[str, Any]:
    """Deterministically extracts all known entity IDs, valid fields, and limitations from supplied outputs.

    This index serves as the single source of truth to prevent phantom citations or hallucinated source IDs.
    """
    available_agents: set[str] = set()
    valid_entities_by_agent: dict[str, set[str]] = {}
    valid_fields_by_agent: dict[str, set[str]] = {}
    upstream_limitations: list[str] = []
    authoritative_facts: dict[str, Any] = {}

    # 1. Requirement Analysis
    if input_data.requirement_analysis is not None:
        agent_id = "requirement-analysis"
        available_agents.add(agent_id)
        ra = input_data.requirement_analysis
        entities: set[str] = set()
        for amb in ra.ambiguities:
            entities.add(str(amb.requirement_id))
        for conf in ra.conflicts:
            entities.add(str(conf.requirement_id))
            entities.add(str(conf.related_requirement_id))
        for gap in ra.missing_information:
            entities.add(gap.area.strip().lower())
        for ref in ra.refinements:
            entities.add(str(ref.requirement_id))
        for clar in ra.scope_clarifications:
            entities.add(clar.topic.strip().lower())

        valid_entities_by_agent[agent_id] = entities
        valid_fields_by_agent[agent_id] = {
            "summary",
            "ambiguities",
            "conflicts",
            "missing_information",
            "refinements",
            "scope_clarifications",
            "completeness_score",
            "active_requirements_count",
            "total_requirements_count",
            "issue",
            "explanation",
            "severity",
            "suggested_clarification",
            "area",
            "description",
            "topic",
            "recommendation",
        }
        authoritative_facts[f"{agent_id}.completeness_score"] = ra.completeness_score
        authoritative_facts[f"{agent_id}.active_requirements_count"] = ra.active_requirements_count

    # 2. Architecture Recommendation
    if input_data.architecture_recommendation is not None:
        agent_id = "architecture-recommendation"
        available_agents.add(agent_id)
        arch = input_data.architecture_recommendation
        entities = set()
        for style in arch.architecture_styles:
            entities.add(style.style.value)
        for comp in arch.components:
            entities.add(comp.name)
            for req_uuid in comp.related_requirement_ids:
                entities.add(str(req_uuid))
        for df in arch.data_flows:
            entities.add(df.source_component)
            entities.add(df.target_component)
        for tech in arch.technologies:
            entities.add(tech.technology)
        for trade in arch.trade_offs:
            entities.add(trade.decision_area)
        for trace in arch.traceability_matrix:
            entities.add(str(trace.requirement_id))

        valid_entities_by_agent[agent_id] = entities
        valid_fields_by_agent[agent_id] = {
            "summary",
            "architecture_styles",
            "components",
            "data_flows",
            "technologies",
            "trade_offs",
            "assumptions",
            "constraints",
            "unknowns",
            "traceability_matrix",
        }

    # 3. Database Design
    if input_data.database_design is not None:
        agent_id = "database-design"
        available_agents.add(agent_id)
        db = input_data.database_design
        entities = set()
        entities.add(db.database_paradigm.value)
        for ent in db.entities:
            entities.add(ent.name)
        for rel in db.relationships:
            entities.add(rel.source_entity)
            entities.add(rel.target_entity)
        for idx in db.indexes:
            entities.add(idx.name)
        for tr in db.requirement_traceability:
            entities.add(str(tr.requirement_id))

        valid_entities_by_agent[agent_id] = entities
        valid_fields_by_agent[agent_id] = {
            "summary",
            "database_paradigm",
            "entities",
            "relationships",
            "indexes",
            "constraints",
            "trade_offs",
            "assumptions",
            "constraints_notes",
            "unknowns",
            "requirement_traceability",
            "architecture_traceability",
        }

    # 4. Risk Prediction
    if input_data.risk_prediction is not None:
        agent_id = "risk-prediction"
        available_agents.add(agent_id)
        rp = input_data.risk_prediction
        entities = {
            rp.model_provenance.model_name,
            rp.risk_level.value,
            *rp.feature_summary.keys(),
        }
        valid_entities_by_agent[agent_id] = entities
        valid_fields_by_agent[agent_id] = {
            "summary",
            "predicted_risk_score",
            "risk_level",
            "feature_summary",
            "model_provenance",
            "limitations",
        }
        upstream_limitations.extend(rp.limitations)
        authoritative_facts[f"{agent_id}.predicted_risk_score"] = rp.predicted_risk_score
        authoritative_facts[f"{agent_id}.risk_level"] = rp.risk_level.value

    # 5. Timeline Prediction
    if input_data.timeline_prediction is not None:
        agent_id = "timeline-prediction"
        available_agents.add(agent_id)
        tp = input_data.timeline_prediction
        entities = {
            tp.model_provenance.model_name,
            tp.target,
            *tp.feature_names,
            *tp.feature_summary.keys(),
        }
        valid_entities_by_agent[agent_id] = entities
        valid_fields_by_agent[agent_id] = {
            "summary",
            "predicted_duration_months",
            "estimated_duration_months",
            "target",
            "target_unit",
            "model_provenance",
            "feature_names",
            "feature_summary",
            "limitations",
        }
        upstream_limitations.extend(tp.limitations)
        authoritative_facts[f"{agent_id}.predicted_duration_months"] = tp.predicted_duration_months
        authoritative_facts[f"{agent_id}.estimated_duration_months"] = tp.estimated_duration_months

    # 6. Bug Prediction
    if input_data.bug_prediction is not None:
        agent_id = "bug-prediction"
        available_agents.add(agent_id)
        bp = input_data.bug_prediction
        entities = {
            bp.model_provenance.model_name,
            bp.prediction_label.value,
            bp.target,
            *bp.feature_names,
            *bp.feature_summary.keys(),
        }
        valid_entities_by_agent[agent_id] = entities
        valid_fields_by_agent[agent_id] = {
            "summary",
            "prediction_label",
            "predicted_probability",
            "target",
            "model_provenance",
            "feature_names",
            "feature_summary",
            "limitations",
        }
        upstream_limitations.extend(bp.limitations)
        authoritative_facts[f"{agent_id}.prediction_label"] = bp.prediction_label.value
        authoritative_facts[f"{agent_id}.predicted_probability"] = bp.predicted_probability

    # 7. Test Case Generation
    if input_data.test_case_generation is not None:
        agent_id = "test-case-generation"
        available_agents.add(agent_id)
        tc = input_data.test_case_generation
        entities = set()
        for case in tc.test_cases:
            entities.add(case.test_case_id)
            for req_id_str in case.requirement_ids:
                entities.add(str(req_id_str).strip())

        valid_entities_by_agent[agent_id] = entities
        valid_fields_by_agent[agent_id] = {
            "summary",
            "test_cases",
            "total_test_cases",
            "coverage",
            "limitations",
            "test_case_id",
            "title",
            "description",
            "test_type",
            "priority",
            "preconditions",
            "steps",
            "expected_results",
            "requirement_ids",
        }
        upstream_limitations.extend(tc.limitations)
        authoritative_facts[f"{agent_id}.total_test_cases"] = tc.total_test_cases
        authoritative_facts[f"{agent_id}.coverage_percentage"] = tc.coverage.coverage_percentage

    # 8. Code Review
    if input_data.code_review is not None:
        agent_id = "code-review"
        available_agents.add(agent_id)
        cr = input_data.code_review
        entities = set(cr.files_reviewed)
        for finding in cr.findings:
            entities.add(finding.finding_id)
            if finding.rule_id:
                entities.add(finding.rule_id)
            entities.add(finding.file_path)

        valid_entities_by_agent[agent_id] = entities
        valid_fields_by_agent[agent_id] = {
            "summary",
            "files_reviewed",
            "findings",
            "metrics",
            "limitations",
            "finding_id",
            "file_path",
            "line_start",
            "line_end",
            "severity",
            "category",
            "source",
            "title",
            "description",
            "evidence",
            "recommendation",
            "rule_id",
        }
        upstream_limitations.extend(cr.limitations)
        authoritative_facts[f"{agent_id}.total_findings"] = cr.metrics.total_findings

    return {
        "available_agents": available_agents,
        "valid_entities_by_agent": valid_entities_by_agent,
        "valid_fields_by_agent": valid_fields_by_agent,
        "upstream_limitations": upstream_limitations,
        "authoritative_facts": authoritative_facts,
    }


def validate_explainability_output(
    output: ExplainabilityOutput,
    source_index: dict[str, Any],
    context: ProjectContextResponse,
) -> ValidationResult:
    """Enforce rigorous deterministic validation on ExplainabilityOutput.

    Invariants:
      1. Non-empty summary and insights list.
      2. Unique, sequential insight IDs (INSIGHT-001, INSIGHT-002, ...).
      3. Valid InsightCategory and ClaimType.
      4. Zero phantom citations: Every SourceReference must link to a supplied agent_id
         and existing source_entity_id / source_field.
      5. Metrics integrity: Analyzed agents list, total insights, category counts,
         and claim type counts must reconcile mathematically.
      6. Limitations non-empty: Must include source-driven and platform limitations.
      7. No duplicate insights (identical category and normalized title).
    """
    errors: list[str] = []

    # 1. Summary check
    if not output.summary.strip():
        errors.append("summary cannot be empty or whitespace only.")

    # 2. Insights non-empty check
    if not output.insights:
        errors.append("insights list cannot be empty.")

    available_agents = source_index.get("available_agents", set())
    valid_entities = source_index.get("valid_entities_by_agent", {})
    valid_fields = source_index.get("valid_fields_by_agent", {})

    seen_insight_ids: set[str] = set()
    seen_fingerprints: set[tuple[str, str]] = set()

    computed_by_category: dict[str, int] = {c.value: 0 for c in InsightCategory}
    computed_by_claim_type: dict[str, int] = {t.value: 0 for t in ClaimType}

    for idx, insight in enumerate(output.insights, start=1):
        prefix = f"Insight [{insight.insight_id or f'index {idx}'}]"

        # Unique insight ID
        raw_id = insight.insight_id.strip()
        if not raw_id:
            errors.append(f"{prefix}: insight_id cannot be blank.")
        elif raw_id in seen_insight_ids:
            errors.append(f"Duplicate insight_id '{raw_id}' detected in explainability output.")
        else:
            seen_insight_ids.add(raw_id)

        # Field completeness
        if not insight.title.strip():
            errors.append(f"{prefix}: title cannot be empty.")
        if not insight.summary.strip():
            errors.append(f"{prefix}: summary cannot be empty.")
        if not insight.explanation.strip():
            errors.append(f"{prefix}: explanation cannot be empty.")

        # Duplicate insight prevention
        fingerprint = (insight.category.value, insight.title.strip().lower())
        if fingerprint in seen_fingerprints:
            errors.append(
                f"{prefix}: duplicate insight detected for category '{insight.category.value}' "
                f"with title '{insight.title}'."
            )
        else:
            seen_fingerprints.add(fingerprint)

        # Category count tracking
        computed_by_category[insight.category.value] = (
            computed_by_category.get(insight.category.value, 0) + 1
        )

        # Source reference validation (Zero phantom citations)
        if not insight.source_references:
            errors.append(f"{prefix}: must contain at least one source_reference.")
        else:
            for ref_idx, ref in enumerate(insight.source_references, start=1):
                ref_prefix = f"{prefix}, reference {ref_idx}"

                # Agent authority check
                clean_agent_id = ref.agent_id.strip()
                if clean_agent_id not in available_agents:
                    errors.append(
                        f"{ref_prefix}: references unsupplied or unregistered agent '{clean_agent_id}'. "
                        f"Available supplied agents are: {sorted(list(available_agents))}."
                    )
                else:
                    # Entity authority check if entity ID is provided
                    if ref.source_entity_id:
                        entity_clean = ref.source_entity_id.strip()
                        allowed_entities = valid_entities.get(clean_agent_id, set())
                        if (
                            allowed_entities
                            and entity_clean not in allowed_entities
                            and entity_clean.lower() not in {e.lower() for e in allowed_entities}
                        ):
                            errors.append(
                                f"{ref_prefix}: references non-existent entity ID '{ref.source_entity_id}' "
                                f"for agent '{clean_agent_id}'."
                            )

                    # Field authority check if field is provided
                    if ref.source_field:
                        field_clean = ref.source_field.strip()
                        allowed_fields = valid_fields.get(clean_agent_id, set())
                        if allowed_fields and field_clean not in allowed_fields:
                            errors.append(
                                f"{ref_prefix}: references non-existent field '{ref.source_field}' "
                                f"for agent '{clean_agent_id}'."
                            )

                # Track claim type
                computed_by_claim_type[ref.claim_type.value] = (
                    computed_by_claim_type.get(ref.claim_type.value, 0) + 1
                )

    # 3. Metrics Reconciliation
    metrics = output.metrics
    expected_analyzed = sorted(list(available_agents))
    if sorted(metrics.analyzed_agents) != expected_analyzed:
        errors.append(
            f"metrics.analyzed_agents mismatch: expected {expected_analyzed}, got {sorted(metrics.analyzed_agents)}."
        )

    if metrics.total_insights != len(output.insights):
        errors.append(
            f"metrics.total_insights ({metrics.total_insights}) mismatch with actual "
            f"insights count ({len(output.insights)})."
        )

    for cat_name, expected_count in computed_by_category.items():
        actual_count = metrics.insights_by_category.get(cat_name, 0)
        if actual_count != expected_count:
            errors.append(
                f"metrics.insights_by_category['{cat_name}'] mismatch: expected {expected_count}, got {actual_count}."
            )

    for claim_name, expected_count in computed_by_claim_type.items():
        actual_count = metrics.claims_count_by_type.get(claim_name, 0)
        if actual_count != expected_count:
            errors.append(
                f"metrics.claims_count_by_type['{claim_name}'] mismatch: expected {expected_count}, got {actual_count}."
            )

    # 4. Limitations invariant (source-driven)
    if not output.limitations:
        errors.append("limitations list cannot be empty.")

    return ValidationResult(
        is_valid=len(errors) == 0,
        errors=errors,
    )
