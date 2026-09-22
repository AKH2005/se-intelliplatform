"""Unit tests for Bug / Defect Prediction feature schemas and extraction engine."""

from datetime import datetime, timezone
import uuid
from pydantic import ValidationError
import pytest

from app.ml.features.bug_features import (
    BugFeatureUnavailableError,
    extract_bug_features,
)
from app.ml.schemas.bug_features import BugFeatureSchema, BugFeatureVector
from app.schemas.context import ProjectContextResponse, RequirementStatistics
from app.schemas.project import ProjectResponse


def _make_dummy_context(settings: dict | None = None) -> ProjectContextResponse:
    now = datetime.now(timezone.utc)
    return ProjectContextResponse(
        project=ProjectResponse(
            id=uuid.uuid4(),
            name="Avionics Guidance System",
            slug="avionics-guidance",
            description="High-reliability guidance subsystem",
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


@pytest.fixture
def sample_valid_bug_inputs() -> dict[str, float]:
    """Sample valid static-code metrics for a module."""
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


@pytest.fixture
def sample_context_with_bug_inputs(sample_valid_bug_inputs: dict[str, float]) -> ProjectContextResponse:
    """Canonical ProjectContextResponse containing valid ml_bug_inputs in settings."""
    return _make_dummy_context(settings={"ml_bug_inputs": sample_valid_bug_inputs})


def test_bug_feature_vector_valid(sample_valid_bug_inputs: dict[str, float]):
    """Verify valid feature vector instantiation and dictionary export."""
    vec = BugFeatureVector(**sample_valid_bug_inputs)
    assert vec.loc == 45.0
    assert vec.v_g == 7.0
    assert vec.branchCount == 13.0

    model_dict = vec.to_model_input_dict()
    assert len(model_dict) == 21
    assert model_dict["v(g)"] == 7.0
    assert model_dict["branchCount"] == 13.0
    assert "defects" not in model_dict


def test_bug_feature_vector_rejects_negative():
    """Verify BugFeatureVector rejects negative static metrics."""
    with pytest.raises(ValidationError):
        BugFeatureVector(
            loc=-1.0,
            v_g=2.0,
            ev_g=1.0,
            iv_g=1.0,
            n=10.0,
            v=10.0,
            l=1.0,
            d=1.0,
            i=1.0,
            e=1.0,
            b=1.0,
            t=1.0,
            lOCode=1.0,
            lOComment=0.0,
            lOBlank=0.0,
            locCodeAndComment=0.0,
            uniq_Op=2.0,
            uniq_Opnd=2.0,
            total_Op=5.0,
            total_Opnd=5.0,
            branchCount=1.0,
        )


def test_bug_feature_vector_rejects_non_finite(sample_valid_bug_inputs: dict[str, float]):
    """Verify BugFeatureVector rejects NaN and Inf."""
    bad_inputs = dict(sample_valid_bug_inputs)
    bad_inputs["loc"] = float("nan")
    with pytest.raises(ValidationError):
        BugFeatureVector(**bad_inputs)

    bad_inputs["loc"] = float("inf")
    with pytest.raises(ValidationError):
        BugFeatureVector(**bad_inputs)


def test_bug_feature_vector_forbids_extra_and_target(sample_valid_bug_inputs: dict[str, float]):
    """Verify BugFeatureVector rejects extra fields, specifically target 'defects'."""
    bad_inputs = dict(sample_valid_bug_inputs)
    bad_inputs["defects"] = True
    with pytest.raises(ValidationError):
        BugFeatureVector(**bad_inputs)

    bad_inputs2 = dict(sample_valid_bug_inputs)
    bad_inputs2["arbitrary_field"] = 999.0
    with pytest.raises(ValidationError):
        BugFeatureVector(**bad_inputs2)


def test_extract_bug_features_success(sample_context_with_bug_inputs: ProjectContextResponse):
    """Verify successful feature extraction from ProjectContext."""
    feature_vector = extract_bug_features(sample_context_with_bug_inputs)
    assert isinstance(feature_vector, BugFeatureVector)
    assert feature_vector.loc == 45.0
    assert feature_vector.v_g == 7.0


def test_extract_bug_features_missing_raises():
    """Verify BugFeatureUnavailableError when static-code metrics are missing."""
    empty_context = _make_dummy_context(settings={})
    with pytest.raises(BugFeatureUnavailableError) as exc_info:
        extract_bug_features(empty_context)
    assert "Required ML bug prediction features are unavailable" in str(exc_info.value)
    assert len(exc_info.value.missing_features) > 0


def test_extract_bug_features_target_leakage_raises(
    sample_context_with_bug_inputs: ProjectContextResponse,
    sample_valid_bug_inputs: dict[str, float],
):
    """Verify BugFeatureUnavailableError is raised if target 'defects' is in inputs."""
    corrupted_inputs = dict(sample_valid_bug_inputs)
    corrupted_inputs["defects"] = True
    sample_context_with_bug_inputs.project.settings = {"ml_bug_inputs": corrupted_inputs}

    with pytest.raises(BugFeatureUnavailableError, match="Target 'defects' is not an allowed feature"):
        extract_bug_features(sample_context_with_bug_inputs)
