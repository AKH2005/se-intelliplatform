"""Unit tests for TimelinePredictionAgent lifecycle and registry."""

from datetime import datetime, timezone
import uuid
import pytest

from app.agents.contracts import AgentType
from app.agents.providers.mock import MockLLMProvider
from app.agents.registry import AgentRegistry, register_default_agents
from app.agents.timeline_prediction.agent import TimelinePredictionAgent
from app.agents.timeline_prediction.contracts import TimelinePredictionOutput
from app.ml.features.timeline_features import TimelineFeatureUnavailableError
from app.ml.schemas.timeline_features import TimelineFeatureSchema
from app.schemas.context import ProjectContextResponse, RequirementStatistics
from app.schemas.project import ProjectResponse


def _create_context_with_timeline_inputs(settings: dict | None = None) -> ProjectContextResponse:
    now = datetime.now(timezone.utc)
    default_settings = {
        "ml_timeline_inputs": {
            "afp": 480.0,
            "input_count": 55.0,
            "output_count": 40.0,
            "enquiry_count": 30.0,
            "file_count": 25.0,
            "interface_count": 15.0,
            "resource_level": 2,
        }
    }
    return ProjectContextResponse(
        project=ProjectResponse(
            id=uuid.uuid4(),
            name="Autonomous Timeline Pilot",
            slug="autonomous-timeline-pilot",
            description="Testing timeline prediction agent execution",
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
    """Verify that TimelinePredictionAgent advertises conforming metadata."""
    agent = TimelinePredictionAgent()
    meta = agent.metadata
    assert meta.agent_id == "timeline-prediction"
    assert meta.name == "Timeline Prediction Agent"
    assert meta.version == "1.0.0"
    assert meta.agent_type == AgentType.ANALYSIS
    assert agent.output_schema == TimelinePredictionOutput


@pytest.mark.asyncio
async def test_agent_lifecycle_with_real_artifact():
    """Integration test exercising the real trained model artifact through agent lifecycle."""
    agent = TimelinePredictionAgent()
    context = _create_context_with_timeline_inputs()
    provider = MockLLMProvider()

    # 1. Initialize
    await agent.initialize()

    # 2. Analyze
    analysis = await agent.analyze(context)
    assert "feature_vector" in analysis
    assert analysis["feature_vector"].afp == 480.0
    assert analysis["feature_vector"].resource_level.value == 2

    # 3. Generate (strictly local ML inference)
    output = await agent.generate(analysis, provider)
    assert isinstance(output, TimelinePredictionOutput)
    assert output.predicted_duration_months > 0.0
    assert output.target == "Duration"
    assert output.target_unit == "months"
    assert output.model_provenance.algorithm == "RandomForestRegressor"
    assert output.model_provenance.model_name == "se_timeline_regressor"
    assert output.model_provenance.training_dataset == "China"
    assert len(output.model_provenance.artifact_checksum) == 64
    assert output.feature_names == TimelineFeatureSchema.APPROVED_FEATURES
    assert len(output.limitations) >= 4

    # 4. Validate output
    val_res = agent.validate_output(output, context)
    assert val_res.is_valid is True
    assert len(val_res.errors) == 0


@pytest.mark.asyncio
async def test_agent_analyze_rejects_missing_features():
    """Verify analyze raises TimelineFeatureUnavailableError when settings lacks required features."""
    agent = TimelinePredictionAgent()
    context = _create_context_with_timeline_inputs(settings={})

    with pytest.raises(TimelineFeatureUnavailableError, match="Required ML timeline features are unavailable"):
        await agent.analyze(context)


def test_registry_integration():
    """Verify TimelinePredictionAgent is properly registered in AgentRegistry."""
    registry = AgentRegistry()
    register_default_agents(registry)
    assert registry.has("timeline-prediction")

    agent = registry.get("timeline-prediction")
    assert isinstance(agent, TimelinePredictionAgent)
    assert agent.metadata.agent_id == "timeline-prediction"

    # Verify idempotency
    register_default_agents(registry)
    assert len(registry.list_agents()) == 9
