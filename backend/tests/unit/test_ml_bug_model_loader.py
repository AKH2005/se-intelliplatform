"""Unit tests for Bug / Defect Prediction model loader, checksum verification, and inference."""

import json
from pathlib import Path
import pytest

from app.ml.inference.bug_model_loader import (
    BugModelChecksumMismatchError,
    BugModelLoader,
    BugModelUnavailableError,
    get_bug_model_loader,
    predict_defect,
    predict_defect_proba,
)
from app.ml.schemas.bug_features import BugFeatureVector


@pytest.fixture
def sample_bug_vector() -> BugFeatureVector:
    """Sample BugFeatureVector for loader testing."""
    return BugFeatureVector(
        loc=35.0,
        v_g=5.0,
        ev_g=2.0,
        iv_g=3.0,
        n=80.0,
        v=400.0,
        l=0.08,
        d=12.5,
        i=32.0,
        e=5000.0,
        b=0.13,
        t=277.0,
        lOCode=28.0,
        lOComment=4.0,
        lOBlank=3.0,
        locCodeAndComment=1.0,
        uniq_Op=14.0,
        uniq_Opnd=18.0,
        total_Op=50.0,
        total_Opnd=30.0,
        branchCount=9.0,
    )


def test_bug_model_loader_success(sample_bug_vector: BugFeatureVector):
    """Verify default BugModelLoader loads metadata and predicts without error."""
    loader = get_bug_model_loader()
    loader.reset_cache()

    metadata = loader.load_metadata()
    assert metadata["model_name"] == "se_bug_classifier"
    assert metadata["task"] == "binary_classification"
    assert metadata["algorithm"] == "LogisticRegression"
    assert "artifact_sha256" in metadata

    model = loader.load_model()
    assert model is not None

    # Test predict returns bool
    prediction = loader.predict(sample_bug_vector)
    assert isinstance(prediction, bool)

    # Test predict_proba returns float in [0.0, 1.0]
    prob = loader.predict_proba(sample_bug_vector)
    assert isinstance(prob, float)
    assert 0.0 <= prob <= 1.0


def test_convenience_inference_functions(sample_bug_vector: BugFeatureVector):
    """Verify predict_defect and predict_defect_proba module functions."""
    pred = predict_defect(sample_bug_vector)
    assert isinstance(pred, bool)

    proba = predict_defect_proba(sample_bug_vector)
    assert isinstance(proba, float)
    assert 0.0 <= proba <= 1.0


def test_bug_model_loader_missing_artifact(tmp_path: Path):
    """Verify BugModelUnavailableError when model artifact file is missing."""
    empty_loader = BugModelLoader(artifact_dir=tmp_path)
    with pytest.raises(BugModelUnavailableError, match="not found"):
        empty_loader.load_model()


def test_bug_model_loader_missing_metadata(tmp_path: Path):
    """Verify BugModelUnavailableError when metadata file is missing."""
    # Create empty model file but no metadata
    fake_model = tmp_path / "bug_model_v1.joblib"
    fake_model.write_bytes(b"dummy model bytes")

    loader = BugModelLoader(artifact_dir=tmp_path)
    with pytest.raises(BugModelUnavailableError, match="metadata not found"):
        loader.load_model()


def test_bug_model_loader_checksum_mismatch(tmp_path: Path):
    """Verify BugModelChecksumMismatchError when artifact SHA-256 does not match metadata."""
    fake_model = tmp_path / "bug_model_v1.joblib"
    fake_model.write_bytes(b"corrupted model content")

    fake_metadata = {
        "model_name": "se_bug_classifier",
        "model_version": "1.0.0",
        "feature_schema_version": "1.0.0",
        "artifact_sha256": "0000000000000000000000000000000000000000000000000000000000000000",
    }
    fake_meta_file = tmp_path / "bug_model_v1_metadata.json"
    fake_meta_file.write_text(json.dumps(fake_metadata), encoding="utf-8")

    loader = BugModelLoader(artifact_dir=tmp_path)
    with pytest.raises(BugModelChecksumMismatchError, match="checksum verification failed"):
        loader.load_model()


def test_bug_model_loader_schema_version_mismatch(tmp_path: Path):
    """Verify BugModelUnavailableError when metadata schema version differs from code."""
    fake_meta = {
        "model_name": "se_bug_classifier",
        "model_version": "1.0.0",
        "feature_schema_version": "9.9.9",
        "artifact_sha256": "abc",
    }
    meta_path = tmp_path / "bug_model_v1_metadata.json"
    meta_path.write_text(json.dumps(fake_meta), encoding="utf-8")

    loader = BugModelLoader(artifact_dir=tmp_path)
    with pytest.raises(BugModelUnavailableError, match="Feature schema version mismatch"):
        loader.load_metadata()
