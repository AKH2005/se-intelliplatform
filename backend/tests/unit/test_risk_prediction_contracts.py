"""Unit tests for Risk Prediction Agent contracts and validation."""

from datetime import datetime, timezone
import uuid
import pytest

from app.agents.risk_prediction.contracts import (
    DEFAULT_MODEL_LIMITATIONS,
    RiskLevel,
    RiskModelProvenance,
    RiskPredictionCandidate,
    RiskPredictionOutput,
    map_risk_score_to_level,
)
from app.agents.risk_prediction.validation import validate_risk_prediction_output
from app.schemas.context import ProjectContextResponse, RequirementStatistics
from app.schemas.project import ProjectResponse


def _make_dummy_context() -> ProjectContextResponse:
    now = datetime.now(timezone.utc)
    return ProjectContextResponse(
        project=ProjectResponse(
            id=uuid.uuid4(),
            name="Risk Test Project",
            slug="risk-test-project",
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


def _make_valid_output() -> RiskPredictionOutput:
    return RiskPredictionOutput(
        summary="Predicted project risk score is 5.50 (scale 1.0–10.0), categorized as MEDIUM risk.",
        predicted_risk_score=5.50,
        risk_level=RiskLevel.MEDIUM,
        feature_summary={
            "project_size": "Medium",
            "team_experience_level": "High",
            "estimated_effort_hours": 1000.0,
            "complexity_level": "Medium",
            "requirement_stability": "Stable",
        },
        model_provenance=RiskModelProvenance(
            model_name="se_risk_regressor",
            model_version="1.0.0",
            algorithm="Ridge",
            training_dataset="Reduced_Software_Project_Risk_Dataset_585.csv",
            feature_schema_version="1.0.0",
            artifact_checksum="a" * 64,
        ),
        limitations=list(DEFAULT_MODEL_LIMITATIONS),
    )


def test_map_risk_score_to_level():
    """Verify deterministic risk level mapping across all boundary conditions."""
    assert map_risk_score_to_level(1.0) == RiskLevel.LOW
    assert map_risk_score_to_level(3.49) == RiskLevel.LOW
    assert map_risk_score_to_level(3.50) == RiskLevel.MEDIUM
    assert map_risk_score_to_level(5.00) == RiskLevel.MEDIUM
    assert map_risk_score_to_level(6.49) == RiskLevel.MEDIUM
    assert map_risk_score_to_level(6.50) == RiskLevel.HIGH
    assert map_risk_score_to_level(8.49) == RiskLevel.HIGH
    assert map_risk_score_to_level(8.50) == RiskLevel.CRITICAL
    assert map_risk_score_to_level(10.0) == RiskLevel.CRITICAL


def test_validation_passes_valid_output():
    """Verify that a well-formed RiskPredictionOutput passes domain validation."""
    context = _make_dummy_context()
    output = _make_valid_output()
    result = validate_risk_prediction_output(output, context)
    assert result.is_valid is True
    assert len(result.errors) == 0


def test_validation_rejects_out_of_range_score():
    """Verify validation rejects score outside [1.0, 10.0]."""
    context = _make_dummy_context()
    output = _make_valid_output()
    output.predicted_risk_score = 0.5  # < 1.0
    result = validate_risk_prediction_output(output, context)
    assert result.is_valid is False
    assert any("outside the valid target scale" in e for e in result.errors)

    output.predicted_risk_score = 10.5  # > 10.0
    result = validate_risk_prediction_output(output, context)
    assert result.is_valid is False


def test_validation_rejects_mismatched_risk_level():
    """Verify validation detects discrepancy between score and risk_level."""
    context = _make_dummy_context()
    output = _make_valid_output()
    output.predicted_risk_score = 2.0  # Should be LOW
    output.risk_level = RiskLevel.CRITICAL  # Mismatched
    result = validate_risk_prediction_output(output, context)
    assert result.is_valid is False
    assert any("does not match deterministic mapping" in e for e in result.errors)


def test_validation_rejects_missing_feature():
    """Verify validation rejects feature_summary missing an approved feature."""
    context = _make_dummy_context()
    output = _make_valid_output()
    del output.feature_summary["project_size"]
    result = validate_risk_prediction_output(output, context)
    assert result.is_valid is False
    assert any("missing required features" in e for e in result.errors)


def test_validation_rejects_empty_limitations():
    """Verify validation rejects output with empty limitations list."""
    context = _make_dummy_context()
    output = _make_valid_output()
    output.limitations = []
    result = validate_risk_prediction_output(output, context)
    assert result.is_valid is False
    assert any("limitations list cannot be empty" in e for e in result.errors)


def test_validation_rejects_prohibited_confidence_language():
    """Verify validation flags prohibited overstatement/confidence claims."""
    context = _make_dummy_context()
    
    prohibited_phrases = [
        "This is a highly accurate prediction.",
        "Model has high confidence in this estimate.",
        "This is a reliable prediction of delivery failure.",
        "The assessment is 95% confident.",
        "The system calculates 90% accurate risk.",
        "Significant chance of being risky during implementation.",
    ]

    for phrase in prohibited_phrases:
        output = _make_valid_output()
        output.summary = phrase
        result = validate_risk_prediction_output(output, context)
        assert result.is_valid is False, f"Failed to reject phrase: '{phrase}'"
        assert any("prohibited overstatement/confidence language" in e for e in result.errors)


def test_candidate_serialization():
    """Verify RiskPredictionCandidate serializes and roundtrips accurately."""
    candidate = RiskPredictionCandidate(
        summary="Candidate summary",
        predicted_risk_score=7.2,
        risk_level=RiskLevel.HIGH,
        feature_summary={"a": 1},
        model_provenance=RiskModelProvenance(
            model_name="se_risk_regressor",
            model_version="1.0.0",
            algorithm="Ridge",
            training_dataset="dataset.csv",
            feature_schema_version="1.0.0",
            artifact_checksum="c" * 64,
        ),
    )
    dump = candidate.model_dump()
    assert dump["predicted_risk_score"] == 7.2
    assert dump["risk_level"] == "HIGH"
    assert len(dump["limitations"]) == len(DEFAULT_MODEL_LIMITATIONS)
