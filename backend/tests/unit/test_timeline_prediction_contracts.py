"""Unit tests for Timeline Prediction Agent contracts and validation."""

from datetime import datetime, timezone
import uuid
import pytest

from app.agents.timeline_prediction.contracts import (
    DEFAULT_TIMELINE_LIMITATIONS,
    TimelineModelProvenance,
    TimelinePredictionCandidate,
    TimelinePredictionOutput,
)
from app.agents.timeline_prediction.validation import validate_timeline_prediction_output
from app.ml.schemas.timeline_features import TimelineFeatureSchema
from app.schemas.context import ProjectContextResponse, RequirementStatistics
from app.schemas.project import ProjectResponse


def _make_dummy_context() -> ProjectContextResponse:
    now = datetime.now(timezone.utc)
    return ProjectContextResponse(
        project=ProjectResponse(
            id=uuid.uuid4(),
            name="Timeline Test Project",
            slug="timeline-test-project",
            description="Test",
            settings={},
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


def _make_valid_output() -> TimelinePredictionOutput:
    return TimelinePredictionOutput(
        agent_id="timeline-prediction",
        agent_version="1.0.0",
        summary="Estimated project duration is 8.50 months (8.5021 months unrounded). Derived via RandomForestRegressor.",
        predicted_duration_months=8.5021,
        estimated_duration_months=8.50,
        target="Duration",
        target_unit="months",
        model_provenance=TimelineModelProvenance(
            model_name="se_timeline_regressor",
            model_version="1.0.0",
            algorithm="RandomForestRegressor",
            training_dataset="China",
            feature_schema_version="1.0.0",
            artifact_checksum="b" * 64,
        ),
        feature_names=list(TimelineFeatureSchema.APPROVED_FEATURES),
        feature_summary={
            "afp": 450.0,
            "input_count": 50.0,
            "output_count": 35.0,
            "enquiry_count": 25.0,
            "file_count": 20.0,
            "interface_count": 10.0,
            "resource_level": 2,
        },
        limitations=list(DEFAULT_TIMELINE_LIMITATIONS),
    )


def test_validation_passes_valid_output():
    """Verify that a conforming TimelinePredictionOutput passes deterministic validation."""
    context = _make_dummy_context()
    output = _make_valid_output()
    result = validate_timeline_prediction_output(output, context)
    assert result.is_valid is True
    assert len(result.errors) == 0


def test_validation_rejects_non_positive_duration():
    """Verify validation rejects zero or negative duration values."""
    context = _make_dummy_context()
    output = _make_valid_output()
    output.predicted_duration_months = 0.0
    result = validate_timeline_prediction_output(output, context)
    assert result.is_valid is False
    assert any("strictly greater than 0.0" in e for e in result.errors)

    output.predicted_duration_months = -5.0
    result = validate_timeline_prediction_output(output, context)
    assert result.is_valid is False


def test_validation_rejects_invalid_target_and_unit():
    """Verify validation rejects mismatched target or unit of measurement."""
    context = _make_dummy_context()
    output = _make_valid_output()
    output.target = "Effort"
    output.target_unit = "hours"
    result = validate_timeline_prediction_output(output, context)
    assert result.is_valid is False
    assert any("target must be 'Duration'" in e for e in result.errors)
    assert any("target_unit must be 'months'" in e for e in result.errors)


def test_validation_rejects_missing_feature_names():
    """Verify validation rejects feature_names that does not match approved 7 predictors."""
    context = _make_dummy_context()
    output = _make_valid_output()
    output.feature_names = ["AFP", "Input"]  # Incomplete
    result = validate_timeline_prediction_output(output, context)
    assert result.is_valid is False
    assert any("feature_names does not match approved predictors" in e for e in result.errors)


def test_validation_rejects_missing_feature_summary_key():
    """Verify validation rejects feature_summary missing a required key."""
    context = _make_dummy_context()
    output = _make_valid_output()
    del output.feature_summary["afp"]
    result = validate_timeline_prediction_output(output, context)
    assert result.is_valid is False
    assert any("missing required keys" in e for e in result.errors)


def test_validation_rejects_empty_limitations():
    """Verify validation rejects empty limitations list."""
    context = _make_dummy_context()
    output = _make_valid_output()
    output.limitations = []
    result = validate_timeline_prediction_output(output, context)
    assert result.is_valid is False
    assert any("limitations list cannot be empty" in e for e in result.errors)


def test_validation_rejects_prohibited_confidence_language():
    """Verify validation flags prohibited overstatement/confidence claims."""
    context = _make_dummy_context()

    prohibited_phrases = [
        "This is a highly accurate prediction.",
        "Model has high confidence in this duration estimate.",
        "This is a highly reliable project timeline.",
        "This represents production-grade forecasting.",
        "The project duration is guaranteed to be 8 months.",
        "The timeline is 95% confident.",
        "There is an 80% accurate timeline estimate.",
        "High probability of completion in 6 months.",
    ]

    for phrase in prohibited_phrases:
        output = _make_valid_output()
        output.summary = phrase
        result = validate_timeline_prediction_output(output, context)
        assert result.is_valid is False, f"Failed to reject phrase: '{phrase}'"
        assert any("prohibited overstatement/confidence language" in e for e in result.errors)


def test_candidate_serialization():
    """Verify TimelinePredictionCandidate serializes and roundtrips cleanly."""
    candidate = TimelinePredictionCandidate(
        summary="Candidate summary",
        predicted_duration_months=11.2345,
        estimated_duration_months=11.23,
        model_provenance=TimelineModelProvenance(
            model_name="se_timeline_regressor",
            model_version="1.0.0",
            algorithm="RandomForestRegressor",
            training_dataset="China",
            feature_schema_version="1.0.0",
            artifact_checksum="c" * 64,
        ),
        feature_names=list(TimelineFeatureSchema.APPROVED_FEATURES),
        feature_summary={"afp": 500.0},
    )
    dump = candidate.model_dump()
    assert dump["predicted_duration_months"] == 11.2345
    assert dump["estimated_duration_months"] == 11.23
    assert dump["target"] == "Duration"
    assert dump["target_unit"] == "months"
    assert len(dump["limitations"]) == len(DEFAULT_TIMELINE_LIMITATIONS)
