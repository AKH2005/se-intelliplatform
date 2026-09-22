"""Unit tests for ML risk feature extraction and schemas."""

from datetime import datetime, timezone
import uuid
import pytest
from pydantic import ValidationError

from app.schemas.context import ProjectContextResponse, RequirementStatistics
from app.schemas.project import ProjectResponse
from app.ml.schemas.risk_features import (
    ComplexityLevel,
    ProjectMLSettings,
    ProjectSize,
    RequirementStability,
    RiskFeatureSchema,
    RiskFeatureVector,
    TeamExperienceLevel,
)
from app.ml.features.risk_features import (
    MLFeatureUnavailableError,
    extract_risk_features,
)


def _make_dummy_context(settings: dict | None = None) -> ProjectContextResponse:
    project_id = uuid.uuid4()
    now = datetime.now(timezone.utc)
    return ProjectContextResponse(
        project=ProjectResponse(
            id=project_id,
            name="Risk Pilot",
            slug="risk-pilot",
            description="A pilot project",
            settings=settings or {},
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


def test_risk_feature_vector_validation():
    """Verify valid RiskFeatureVector creation and dictionary export."""
    vector = RiskFeatureVector(
        project_size=ProjectSize.MEDIUM,
        team_experience_level=TeamExperienceLevel.HIGH,
        estimated_effort_hours=450.0,
        complexity_level=ComplexityLevel.LOW,
        requirement_stability=RequirementStability.STABLE,
    )
    assert vector.project_size == ProjectSize.MEDIUM
    data = vector.to_model_input_dict()
    assert data["Project_Size"] == "Medium"
    assert data["Team_Experience_Level"] == "High"
    assert data["Estimated_Effort_Hours"] == 450.0
    assert data["Complexity_Level"] == "Low"
    assert data["Requirement_Stability"] == "Stable"


def test_risk_feature_vector_rejects_negative_effort():
    """Verify RiskFeatureVector rejects negative effort hours."""
    with pytest.raises(ValidationError):
        RiskFeatureVector(
            project_size=ProjectSize.MEDIUM,
            team_experience_level=TeamExperienceLevel.HIGH,
            estimated_effort_hours=-5.0,
            complexity_level=ComplexityLevel.LOW,
            requirement_stability=RequirementStability.STABLE,
        )


def test_risk_feature_vector_rejects_invalid_enum():
    """Verify RiskFeatureVector rejects unknown categorical string."""
    with pytest.raises(ValidationError):
        RiskFeatureVector(
            project_size="SuperLarge",  # type: ignore
            team_experience_level=TeamExperienceLevel.HIGH,
            estimated_effort_hours=500.0,
            complexity_level=ComplexityLevel.LOW,
            requirement_stability=RequirementStability.STABLE,
        )


def test_extract_risk_features_success():
    """Verify extract_risk_features succeeds when settings has ml_risk_inputs."""
    settings = {
        "ml_risk_inputs": {
            "project_size": "Large",
            "team_experience_level": "Medium",
            "complexity_level": "High",
            "requirement_stability": "Moderate",
            "estimated_effort_hours": 200.0,
        }
    }
    context = _make_dummy_context(settings=settings)
    features = extract_risk_features(context)
    assert features.project_size == ProjectSize.LARGE
    assert features.team_experience_level == TeamExperienceLevel.MEDIUM
    assert features.complexity_level == ComplexityLevel.HIGH
    assert features.requirement_stability == RequirementStability.MODERATE
    assert features.estimated_effort_hours == 200.0


def test_extract_risk_features_top_level_settings():
    """Verify extract_risk_features works with top-level settings keys."""
    settings = {
        "project_size": "Small",
        "team_experience_level": "Low",
        "complexity_level": "Low",
        "requirement_stability": "Stable",
        "estimated_effort_hours": 350.0,
    }
    context = _make_dummy_context(settings=settings)
    features = extract_risk_features(context)
    assert features.estimated_effort_hours == 350.0
    assert features.project_size == ProjectSize.SMALL


def test_extract_risk_features_rejects_missing_ml_features():
    """Verify extract_risk_features rejects project without settings."""
    context = _make_dummy_context(settings={})
    with pytest.raises(MLFeatureUnavailableError, match="Required ML risk features are unavailable"):
        extract_risk_features(context)


def test_extract_risk_features_rejects_missing_effort_hours():
    """Verify extract_risk_features rejects missing effort hours without silent imputation."""
    settings = {
        "project_size": "Small",
        "team_experience_level": "Low",
        "complexity_level": "Low",
        "requirement_stability": "Stable",
    }
    context = _make_dummy_context(settings=settings)
    with pytest.raises(MLFeatureUnavailableError, match="Required ML risk features are unavailable"):
        extract_risk_features(context)
