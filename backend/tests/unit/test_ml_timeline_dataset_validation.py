"""Unit tests for China dataset validation and leakage exclusion in Timeline Prediction."""

from pathlib import Path
import pandas as pd
import pytest

from app.ml.schemas.timeline_features import TimelineFeatureSchema
from app.ml.training.train_timeline_model import (
    find_dataset_path,
    load_dataset,
    validate_dataset,
)


def test_real_dataset_passes_validation():
    """Verify that the real China dataset passes strict validation."""
    data_path = find_dataset_path()
    assert data_path.exists(), f"China dataset missing at {data_path}"

    df = load_dataset(data_path)
    assert len(df) == 499
    assert df["ID"].nunique() == 499

    audit = validate_dataset(df)
    assert audit["rows"] == 499
    assert audit["columns"] == 19
    assert audit["duplicate_rows"] == 0
    assert audit["duplicate_ids"] == 0
    assert audit["target_stats"]["min"] >= 1.0


def test_validate_dataset_rejects_missing_target():
    """Verify validate_dataset rejects DataFrame lacking Duration column."""
    data_path = find_dataset_path()
    df = load_dataset(data_path).drop(columns=["Duration"])
    with pytest.raises(ValueError, match="Dataset shape mismatch"):
        validate_dataset(df)


def test_validate_dataset_rejects_missing_feature():
    """Verify validate_dataset rejects DataFrame missing approved features."""
    data_path = find_dataset_path()
    df = load_dataset(data_path).drop(columns=["AFP"])
    with pytest.raises(ValueError, match="Dataset shape mismatch"):
        validate_dataset(df)


def test_validate_dataset_rejects_nulls():
    """Verify validate_dataset rejects null values."""
    data_path = find_dataset_path()
    df = load_dataset(data_path)
    df.loc[0, "AFP"] = None
    with pytest.raises(ValueError, match="Dataset contains missing values"):
        validate_dataset(df)


def test_validate_dataset_rejects_non_positive_duration():
    """Verify validate_dataset rejects zero or negative Duration values."""
    data_path = find_dataset_path()
    df = load_dataset(data_path)
    df.loc[0, "Duration"] = 0.0
    with pytest.raises(ValueError, match="Duration target contains zero or negative values"):
        validate_dataset(df)

    df.loc[0, "Duration"] = -2.5
    with pytest.raises(ValueError, match="Duration target contains zero or negative values"):
        validate_dataset(df)


def test_validate_dataset_rejects_invalid_resource():
    """Verify validate_dataset rejects unknown Resource categorical levels."""
    data_path = find_dataset_path()
    df = load_dataset(data_path)
    df.loc[0, "Resource"] = 99.0
    with pytest.raises(ValueError, match="Resource contains invalid levels"):
        validate_dataset(df)


def test_leakage_features_not_in_approved_features():
    """Verify strict separation between approved predictors and leakage/excluded variables."""
    approved = set(TimelineFeatureSchema.APPROVED_FEATURES)
    excluded = set(TimelineFeatureSchema.EXCLUDED_LEAKAGE_FEATURES)

    # Intersection must be completely empty
    intersection = approved & excluded
    assert len(intersection) == 0, f"Found leakage features in approved features: {intersection}"

    # Critical leakage fields must be explicitly excluded
    assert "Effort" in excluded
    assert "N_effort" in excluded
    assert "PDR_AFP" in excluded
    assert "Changed" in excluded
    assert "Deleted" in excluded
    assert "Dev.Type" in excluded
