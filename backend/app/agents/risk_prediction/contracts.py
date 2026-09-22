"""Contracts and Data Models for Risk Prediction Agent."""

import enum
from typing import Any
from pydantic import BaseModel, ConfigDict, Field


class RiskLevel(str, enum.Enum):
    """Categorical risk band mapped from continuous predicted risk score.
    
    CRITICAL POLICY:
    These threshold boundaries represent deterministic APPLICATION POLICY,
    not an ML classification output or learned statistical property.
    """
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


# Deterministic application policy thresholds for risk band mapping
# Scale: approximately 1.0 – 10.0 (derived from dataset target distribution)
RISK_THRESHOLD_LOW_MAX = 3.5
RISK_THRESHOLD_MEDIUM_MAX = 6.5
RISK_THRESHOLD_HIGH_MAX = 8.5


def map_risk_score_to_level(score: float) -> RiskLevel:
    """Map a continuous predicted risk score to a categorical RiskLevel.
    
    Application Policy:
      - score < 3.5: LOW
      - 3.5 <= score < 6.5: MEDIUM
      - 6.5 <= score < 8.5: HIGH
      - score >= 8.5: CRITICAL
    """
    if score < RISK_THRESHOLD_LOW_MAX:
        return RiskLevel.LOW
    elif score < RISK_THRESHOLD_MEDIUM_MAX:
        return RiskLevel.MEDIUM
    elif score < RISK_THRESHOLD_HIGH_MAX:
        return RiskLevel.HIGH
    else:
        return RiskLevel.CRITICAL


# Canonical limitations derived from the Phase 7A.0 training report
DEFAULT_MODEL_LIMITATIONS = [
    "Dataset size is limited to 585 historical software development projects.",
    "Training dataset is external to SE IntelliPlatform and may exhibit differing domain dynamics.",
    "Current model exhibits weak predictive performance (Test R² = -0.0087, Test MAE = 2.1999 vs Dummy MAE = 2.2511).",
    "Test R² is negative, indicating marginal improvement over a constant mean baseline.",
    "Historical training performance does not guarantee real-world generalization on SE IntelliPlatform projects.",
    "Runtime feature definitions must remain strictly compatible with the training dataset schema.",
]


class RiskModelProvenance(BaseModel):
    """Authoritative metadata describing the trained ML model artifact."""

    model_config = ConfigDict(extra="forbid")

    model_name: str = Field(..., description="Registered model identifier")
    model_version: str = Field(..., description="Semantic version of the model artifact")
    algorithm: str = Field(..., description="Scikit-learn estimator algorithm name")
    training_dataset: str = Field(..., description="Dataset filename used for training")
    feature_schema_version: str = Field(..., description="Version of the feature schema contract")
    artifact_checksum: str = Field(..., description="SHA-256 byte checksum of the joblib artifact")


class RiskPredictionCandidate(BaseModel):
    """Raw candidate prediction produced by the ML model before final validation."""

    model_config = ConfigDict(extra="forbid")

    summary: str = Field(..., description="Descriptive summary of the risk assessment")
    predicted_risk_score: float = Field(..., description="Raw continuous predicted risk score")
    risk_level: RiskLevel = Field(..., description="Deterministic categorical risk band")
    feature_summary: dict[str, Any] = Field(..., description="Human-readable validated input features")
    model_provenance: RiskModelProvenance = Field(..., description="Authoritative model provenance metadata")
    limitations: list[str] = Field(default_factory=lambda: list(DEFAULT_MODEL_LIMITATIONS), description="Acknowledged model limitations")


class RiskPredictionOutput(BaseModel):
    """Authoritative, validated structured result emitted by RiskPredictionAgent."""

    model_config = ConfigDict(extra="forbid")

    summary: str = Field(..., description="Descriptive summary of the risk assessment")
    predicted_risk_score: float = Field(..., description="Continuous predicted risk score on 1.0 - 10.0 scale")
    risk_level: RiskLevel = Field(..., description="Deterministic categorical risk band")
    feature_summary: dict[str, Any] = Field(..., description="Human-readable validated input features")
    model_provenance: RiskModelProvenance = Field(..., description="Authoritative model provenance metadata")
    limitations: list[str] = Field(..., description="Acknowledged model limitations")
