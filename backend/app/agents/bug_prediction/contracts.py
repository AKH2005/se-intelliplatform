"""Contracts and Data Models for Bug / Defect Prediction Agent."""

import enum
from typing import Any
from pydantic import BaseModel, ConfigDict, Field

# Canonical limitations derived from the Phase 7C.0 training report
DEFAULT_BUG_LIMITATIONS = [
    (
        "This prediction is an ML-based defect classification signal trained on the NASA JM1 static-code dataset. "
        "Held-out test performance is moderate (Recall: 0.4851, F1: 0.4333, PR-AUC: 0.4254, ROC-AUC: 0.6915). "
        "It should be treated as an advisory quality indicator, not a guarantee that a module is defective or defect-free."
    ),
    (
        "Predictions reflect empirical static metric associations within historical NASA flight software "
        "and do not establish direct causality or guarantee runtime reliability."
    ),
    (
        "The predicted probability represents the classifier's raw positive-class probability estimate. "
        "It is not a certainty score, business confidence rating, or severity indicator."
    ),
    (
        "Static code metrics capture syntactic and structural complexity (McCabe, Halstead, line counts), "
        "not runtime execution correctness, domain logic validity, or developer competency."
    ),
    (
        "Runtime feature definitions must remain strictly compatible with the 21 approved NASA JM1 static-code metrics."
    ),
]


class DefectPredictionLabel(str, enum.Enum):
    """Categorical classification of module defect status."""

    DEFECTIVE = "DEFECTIVE"
    NON_DEFECTIVE = "NON_DEFECTIVE"


class BugModelProvenance(BaseModel):
    """Authoritative metadata describing the trained Bug ML model artifact."""

    model_config = ConfigDict(extra="forbid")

    model_name: str = Field(..., description="Registered model identifier")
    model_version: str = Field(..., description="Semantic version of the model artifact")
    algorithm: str = Field(..., description="Scikit-learn estimator algorithm name")
    training_dataset: str = Field(..., description="Dataset name used for training")
    feature_schema_version: str = Field(..., description="Version of the feature schema contract")
    artifact_checksum: str = Field(..., description="SHA-256 byte checksum of the joblib artifact")


class BugPredictionCandidate(BaseModel):
    """Raw candidate prediction produced by the Bug model before final validation."""

    model_config = ConfigDict(extra="forbid")

    agent_id: str = Field(default="bug-prediction", description="Predicting agent identifier")
    agent_version: str = Field(default="1.0.0", description="Predicting agent version")
    summary: str = Field(..., description="Descriptive summary of the defect prediction assessment")
    prediction_label: DefectPredictionLabel = Field(..., description="Defect classification (DEFECTIVE or NON_DEFECTIVE)")
    predicted_probability: float = Field(..., description="Classifier's raw positive-class probability estimate in [0.0, 1.0]")
    target: str = Field(default="defects", description="Target metric name")
    model_provenance: BugModelProvenance = Field(..., description="Authoritative model provenance metadata")
    feature_names: list[str] = Field(..., description="List of approved feature names evaluated by model")
    feature_summary: dict[str, float] = Field(..., description="Human-readable validated input features")
    limitations: list[str] = Field(
        default_factory=lambda: list(DEFAULT_BUG_LIMITATIONS),
        description="Acknowledged model limitations",
    )


class BugPredictionOutput(BaseModel):
    """Authoritative, validated structured result emitted by BugPredictionAgent."""

    model_config = ConfigDict(extra="forbid")

    agent_id: str = Field(default="bug-prediction", description="Predicting agent identifier")
    agent_version: str = Field(default="1.0.0", description="Predicting agent version")
    summary: str = Field(..., description="Descriptive summary of the defect prediction assessment")
    prediction_label: DefectPredictionLabel = Field(..., description="Defect classification (DEFECTIVE or NON_DEFECTIVE)")
    predicted_probability: float = Field(..., description="Classifier's raw positive-class probability estimate in [0.0, 1.0]")
    target: str = Field(default="defects", description="Target metric name")
    model_provenance: BugModelProvenance = Field(..., description="Authoritative model provenance metadata")
    feature_names: list[str] = Field(..., description="List of approved feature names evaluated by model")
    feature_summary: dict[str, float] = Field(..., description="Human-readable validated input features")
    limitations: list[str] = Field(..., description="Acknowledged model limitations")
