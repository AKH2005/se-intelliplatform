"""Unit tests for Timeline Prediction model loader and inference."""

import json
from pathlib import Path
import pytest

from app.ml.inference.timeline_model_loader import (
    TimelineModelChecksumMismatchError,
    TimelineModelLoader,
    TimelineModelUnavailableError,
    get_timeline_model_loader,
    predict_duration,
)
from app.ml.schemas.timeline_features import ResourceLevel, TimelineFeatureVector


@pytest.fixture(autouse=True)
def reset_loader_cache():
    """Reset the singleton cache before and after tests."""
    loader = get_timeline_model_loader()
    loader.reset_cache()
    yield
    loader.reset_cache()


def test_timeline_model_loader_success():
    """Verify that the trained timeline model loads successfully and matches metadata checksum."""
    loader = get_timeline_model_loader()
    metadata = loader.load_metadata()
    pipeline = loader.load_model()
    assert pipeline is not None
    assert metadata["model_name"] == "se_timeline_regressor"
    assert metadata["task"] == "regression"
    assert metadata["target"] == "Duration"
    assert metadata["target_unit"] == "months"
    assert "sha256_checksum" in metadata


def test_predict_duration_returns_valid_float():
    """Verify predict_duration produces a positive continuous float (months)."""
    vector = TimelineFeatureVector(
        afp=300.0,
        input_count=35.0,
        output_count=25.0,
        enquiry_count=15.0,
        file_count=10.0,
        interface_count=2.0,
        resource_level=ResourceLevel.LEVEL_1,
    )
    duration = predict_duration(vector)
    assert isinstance(duration, float)
    assert duration > 0.0


def test_timeline_model_loader_detects_checksum_mismatch(tmp_path):
    """Verify TimelineModelChecksumMismatchError is raised when file bytes are tampered."""
    fake_joblib = tmp_path / "timeline_model_v1.joblib"
    fake_metadata = tmp_path / "timeline_model_v1_metadata.json"

    # Write corrupted file
    fake_joblib.write_bytes(b"tampered timeline artifact")
    meta = {
        "model_name": "se_timeline_regressor",
        "feature_schema_version": "1.0.0",
        "sha256_checksum": "0000000000000000000000000000000000000000000000000000000000000000",
    }
    fake_metadata.write_text(json.dumps(meta))

    loader = TimelineModelLoader(
        artifact_dir=tmp_path,
        model_filename="timeline_model_v1.joblib",
        metadata_filename="timeline_model_v1_metadata.json",
    )
    with pytest.raises(TimelineModelChecksumMismatchError):
        loader.load_model()


def test_timeline_model_loader_detects_missing_file(tmp_path):
    """Verify TimelineModelUnavailableError is raised when files are missing."""
    loader = TimelineModelLoader(
        artifact_dir=tmp_path,
        model_filename="non_existent.joblib",
        metadata_filename="non_existent.json",
    )
    with pytest.raises(TimelineModelUnavailableError):
        loader.load_model()
