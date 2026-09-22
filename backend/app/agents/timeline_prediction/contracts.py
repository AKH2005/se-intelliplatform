"""Contracts and Data Models for Timeline Prediction Agent."""

from typing import Any
from pydantic import BaseModel, ConfigDict, Field

# Canonical limitations derived from the Phase 7B.0 training report
DEFAULT_TIMELINE_LIMITATIONS = [
    "The model is an empirical duration-estimation model trained on 499 historical China software projects. Its held-out test R² is 0.2362 and MAE is 4.5926 months. It should be treated as an advisory point estimate, not a guaranteed project deadline.",
    "Predictions reflect empirical functional size associations within historical datasets and do not imply direct causal levers.",
    "A substantial portion of timeline variance is governed by organizational, process, and team factors not captured in function point metrics.",
    "The continuous point estimate represents expected elapsed months, not a contractually binding project management deadline.",
    "Runtime feature definitions must remain strictly compatible with the China dataset function point metrics.",
]


class TimelineModelProvenance(BaseModel):
    """Authoritative metadata describing the trained Timeline ML model artifact."""

    model_config = ConfigDict(extra="forbid")

    model_name: str = Field(..., description="Registered model identifier")
    model_version: str = Field(..., description="Semantic version of the model artifact")
    algorithm: str = Field(..., description="Scikit-learn estimator algorithm name")
    training_dataset: str = Field(..., description="Dataset name used for training")
    feature_schema_version: str = Field(..., description="Version of the feature schema contract")
    artifact_checksum: str = Field(..., description="SHA-256 byte checksum of the joblib artifact")


class TimelinePredictionCandidate(BaseModel):
    """Raw candidate prediction produced by the Timeline model before final validation."""

    model_config = ConfigDict(extra="forbid")

    agent_id: str = Field(default="timeline-prediction", description="Predicting agent identifier")
    agent_version: str = Field(default="1.0.0", description="Predicting agent version")
    summary: str = Field(..., description="Descriptive summary of the timeline duration assessment")
    predicted_duration_months: float = Field(..., description="Raw continuous predicted duration in elapsed months")
    estimated_duration_months: float = Field(..., description="Presentation rounded duration estimate in months")
    target: str = Field(default="Duration", description="Target metric name")
    target_unit: str = Field(default="months", description="Target unit of measurement")
    model_provenance: TimelineModelProvenance = Field(..., description="Authoritative model provenance metadata")
    feature_names: list[str] = Field(..., description="List of approved feature names evaluated by model")
    feature_summary: dict[str, Any] = Field(..., description="Human-readable validated input features")
    limitations: list[str] = Field(
        default_factory=lambda: list(DEFAULT_TIMELINE_LIMITATIONS),
        description="Acknowledged model limitations",
    )


class TimelinePredictionOutput(BaseModel):
    """Authoritative, validated structured result emitted by TimelinePredictionAgent."""

    model_config = ConfigDict(extra="forbid")

    agent_id: str = Field(default="timeline-prediction", description="Predicting agent identifier")
    agent_version: str = Field(default="1.0.0", description="Predicting agent version")
    summary: str = Field(..., description="Descriptive summary of the timeline duration assessment")
    predicted_duration_months: float = Field(..., description="Continuous predicted duration in elapsed months")
    estimated_duration_months: float = Field(..., description="Presentation rounded duration estimate in months")
    target: str = Field(default="Duration", description="Target metric name")
    target_unit: str = Field(default="months", description="Target unit of measurement")
    model_provenance: TimelineModelProvenance = Field(..., description="Authoritative model provenance metadata")
    feature_names: list[str] = Field(..., description="List of approved feature names evaluated by model")
    feature_summary: dict[str, Any] = Field(..., description="Human-readable validated input features")
    limitations: list[str] = Field(..., description="Acknowledged model limitations")
