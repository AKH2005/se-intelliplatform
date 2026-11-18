"""Unit tests for ML risk dataset validation."""

from pathlib import Path
import pandas as pd
import pytest

from app.ml.schemas.risk_features import RiskFeatureSchema
from app.ml.training.train_risk_model import validate_dataset


def _get_dataset_path() -> Path:
    backend_dir = Path(__file__).resolve().parent.parent.parent
    candidate = backend_dir / "Reduced_Software_Project_Risk_Dataset_585.csv"
    if candidate.exists():
        return candidate
    return backend_dir.parent / "Reduced_Software_Project_Risk_Dataset_585.csv"


def test_real_dataset_passes_validation():
    """Verify that the real 585-row dataset passes strict schema validation."""
    csv_path = _get_dataset_path()
    assert csv_path.exists(), f"Dataset file missing at {csv_path}"

    df = pd.read_csv(csv_path)
    assert len(df) == 585
    assert df["Project_ID"].nunique() == 585

    # Should validate without raising ValueError
    audit = validate_dataset(df)
    assert audit["rows"] == 585
    assert audit["columns"] == 12


def test_validate_dataset_rejects_missing_target():
    """Verify validate_dataset rejects DataFrame lacking target column."""
    df = pd.DataFrame({
        "Project_ID": [1, 2],
        "Project_Size": ["Small", "Large"],
        "Team_Experience_Level": ["Low", "High"],
        "Estimated_Effort_Hours": [100.0, 200.0],
        "Complexity_Level": ["Low", "High"],
        "Requirement_Stability": ["Stable", "Unstable"],
    })
    with pytest.raises(ValueError, match="Dataset shape mismatch"):
        validate_dataset(df)


def test_validate_dataset_rejects_missing_feature():
    """Verify validate_dataset rejects DataFrame missing columns."""
    df = pd.DataFrame({
        "Project_ID": [1],
        "Risk_Score": [5.0],
        "Project_Size": ["Small"],
        "Team_Experience_Level": ["Low"],
    })
    with pytest.raises(ValueError, match="Dataset shape mismatch"):
        validate_dataset(df)


def test_validate_dataset_rejects_nulls():
    """Verify validate_dataset rejects null values in predictors."""
    csv_path = _get_dataset_path()
    df = pd.read_csv(csv_path)
    df.loc[0, "Project_Size"] = None

    with pytest.raises(ValueError, match="Dataset contains missing values"):
        validate_dataset(df)


def test_validate_dataset_rejects_negative_effort():
    """Verify validate_dataset rejects non-positive effort hours."""
    root_dir = Path(__file__).resolve().parent.parent.parent.parent
    csv_path = root_dir / "Reduced_Software_Project_Risk_Dataset_585.csv"
    df = pd.read_csv(csv_path)
    df.loc[0, "Estimated_Effort_Hours"] = -10.0

    with pytest.raises(ValueError, match="positive"):
        validate_dataset(df)


def test_validate_dataset_rejects_invalid_category():
    """Verify validate_dataset rejects unknown category values."""
    root_dir = Path(__file__).resolve().parent.parent.parent.parent
    csv_path = root_dir / "Reduced_Software_Project_Risk_Dataset_585.csv"
    df = pd.read_csv(csv_path)
    df.loc[0, "Project_Size"] = "Gigantic"

    with pytest.raises(ValueError, match="Unexpected categorical values in 'Project_Size'"):
        validate_dataset(df)
