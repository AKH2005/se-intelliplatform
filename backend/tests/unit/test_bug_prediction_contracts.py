"""Unit tests for Bug Prediction Agent contracts and deterministic validation."""

from datetime import datetime, timezone
import uuid
import pytest
from pydantic import ValidationError

from app.agents.bug_prediction.contracts import (
    DEFAULT_BUG_LIMITATIONS,
    BugModelProvenance,
    BugPredictionCandidate,
    BugPredictionOutput,
    DefectPredictionLabel,
)
from app.agents.bug_prediction.validation import validate_bug_prediction_output
from app.ml.schemas.bug_features import BugFeatureSchema
from app.schemas.context import ProjectContextResponse, RequirementStatistics
from app.schemas.project import ProjectResponse


def _make_dummy_context() -> ProjectContextResponse:
    now = datetime.now(timezone.utc)
    return ProjectContextResponse(
        project=ProjectResponse(
            id=uuid.uuid4(),
            name="Bug Test Project",
            slug="bug-test-project",
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


def _make_valid_feature_summary() -> dict[str, float]:
    return {
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


def _make_valid_output(
    summary: str = "Module defect susceptibility is evaluated as DEFECTIVE with a raw model positive-class probability estimate of 0.6521.",
    predicted_probability: float = 0.6521,
    prediction_label: DefectPredictionLabel = DefectPredictionLabel.DEFECTIVE,
) -> BugPredictionOutput:
    return BugPredictionOutput(
        agent_id="bug-prediction",
        agent_version="1.0.0",
        summary=summary,
        prediction_label=prediction_label,
        predicted_probability=predicted_probability,
        target="defects",
        model_provenance=BugModelProvenance(
            model_name="se_bug_classifier",
            model_version="1.0.0",
            algorithm="LogisticRegression",
            training_dataset="JM1",
            feature_schema_version="1.0.0",
            artifact_checksum="563b2b0ffd522df7ff8f50b0a025a9e64a678fb917ac7bbddc2f15e2035e430e",
        ),
        feature_names=list(BugFeatureSchema.APPROVED_FEATURES),
        feature_summary=_make_valid_feature_summary(),
        limitations=list(DEFAULT_BUG_LIMITATIONS),
    )


def test_valid_bug_prediction_candidate_creation():
    """Verify BugPredictionCandidate instantiated with required fields."""
    cand = BugPredictionCandidate(
        summary="Empirical defect prediction assessment.",
        prediction_label=DefectPredictionLabel.NON_DEFECTIVE,
        predicted_probability=0.2145,
        target="defects",
        model_provenance=BugModelProvenance(
            model_name="se_bug_classifier",
            model_version="1.0.0",
            algorithm="LogisticRegression",
            training_dataset="JM1",
            feature_schema_version="1.0.0",
            artifact_checksum="563b2b0ffd522df7ff8f50b0a025a9e64a678fb917ac7bbddc2f15e2035e430e",
        ),
        feature_names=list(BugFeatureSchema.APPROVED_FEATURES),
        feature_summary=_make_valid_feature_summary(),
    )
    assert cand.prediction_label == DefectPredictionLabel.NON_DEFECTIVE
    assert cand.predicted_probability == 0.2145
    assert len(cand.limitations) >= 3


def test_candidate_extra_fields_forbidden():
    """Verify extra attributes are forbidden in contracts."""
    with pytest.raises(ValidationError):
        BugPredictionCandidate(
            summary="test",
            prediction_label=DefectPredictionLabel.DEFECTIVE,
            predicted_probability=0.5,
            target="defects",
            model_provenance=BugModelProvenance(
                model_name="se_bug_classifier",
                model_version="1.0.0",
                algorithm="LogisticRegression",
                training_dataset="JM1",
                feature_schema_version="1.0.0",
                artifact_checksum="563b2b0ffd522df7ff8f50b0a025a9e64a678fb917ac7bbddc2f15e2035e430e",
            ),
            feature_names=list(BugFeatureSchema.APPROVED_FEATURES),
            feature_summary=_make_valid_feature_summary(),
            unauthorized_key="malicious",
        )


def test_validate_bug_prediction_output_success():
    """Verify authoritative validation passes on valid output."""
    context = _make_dummy_context()
    output = _make_valid_output()
    result = validate_bug_prediction_output(output, context)
    assert result.is_valid
    assert len(result.errors) == 0


def test_validate_bug_prediction_invalid_probability():
    """Verify validation fails on negative or >1.0 or non-finite probability."""
    context = _make_dummy_context()

    # Negative probability
    bad_prob_out = _make_valid_output(predicted_probability=-0.1)
    res = validate_bug_prediction_output(bad_prob_out, context)
    assert not res.is_valid
    assert any("predicted_probability must be between 0.0 and 1.0" in err for err in res.errors)

    # >1.0 probability
    bad_prob_out2 = _make_valid_output(predicted_probability=1.5)
    res2 = validate_bug_prediction_output(bad_prob_out2, context)
    assert not res2.is_valid
    assert any("predicted_probability must be between 0.0 and 1.0" in err for err in res2.errors)


def test_validate_bug_prediction_invalid_target():
    """Verify validation fails if target is not 'defects'."""
    context = _make_dummy_context()
    output = _make_valid_output()
    output.target = "bugs_count"
    res = validate_bug_prediction_output(output, context)
    assert not res.is_valid
    assert any("target must be 'defects'" in err for err in res.errors)


def test_validate_bug_prediction_feature_names_mismatch():
    """Verify validation fails if feature_names does not match 21 approved predictors."""
    context = _make_dummy_context()
    output = _make_valid_output()
    output.feature_names = ["loc", "v(g)"]  # Incomplete
    res = validate_bug_prediction_output(output, context)
    assert not res.is_valid
    assert any("feature_names does not match approved predictors" in err for err in res.errors)


def test_validate_bug_prediction_feature_summary_incomplete():
    """Verify validation fails if feature_summary lacks required features."""
    context = _make_dummy_context()
    output = _make_valid_output()
    output.feature_summary = {"loc": 10.0}  # Missing 20 features
    res = validate_bug_prediction_output(output, context)
    assert not res.is_valid
    assert any("feature_summary is missing required keys" in err for err in res.errors)


def test_validate_bug_prediction_model_provenance_mismatch():
    """Verify validation fails if model provenance is inaccurate."""
    context = _make_dummy_context()
    output = _make_valid_output()
    output.model_provenance.algorithm = "RandomForestClassifier"  # Mismatch
    res = validate_bug_prediction_output(output, context)
    assert not res.is_valid
    assert any("model_provenance.algorithm must be 'LogisticRegression'" in err for err in res.errors)


def test_validate_bug_prediction_prohibited_language():
    """Verify validation rejects prohibited overstatement/confidence language."""
    context = _make_dummy_context()

    prohibited_phrases = [
        "This is a highly accurate defect prediction.",
        "Delivers high confidence defect classification.",
        "Guaranteed zero defects in production.",
        "Production-grade defect detection system.",
        "Provides 100% accurate prediction.",
    ]

    for phrase in prohibited_phrases:
        output = _make_valid_output(summary=phrase)
        res = validate_bug_prediction_output(output, context)
        assert not res.is_valid
        assert any("prohibited overstatement/confidence language" in err for err in res.errors)
