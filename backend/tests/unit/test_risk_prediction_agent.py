"""Unit tests for RiskPredictionAgent lifecycle and behavior."""

from datetime import datetime, timezone
import uuid
import pytest

from app.agents.contracts import AgentType
from app.agents.providers.mock import MockLLMProvider
from app.agents.registry import AgentRegistry, register_default_agents
from app.agents.risk_prediction.agent import RiskPredictionAgent
from app.agents.risk_prediction.contracts import RiskLevel, RiskPredictionOutput
from app.ml.features.risk_features import MLFeatureUnavailableError
from app.schemas.context import ProjectContextResponse, RequirementStatistics
from app.schemas.project import ProjectResponse


def _create_context_with_ml_inputs(settings: dict | None = None) -> ProjectContextResponse:
    now = datetime.now(timezone.utc)
    default_settings = {
        "ml_risk_inputs": {
            "project_size": "Medium",
            "team_experience_level": "High",
            "estimated_effort_hours": 950.0,
            "complexity_level": "High",
            "requirement_stability": "Moderate",
        }
    }
    return ProjectContextResponse(
        project=ProjectResponse(
            id=uuid.uuid4(),
            name="Autonomous Agent Risk Pilot",
            slug="autonomous-agent-risk-pilot",
            description="Testing risk agent execution",
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
    """Verify that RiskPredictionAgent advertises conforming metadata."""
    agent = RiskPredictionAgent()
    meta = agent.metadata
    assert meta.agent_id == "risk-prediction"
    assert meta.name == "Risk Prediction Agent"
    assert meta.version == "1.0.0"
    assert meta.agent_type == AgentType.ANALYSIS
    assert agent.output_schema == RiskPredictionOutput


@pytest.mark.asyncio
async def test_agent_lifecycle_with_real_artifact():
    """Integration test exercising the real trained model artifact through agent lifecycle."""
    agent = RiskPredictionAgent()
    context = _create_context_with_ml_inputs()
    provider = MockLLMProvider()

    # 1. Initialize
    await agent.initialize()

    # 2. Analyze
    analysis = await agent.analyze(context)
    assert "feature_vector" in analysis
    assert analysis["feature_vector"].project_size.value == "Medium"
    assert analysis["feature_vector"].estimated_effort_hours == 950.0

    # 3. Generate (strictly local ML inference)
    output = await agent.generate(analysis, provider)
    assert isinstance(output, RiskPredictionOutput)
    assert 1.0 <= output.predicted_risk_score <= 10.0
    assert isinstance(output.risk_level, RiskLevel)
    assert output.model_provenance.algorithm == "Ridge"
    assert output.model_provenance.model_name == "se_risk_regressor"
    assert len(output.model_provenance.artifact_checksum) == 64
    assert len(output.limitations) >= 6

    # 4. Validate output
    val_res = agent.validate_output(output, context)
    assert val_res.is_valid is True
    assert len(val_res.errors) == 0


@pytest.mark.asyncio
async def test_agent_analyze_rejects_missing_features():
    """Verify analyze raises MLFeatureUnavailableError when settings lacks required features."""
    agent = RiskPredictionAgent()
    context = _create_context_with_ml_inputs(settings={})

    with pytest.raises(MLFeatureUnavailableError, match="Required ML risk features are unavailable"):
        await agent.analyze(context)


def test_registry_integration():
    """Verify RiskPredictionAgent is properly registered in AgentRegistry."""
    registry = AgentRegistry()
    register_default_agents(registry)
    assert registry.has("risk-prediction")

    agent = registry.get("risk-prediction")
    assert isinstance(agent, RiskPredictionAgent)
    assert agent.metadata.agent_id == "risk-prediction"

    # Verify idempotency
    register_default_agents(registry)
    assert len(registry.list_agents()) == 9
