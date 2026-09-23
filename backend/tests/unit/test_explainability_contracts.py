"""Unit tests for Phase 8.2 Explainability & Engineering Insights Agent contracts and validation."""

from datetime import datetime, timezone
import uuid
import pytest
from pydantic import ValidationError

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
from app.agents.explainability.validation import (
    PLATFORM_EXPLAINABILITY_LIMITATIONS,
    build_source_fact_index,
    validate_explainability_input,
    validate_explainability_output,
)
from app.agents.risk_prediction.contracts import (
    RiskLevel,
    RiskModelProvenance,
    RiskPredictionOutput,
)
from app.schemas.context import ProjectContextResponse, RequirementStatistics
from app.schemas.project import ProjectResponse


@pytest.fixture
def sample_context():
    project_id = uuid.uuid4()
    now = datetime.now(timezone.utc)
    project = ProjectResponse(
        id=project_id,
        name="ExplainabilityDemo",
        slug="explainabilitydemo",
        description="Demo project for testing explainability",
        created_at=now,
        updated_at=now,
    )
    stats = RequirementStatistics(
        total_requirements=1,
        active_requirements=1,
        functional_count=1,
        non_functional_count=0,
        constraint_count=0,
        by_priority={"HIGH": 1},
        by_status={"APPROVED": 1},
        completion_percentage=0.0,
    )
    return ProjectContextResponse(
        project=project,
        requirements=[],
        statistics=stats,
        context_version=1,
        generated_at=now,
    )


@pytest.fixture
def sample_risk_output():
    return RiskPredictionOutput(
        predicted_risk_score=7.4,
        risk_level=RiskLevel.HIGH,
        feature_summary={"active_requirements_count": 10},
        model_provenance=RiskModelProvenance(
            model_name="risk_ridge_v1",
            model_version="1.0.0",
            algorithm="Ridge",
            training_dataset="risk_data.csv",
            feature_schema_version="1.0.0",
            artifact_checksum="abc123checksum",
        ),
        summary="High risk predicted due to scope complexity.",
        limitations=["Trained on historical project benchmarks."],
    )


# =========================================================================
# 1. Enum Contract Tests
# =========================================================================

def test_insight_category_enums():
    """Verify all 9 mandated insight categories exist."""
    expected = {
        "REQUIREMENT",
        "ARCHITECTURE",
        "DATABASE",
        "RISK",
        "TIMELINE",
        "DEFECT",
        "TESTING",
        "CODE_REVIEW",
        "CROSS_CUTTING",
    }
    actual = {c.value for c in InsightCategory}
    assert actual == expected


def test_claim_type_enums():
    """Verify epistemic claim types exist."""
    expected = {"FACT", "INTERPRETATION", "RECOMMENDATION", "LIMITATION"}
    actual = {t.value for t in ClaimType}
    assert actual == expected


# =========================================================================
# 2. SourceReference & EngineeringInsight Contract Tests
# =========================================================================

def test_source_reference_valid():
    """Verify valid SourceReference construction."""
    ref = SourceReference(
        agent_id="risk-prediction",
        source_entity_id="risk_ridge_v1",
        source_field="predicted_risk_score",
        claim_type=ClaimType.FACT,
    )
    assert ref.agent_id == "risk-prediction"
    assert ref.source_entity_id == "risk_ridge_v1"
    assert ref.source_field == "predicted_risk_score"
    assert ref.claim_type == ClaimType.FACT


def test_source_reference_extra_forbidden():
    """Verify SourceReference forbids arbitrary extra fields."""
    with pytest.raises(ValidationError):
        SourceReference(
            agent_id="risk-prediction",
            claim_type=ClaimType.FACT,
            unsupported_field="invalid",
        )


def test_engineering_insight_valid():
    """Verify valid EngineeringInsight model construction."""
    ref = SourceReference(
        agent_id="risk-prediction",
        source_entity_id="risk_ridge_v1",
        source_field="predicted_risk_score",
        claim_type=ClaimType.FACT,
    )
    insight = EngineeringInsight(
        insight_id="INSIGHT-001",
        category=InsightCategory.RISK,
        title="High Project Risk Identified",
        summary="Risk score 7.4 indicates substantial delivery uncertainty.",
        explanation="The risk prediction model output suggests complex dependencies.",
        source_references=[ref],
        suggested_actions=["Review scope boundaries and break down epics."],
    )
    assert insight.insight_id == "INSIGHT-001"
    assert insight.category == InsightCategory.RISK
    assert len(insight.source_references) == 1


def test_engineering_insight_empty_source_references_fails():
    """Verify EngineeringInsight requires at least one source reference."""
    with pytest.raises(ValidationError):
        EngineeringInsight(
            insight_id="INSIGHT-001",
            category=InsightCategory.RISK,
            title="High Project Risk",
            summary="Risk is elevated.",
            explanation="Explanation text here.",
            source_references=[],  # Empty list forbidden
        )


# =========================================================================
# 3. ExplainabilityInput Contract Tests
# =========================================================================

def test_explainability_input_valid(sample_risk_output):
    """Verify ExplainabilityInput accepts single upstream output."""
    inp = ExplainabilityInput(
        target_scope="Core Services",
        user_query="Why is risk high?",
        risk_prediction=sample_risk_output,
    )
    assert inp.target_scope == "Core Services"
    assert inp.user_query == "Why is risk high?"
    assert inp.risk_prediction is not None


def test_explainability_input_empty_fails():
    """Verify ExplainabilityInput fails deterministic validation if no outputs supplied."""
    with pytest.raises(ValidationError) as exc:
        ExplainabilityInput()
    assert "at least one upstream agent output" in str(exc.value).lower()


def test_validate_explainability_input_function(sample_risk_output):
    """Verify validate_explainability_input passes with output and rejects empty."""
    valid_input = ExplainabilityInput(risk_prediction=sample_risk_output)
    validate_explainability_input(valid_input)  # Must not raise

    # Direct check if empty somehow bypasses pydantic model_validator
    fake_empty = ExplainabilityInput.model_construct(
        requirement_analysis=None,
        architecture_recommendation=None,
        database_design=None,
        risk_prediction=None,
        timeline_prediction=None,
        bug_prediction=None,
        test_case_generation=None,
        code_review=None,
    )
    with pytest.raises(AgentValidationError):
        validate_explainability_input(fake_empty)


# =========================================================================
# 4. Deterministic Fact Index Tests
# =========================================================================

def test_build_source_fact_index(sample_risk_output):
    """Verify deterministic fact index extracts valid entities, fields, and limitations."""
    inp = ExplainabilityInput(risk_prediction=sample_risk_output)
    index = build_source_fact_index(inp)

    assert "risk-prediction" in index["available_agents"]
    assert "requirement-analysis" not in index["available_agents"]
    assert "risk_ridge_v1" in index["valid_entities_by_agent"]["risk-prediction"]
    assert "predicted_risk_score" in index["valid_fields_by_agent"]["risk-prediction"]
    assert "Trained on historical project benchmarks." in index["upstream_limitations"]


# =========================================================================
# 5. Deterministic Output Validation Tests (Zero Phantom Citations)
# =========================================================================

def test_validate_output_success(sample_risk_output, sample_context):
    """Verify valid ExplainabilityOutput passes deterministic validation."""
    inp = ExplainabilityInput(risk_prediction=sample_risk_output)
    source_index = build_source_fact_index(inp)

    ref = SourceReference(
        agent_id="risk-prediction",
        source_entity_id="risk_ridge_v1",
        source_field="predicted_risk_score",
        claim_type=ClaimType.FACT,
    )
    insight = EngineeringInsight(
        insight_id="INSIGHT-001",
        category=InsightCategory.RISK,
        title="Elevated Risk Score",
        summary="Ridge model predicted score 7.4.",
        explanation="Statistical score indicates higher likelihood of schedule slippage.",
        source_references=[ref],
        suggested_actions=["Review critical path."],
    )
    output = ExplainabilityOutput(
        agent_id="explainability-insights",
        agent_version="1.0.0",
        summary="Explainability synthesis completed.",
        insights=[insight],
        metrics=ExplainabilitySummary(
            analyzed_agents=["risk-prediction"],
            total_insights=1,
            insights_by_category={c.value: (1 if c == InsightCategory.RISK else 0) for c in InsightCategory},
            claims_count_by_type={t.value: (1 if t == ClaimType.FACT else 0) for t in ClaimType},
        ),
        limitations=list(PLATFORM_EXPLAINABILITY_LIMITATIONS),
    )

    result = validate_explainability_output(output, source_index, sample_context)
    assert result.is_valid is True
    assert len(result.errors) == 0


def test_validate_output_rejects_phantom_agent(sample_risk_output, sample_context):
    """Verify rejection when insight references an agent output that was never supplied."""
    inp = ExplainabilityInput(risk_prediction=sample_risk_output)
    source_index = build_source_fact_index(inp)

    phantom_ref = SourceReference(
        agent_id="code-review",  # NOT supplied!
        source_entity_id="CR-001",
        source_field="severity",
        claim_type=ClaimType.FACT,
    )
    insight = EngineeringInsight(
        insight_id="INSIGHT-001",
        category=InsightCategory.CODE_REVIEW,
        title="Phantom Finding",
        summary="References unsupplied code review.",
        explanation="Should be rejected deterministically.",
        source_references=[phantom_ref],
    )
    output = ExplainabilityOutput(
        summary="Synthesis.",
        insights=[insight],
        metrics=ExplainabilitySummary(
            analyzed_agents=["risk-prediction"],
            total_insights=1,
            insights_by_category={c.value: (1 if c == InsightCategory.CODE_REVIEW else 0) for c in InsightCategory},
            claims_count_by_type={t.value: (1 if t == ClaimType.FACT else 0) for t in ClaimType},
        ),
        limitations=["Limitation 1"],
    )

    result = validate_explainability_output(output, source_index, sample_context)
    assert result.is_valid is False
    assert any("references unsupplied or unregistered agent 'code-review'" in err for err in result.errors)


def test_validate_output_rejects_phantom_entity_id(sample_risk_output, sample_context):
    """Verify rejection when insight references non-existent entity ID for supplied agent."""
    inp = ExplainabilityInput(risk_prediction=sample_risk_output)
    source_index = build_source_fact_index(inp)

    phantom_entity_ref = SourceReference(
        agent_id="risk-prediction",
        source_entity_id="NON_EXISTENT_MODEL_UUID",
        source_field="predicted_risk_score",
        claim_type=ClaimType.FACT,
    )
    insight = EngineeringInsight(
        insight_id="INSIGHT-001",
        category=InsightCategory.RISK,
        title="Invalid Model ID",
        summary="References bad model ID.",
        explanation="Should be rejected.",
        source_references=[phantom_entity_ref],
    )
    output = ExplainabilityOutput(
        summary="Synthesis.",
        insights=[insight],
        metrics=ExplainabilitySummary(
            analyzed_agents=["risk-prediction"],
            total_insights=1,
            insights_by_category={c.value: (1 if c == InsightCategory.RISK else 0) for c in InsightCategory},
            claims_count_by_type={t.value: (1 if t == ClaimType.FACT else 0) for t in ClaimType},
        ),
        limitations=["Limitation 1"],
    )

    result = validate_explainability_output(output, source_index, sample_context)
    assert result.is_valid is False
    assert any("references non-existent entity ID 'NON_EXISTENT_MODEL_UUID'" in err for err in result.errors)


def test_validate_output_rejects_phantom_field(sample_risk_output, sample_context):
    """Verify rejection when insight references non-existent field for supplied agent."""
    inp = ExplainabilityInput(risk_prediction=sample_risk_output)
    source_index = build_source_fact_index(inp)

    phantom_field_ref = SourceReference(
        agent_id="risk-prediction",
        source_entity_id="risk_ridge_v1",
        source_field="hallucinated_field_name",
        claim_type=ClaimType.FACT,
    )
    insight = EngineeringInsight(
        insight_id="INSIGHT-001",
        category=InsightCategory.RISK,
        title="Invalid Field Name",
        summary="References bad field.",
        explanation="Should be rejected.",
        source_references=[phantom_field_ref],
    )
    output = ExplainabilityOutput(
        summary="Synthesis.",
        insights=[insight],
        metrics=ExplainabilitySummary(
            analyzed_agents=["risk-prediction"],
            total_insights=1,
            insights_by_category={c.value: (1 if c == InsightCategory.RISK else 0) for c in InsightCategory},
            claims_count_by_type={t.value: (1 if t == ClaimType.FACT else 0) for t in ClaimType},
        ),
        limitations=["Limitation 1"],
    )

    result = validate_explainability_output(output, source_index, sample_context)
    assert result.is_valid is False
    assert any("references non-existent field 'hallucinated_field_name'" in err for err in result.errors)


def test_validate_output_rejects_metrics_mismatch(sample_risk_output, sample_context):
    """Verify rejection when candidate spoofed metrics don't reconcile."""
    inp = ExplainabilityInput(risk_prediction=sample_risk_output)
    source_index = build_source_fact_index(inp)

    ref = SourceReference(
        agent_id="risk-prediction",
        source_entity_id="risk_ridge_v1",
        source_field="predicted_risk_score",
        claim_type=ClaimType.FACT,
    )
    insight = EngineeringInsight(
        insight_id="INSIGHT-001",
        category=InsightCategory.RISK,
        title="Elevated Risk Score",
        summary="Ridge model predicted score 7.4.",
        explanation="Statistical score indicates higher risk.",
        source_references=[ref],
    )
    output = ExplainabilityOutput(
        summary="Synthesis.",
        insights=[insight],
        metrics=ExplainabilitySummary(
            analyzed_agents=["risk-prediction"],
            total_insights=999,  # Mismatch!
            insights_by_category={c.value: 0 for c in InsightCategory},
            claims_count_by_type={t.value: 0 for t in ClaimType},
        ),
        limitations=["Limitation 1"],
    )

    result = validate_explainability_output(output, source_index, sample_context)
    assert result.is_valid is False
    assert any("total_insights" in err for err in result.errors)
