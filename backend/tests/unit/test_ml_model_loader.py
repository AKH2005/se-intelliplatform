"""Unit tests for ML risk model loader and inference."""

import json
from pathlib import Path
import pytest

from app.ml.inference.model_loader import (
    ModelChecksumMismatchError,
    ModelUnavailableError,
    RiskModelLoader,
    get_risk_model_loader,
    predict_risk,
)
from app.ml.schemas.risk_features import (
    ComplexityLevel,
    ProjectSize,
    RequirementStability,
    RiskFeatureVector,
    TeamExperienceLevel,
)


@pytest.fixture(autouse=True)
def reset_loader_cache():
    """Reset the singleton cache before and after tests."""
    loader = get_risk_model_loader()
    loader.reset_cache()
    yield
    loader.reset_cache()


def test_model_loader_success():
    """Verify that the trained model loads successfully and matches metadata checksum."""
    loader = get_risk_model_loader()
    metadata = loader.load_metadata()
    pipeline = loader.load_model()
    assert pipeline is not None
    assert metadata["model_name"] == "se_risk_regressor"
    assert metadata["task"] == "regression"
    assert metadata["target"] == "Risk_Score"
    assert "sha256_checksum" in metadata


def test_predict_risk_returns_valid_float():
    """Verify predict_risk produces a continuous float output."""
    vector = RiskFeatureVector(
        project_size=ProjectSize.MEDIUM,
        team_experience_level=TeamExperienceLevel.HIGH,
        estimated_effort_hours=750.0,
        complexity_level=ComplexityLevel.LOW,
        requirement_stability=RequirementStability.STABLE,
    )
    score = predict_risk(vector)
    assert isinstance(score, float)
    assert 1.0 <= score <= 10.0


def test_model_loader_detects_checksum_mismatch(tmp_path):
    """Verify ModelChecksumMismatchError is raised when file bytes are tampered."""
    fake_joblib = tmp_path / "risk_model_v1.joblib"
    fake_metadata = tmp_path / "risk_model_v1_metadata.json"

    # Write corrupt dummy file
    fake_joblib.write_bytes(b"tampered content")
    # Write metadata with mismatched hash
    meta = {
        "model_name": "se_risk_regressor",
        "feature_schema_version": "1.0.0",
        "sha256_checksum": "0000000000000000000000000000000000000000000000000000000000000000",
    }
    fake_metadata.write_text(json.dumps(meta))

    loader = RiskModelLoader(
        artifact_dir=tmp_path,
        model_filename="risk_model_v1.joblib",
        metadata_filename="risk_model_v1_metadata.json",
    )
    with pytest.raises(ModelChecksumMismatchError):
        loader.load_model()


def test_model_loader_detects_missing_file(tmp_path):
    """Verify ModelUnavailableError is raised when files are missing."""
    loader = RiskModelLoader(
        artifact_dir=tmp_path,
        model_filename="non_existent.joblib",
        metadata_filename="non_existent.json",
    )
    with pytest.raises(ModelUnavailableError):
        loader.load_model()
