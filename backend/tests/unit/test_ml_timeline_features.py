"""Unit tests for Timeline (Duration) Prediction feature extraction and schemas."""

from datetime import datetime, timezone
import uuid
import pytest
from pydantic import ValidationError

from app.ml.features.timeline_features import (
    TimelineFeatureUnavailableError,
    extract_timeline_features,
)
from app.ml.schemas.timeline_features import ResourceLevel, TimelineFeatureVector
from app.schemas.context import ProjectContextResponse, RequirementStatistics
from app.schemas.project import ProjectResponse


def _make_dummy_context(settings: dict | None = None) -> ProjectContextResponse:
    now = datetime.now(timezone.utc)
    return ProjectContextResponse(
        project=ProjectResponse(
            id=uuid.uuid4(),
            name="Timeline Pilot",
            slug="timeline-pilot",
            description="A pilot project for duration estimation",
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


def test_timeline_feature_vector_validation():
    """Verify valid TimelineFeatureVector creation and dictionary export."""
    vector = TimelineFeatureVector(
        afp=350.0,
        input_count=45.0,
        output_count=30.0,
        enquiry_count=20.0,
        file_count=15.0,
        interface_count=5.0,
        resource_level=ResourceLevel.LEVEL_2,
    )
    assert vector.afp == 350.0
    assert vector.resource_level == ResourceLevel.LEVEL_2

    data = vector.to_model_input_dict()
    assert data["AFP"] == 350.0
    assert data["Input"] == 45.0
    assert data["Output"] == 30.0
    assert data["Enquiry"] == 20.0
    assert data["File"] == 15.0
    assert data["Interface"] == 5.0
    assert data["Resource"] == 2


def test_timeline_feature_vector_rejects_non_positive_afp():
    """Verify TimelineFeatureVector rejects zero or negative AFP."""
    with pytest.raises(ValidationError):
        TimelineFeatureVector(
            afp=0.0,
            input_count=10.0,
            output_count=10.0,
            enquiry_count=10.0,
            file_count=10.0,
            interface_count=10.0,
            resource_level=ResourceLevel.LEVEL_1,
        )

    with pytest.raises(ValidationError):
        TimelineFeatureVector(
            afp=-50.0,
            input_count=10.0,
            output_count=10.0,
            enquiry_count=10.0,
            file_count=10.0,
            interface_count=10.0,
            resource_level=ResourceLevel.LEVEL_1,
        )


def test_timeline_feature_vector_rejects_invalid_resource():
    """Verify TimelineFeatureVector rejects unknown resource tier."""
    with pytest.raises(ValidationError):
        TimelineFeatureVector(
            afp=100.0,
            input_count=10.0,
            output_count=10.0,
            enquiry_count=10.0,
            file_count=10.0,
            interface_count=10.0,
            resource_level=9,  # type: ignore
        )


def test_extract_timeline_features_success():
    """Verify extract_timeline_features extracts valid features from ml_timeline_inputs."""
    settings = {
        "ml_timeline_inputs": {
            "afp": 450.0,
            "input_count": 50.0,
            "output_count": 35.0,
            "enquiry_count": 25.0,
            "file_count": 20.0,
            "interface_count": 10.0,
            "resource_level": 3,
        }
    }
    context = _make_dummy_context(settings=settings)
    features = extract_timeline_features(context)
    assert features.afp == 450.0
    assert features.resource_level == ResourceLevel.LEVEL_3
    assert features.input_count == 50.0


def test_extract_timeline_features_top_level_settings():
    """Verify extract_timeline_features supports top-level settings."""
    settings = {
        "afp": 220.0,
        "input_count": 20.0,
        "output_count": 15.0,
        "enquiry_count": 10.0,
        "file_count": 8.0,
        "interface_count": 2.0,
        "resource_level": 1,
    }
    context = _make_dummy_context(settings=settings)
    features = extract_timeline_features(context)
    assert features.afp == 220.0
    assert features.resource_level == ResourceLevel.LEVEL_1


def test_extract_timeline_features_rejects_missing_features():
    """Verify extract_timeline_features raises TimelineFeatureUnavailableError when missing predictors."""
    context = _make_dummy_context(settings={})
    with pytest.raises(TimelineFeatureUnavailableError, match="Required ML timeline features are unavailable"):
        extract_timeline_features(context)


def test_extract_timeline_features_rejects_partial_features():
    """Verify extract_timeline_features identifies specific missing keys."""
    settings = {
        "afp": 150.0,
        "input_count": 10.0,
        # Missing other 5 features
    }
    context = _make_dummy_context(settings=settings)
    with pytest.raises(TimelineFeatureUnavailableError) as exc_info:
        extract_timeline_features(context)
    assert "output_count" in exc_info.value.missing_features
    assert "resource_level" in exc_info.value.missing_features
