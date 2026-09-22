"""Unit tests for JM1 Bug / Defect Prediction dataset validation and duplicate policy."""

from pathlib import Path
import pandas as pd
import pytest

from app.ml.schemas.bug_features import BugFeatureSchema
from app.ml.training.train_bug_model import (
    deduplicate_dataset,
    find_dataset_path,
    load_dataset,
    validate_dataset,
)


@pytest.fixture(scope="module")
def jm1_dataframe() -> pd.DataFrame:
    """Load JM1 dataset for testing."""
    path = find_dataset_path()
    return load_dataset(path)


def test_find_dataset_path_success():
    """Verify JM1 dataset is located in standard locations."""
    path = find_dataset_path()
    assert path.exists()
    assert path.suffix.lower() == ".arff"


def test_find_dataset_path_nonexistent():
    """Verify FileNotFoundError on non-existent custom path."""
    with pytest.raises(FileNotFoundError, match="Specified dataset path does not exist"):
        find_dataset_path(Path("non_existent_dataset.arff"))


def test_dataset_schema_and_dimensions(jm1_dataframe: pd.DataFrame):
    """Verify raw JM1 dataset row count and attribute structure."""
    assert len(jm1_dataframe) == 10885
    assert len(jm1_dataframe.columns) == 22
    assert BugFeatureSchema.TARGET_COLUMN in jm1_dataframe.columns

    for feature in BugFeatureSchema.APPROVED_FEATURES:
        assert feature in jm1_dataframe.columns


def test_dataset_target_binary_domain(jm1_dataframe: pd.DataFrame):
    """Verify target column contains only binary labels 'false' and 'true'."""
    unique_values = set(jm1_dataframe[BugFeatureSchema.TARGET_COLUMN].dropna().unique())
    assert unique_values == {"false", "true"}


def test_dataset_audit_validation(jm1_dataframe: pd.DataFrame):
    """Verify dataset audit calculation."""
    audit = validate_dataset(jm1_dataframe)
    assert audit["original_rows"] == 10885
    assert audit["original_cols"] == 22
    assert audit["exact_duplicates"] == 1973
    assert audit["feature_duplicates"] >= 1973
    assert audit["class_distribution_raw"]["false"] == 8779
    assert audit["class_distribution_raw"]["true"] == 2106
    assert len(audit["constant_features"]) == 0

    # 5 features with missing values
    assert len(audit["missing_values"]) == 5
    for col in ["uniq_Op", "uniq_Opnd", "total_Op", "total_Opnd", "branchCount"]:
        assert audit["missing_values"][col] == 5


def test_exact_duplicate_policy_removal(jm1_dataframe: pd.DataFrame):
    """Verify exact duplicate rows are removed prior to splitting."""
    df_dedup, removed = deduplicate_dataset(jm1_dataframe)
    assert removed == 1973
    assert len(df_dedup) == 8912

    # Verify no exact duplicates remain
    assert df_dedup.duplicated().sum() == 0


def test_feature_only_duplicate_preservation():
    """Verify that identical features with differing defect labels are preserved."""
    test_data = pd.DataFrame([
        {"loc": 10.0, "v(g)": 2.0, "defects": "false"},
        {"loc": 10.0, "v(g)": 2.0, "defects": "false"},  # exact duplicate -> drop
        {"loc": 10.0, "v(g)": 2.0, "defects": "true"},   # different label -> retain!
    ])
    deduped, removed = deduplicate_dataset(test_data)
    assert removed == 1
    assert len(deduped) == 2
    assert set(deduped["defects"]) == {"false", "true"}


def test_target_leakage_exclusion():
    """Regression test: Target 'defects' must NEVER be part of the approved predictor list."""
    assert "defects" not in BugFeatureSchema.APPROVED_FEATURES
    assert "defects" not in BugFeatureSchema.NUMERICAL_FEATURES
    assert "defects" in BugFeatureSchema.EXCLUDED_LEAKAGE_FEATURES
    assert len(BugFeatureSchema.APPROVED_FEATURES) == 21


def test_validate_dataset_missing_target_raises():
    """Verify validate_dataset raises ValueError when target column is missing."""
    df_corrupt = pd.DataFrame({"loc": [10.0, 20.0]})
    with pytest.raises(ValueError, match="Target column 'defects' not found"):
        validate_dataset(df_corrupt)


def test_validate_dataset_invalid_target_values_raises():
    """Verify validate_dataset raises ValueError on unexpected target values."""
    df_bad_target = pd.DataFrame({
        f: [1.0] for f in BugFeatureSchema.APPROVED_FEATURES
    })
    df_bad_target["defects"] = ["maybe"]
    with pytest.raises(ValueError, match="Unexpected target values in 'defects'"):
        validate_dataset(df_bad_target)
