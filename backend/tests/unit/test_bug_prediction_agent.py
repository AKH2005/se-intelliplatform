"""Unit tests for BugPredictionAgent lifecycle and registry integration."""

from datetime import datetime, timezone
import uuid
import pytest

from app.agents.bug_prediction.agent import BugPredictionAgent
from app.agents.bug_prediction.contracts import BugPredictionOutput, DefectPredictionLabel
from app.agents.contracts import AgentType
from app.agents.providers.mock import MockLLMProvider
from app.agents.registry import AgentRegistry, register_default_agents
from app.ml.features.bug_features import BugFeatureUnavailableError
from app.ml.schemas.bug_features import BugFeatureSchema
from app.schemas.context import ProjectContextResponse, RequirementStatistics
from app.schemas.project import ProjectResponse


def _create_context_with_bug_inputs(settings: dict | None = None) -> ProjectContextResponse:
    now = datetime.now(timezone.utc)
    default_settings = {
        "ml_bug_inputs": {
            "loc": 45.0,
            "v(g)": 7.0,
            "ev(g)": 3.0,
            "iv(g)": 4.0,
            "n": 120.0,
            "v": 650.0,
            "l": 0.05,
            "d": 20.0,
            "i": 32.5,
            "e": 13000.0,
            "b": 0.22,
            "t": 722.0,
            "lOCode": 35.0,
            "lOComment": 5.0,
            "lOBlank": 5.0,
            "locCodeAndComment": 2.0,
            "uniq_Op": 18.0,
            "uniq_Opnd": 25.0,
            "total_Op": 70.0,
            "total_Opnd": 50.0,
            "branchCount": 13.0,
        }
    }
    return ProjectContextResponse(
        project=ProjectResponse(
            id=uuid.uuid4(),
            name="Autonomous Bug Pilot",
            slug="autonomous-bug-pilot",
            description="Testing bug prediction agent execution",
            settings=settings if settings is not None else default_settings,
            is_active=True,
            created_at=now,
            updated_at=now,
        ),
        requirements=[],
        statistics=RequirementStatistics(
            total_requirements=0,
            active_requirements=0,
            functional_count=0,
            non_functional_count=0,
            constraint_count=0,
            by_priority={},
            by_status={},
            completion_percentage=0.0,
        ),
        context_version=1,
        generated_at=now,
    )


def test_agent_metadata():
    """Verify that BugPredictionAgent advertises conforming metadata."""
    agent = BugPredictionAgent()
    meta = agent.metadata
    assert meta.agent_id == "bug-prediction"
    assert meta.name == "Bug Prediction Agent"
    assert meta.version == "1.0.0"
    assert meta.agent_type == AgentType.ANALYSIS
    assert agent.output_schema == BugPredictionOutput


@pytest.mark.asyncio
async def test_agent_lifecycle_with_real_artifact():
    """Integration test exercising the real trained model artifact through agent lifecycle."""
    agent = BugPredictionAgent()
    context = _create_context_with_bug_inputs()
    provider = MockLLMProvider()

    # 1. Initialize
    await agent.initialize()

    # 2. Analyze
    analysis = await agent.analyze(context)
    assert "feature_vector" in analysis
    assert analysis["feature_vector"].loc == 45.0
    assert analysis["feature_vector"].v_g == 7.0

    # 3. Generate (strictly local ML inference without calling LLM)
    output = await agent.generate(analysis, provider)
    assert isinstance(output, BugPredictionOutput)
    assert isinstance(output.prediction_label, DefectPredictionLabel)
    assert 0.0 <= output.predicted_probability <= 1.0
    assert output.target == "defects"
    assert output.model_provenance.algorithm == "LogisticRegression"
    assert output.model_provenance.model_name == "se_bug_classifier"
    assert output.model_provenance.training_dataset == "JM1"
    assert output.model_provenance.artifact_checksum == "563b2b0ffd522df7ff8f50b0a025a9e64a678fb917ac7bbddc2f15e2035e430e"
    assert output.feature_names == BugFeatureSchema.APPROVED_FEATURES
    assert len(output.limitations) >= 4

    # 4. Validate output
    val_res = agent.validate_output(output, context)
    assert val_res.is_valid is True
    assert len(val_res.errors) == 0

    # 5. Verify LLM provider was never invoked
    assert len(provider.call_history) == 0


@pytest.mark.asyncio
async def test_agent_lifecycle_non_defective_path():
    """Verify inference for a low-complexity module predicted as NON_DEFECTIVE."""
    low_complexity_metrics = {
        "loc": 5.0,
        "v(g)": 1.0,
        "ev(g)": 1.0,
        "iv(g)": 1.0,
        "n": 10.0,
        "v": 30.0,
        "l": 0.5,
        "d": 2.0,
        "i": 15.0,
        "e": 60.0,
        "b": 0.01,
        "t": 3.0,
        "lOCode": 4.0,
        "lOComment": 1.0,
        "lOBlank": 0.0,
        "locCodeAndComment": 0.0,
        "uniq_Op": 4.0,
        "uniq_Opnd": 4.0,
        "total_Op": 6.0,
        "total_Opnd": 4.0,
        "branchCount": 1.0,
    }
    agent = BugPredictionAgent()
    context = _create_context_with_bug_inputs(settings={"ml_bug_inputs": low_complexity_metrics})
    provider = MockLLMProvider()

    await agent.initialize()
    analysis = await agent.analyze(context)
    output = await agent.generate(analysis, provider)

    assert output.prediction_label == DefectPredictionLabel.NON_DEFECTIVE
    assert output.predicted_probability < 0.5
    assert agent.validate_output(output, context).is_valid


@pytest.mark.asyncio
async def test_agent_lifecycle_defective_path():
    """Verify inference for a high-complexity module predicted as DEFECTIVE."""
    high_complexity_metrics = {
        "loc": 350.0,
        "v(g)": 45.0,
        "ev(g)": 25.0,
        "iv(g)": 20.0,
        "n": 1200.0,
        "v": 8500.0,
        "l": 0.01,
        "d": 60.0,
        "i": 140.0,
        "e": 510000.0,
        "b": 2.8,
        "t": 28333.0,
        "lOCode": 280.0,
        "lOComment": 40.0,
        "lOBlank": 30.0,
        "locCodeAndComment": 15.0,
        "uniq_Op": 45.0,
        "uniq_Opnd": 85.0,
        "total_Op": 750.0,
        "total_Opnd": 450.0,
        "branchCount": 85.0,
    }
    agent = BugPredictionAgent()
    context = _create_context_with_bug_inputs(settings={"ml_bug_inputs": high_complexity_metrics})
    provider = MockLLMProvider()

    await agent.initialize()
    analysis = await agent.analyze(context)
    output = await agent.generate(analysis, provider)

    assert output.prediction_label == DefectPredictionLabel.DEFECTIVE
    assert output.predicted_probability > 0.5
    assert agent.validate_output(output, context).is_valid


@pytest.mark.asyncio
async def test_agent_analyze_rejects_missing_features():
    """Verify analyze raises BugFeatureUnavailableError when settings lacks required features."""
    agent = BugPredictionAgent()
    context = _create_context_with_bug_inputs(settings={})

    with pytest.raises(BugFeatureUnavailableError, match="Required ML bug prediction features are unavailable"):
        await agent.analyze(context)


def test_registry_integration():
    """Verify BugPredictionAgent is properly registered in AgentRegistry."""
    registry = AgentRegistry()
    register_default_agents(registry)
    assert registry.has("bug-prediction")

    agent = registry.get("bug-prediction")
    assert isinstance(agent, BugPredictionAgent)
    assert agent.metadata.agent_id == "bug-prediction"

    # Verify idempotency
    register_default_agents(registry)
    assert len(registry.list_agents()) == 7
