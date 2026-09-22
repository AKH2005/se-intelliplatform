"""Feature extraction engine for Risk Prediction model inference.

Extracts validated feature vectors from canonical Project Context without
silent imputation or uncalibrated heuristics.
"""

from typing import Any
from pydantic import ValidationError

from app.ml.schemas.risk_features import (
    ComplexityLevel,
    ProjectSize,
    RequirementStability,
    RiskFeatureVector,
    TeamExperienceLevel,
)
from app.agents.exceptions import AgentValidationError
from app.schemas.context import ProjectContextResponse


class MLFeatureUnavailableError(AgentValidationError, ValueError):
    """Raised when required runtime ML features are missing from project context."""

    def __init__(self, missing_features: list[str], details: str | None = None) -> None:
        self.missing_features = missing_features
        msg = f"Required ML risk features are unavailable in project context: {missing_features}."
        if details:
            msg += f" Details: {details}"
        super().__init__(message=msg, validation_errors=missing_features)


def extract_risk_features(context: ProjectContextResponse) -> RiskFeatureVector:
    """Extract and validate the 5-predictor feature vector from canonical ProjectContext.
    
    Source priority:
      1. `context.project.settings.get("ml_risk_inputs", {})`
      2. `context.project.settings` (top-level keys)
      
    Guarantees:
      - Zero silent imputation or heuristic proxy invention.
      - If any required feature is absent or invalid, raises MLFeatureUnavailableError.
    """
    settings: dict[str, Any] = context.project.settings or {}
    source_dict = settings.get("ml_risk_inputs", settings)
    if not isinstance(source_dict, dict):
        source_dict = settings

    required_keys = [
        "project_size",
        "team_experience_level",
        "estimated_effort_hours",
        "complexity_level",
        "requirement_stability",
    ]

    missing = [k for k in required_keys if source_dict.get(k) is None]
    if missing:
        raise MLFeatureUnavailableError(
            missing_features=missing,
            details="Configure required ML fields in Project.settings to enable Risk Prediction.",
        )

    try:
        return RiskFeatureVector(
            project_size=source_dict["project_size"],
            team_experience_level=source_dict["team_experience_level"],
            estimated_effort_hours=float(source_dict["estimated_effort_hours"]),
            complexity_level=source_dict["complexity_level"],
            requirement_stability=source_dict["requirement_stability"],
        )
    except ValidationError as ve:
        error_msgs = [f"{err['loc'][0]}: {err['msg']}" for err in ve.errors()]
        raise MLFeatureUnavailableError(
            missing_features=[],
            details="; ".join(error_msgs),
        ) from ve
    except (ValueError, TypeError) as exc:
        raise MLFeatureUnavailableError(
            missing_features=[],
            details=f"Invalid feature values: {exc}",
        ) from exc
