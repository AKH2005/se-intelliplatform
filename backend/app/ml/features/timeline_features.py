"""Feature extraction engine for Timeline (Duration) Prediction model inference.

Extracts validated feature vectors from canonical Project Context without
silent imputation or uncalibrated heuristics.
"""

from typing import Any
from pydantic import ValidationError

from app.agents.exceptions import AgentValidationError
from app.ml.schemas.timeline_features import ResourceLevel, TimelineFeatureVector
from app.schemas.context import ProjectContextResponse


class TimelineFeatureUnavailableError(AgentValidationError, ValueError):
    """Raised when required runtime timeline ML features are missing from project context."""

    def __init__(self, missing_features: list[str], details: str | None = None) -> None:
        self.missing_features = missing_features
        msg = f"Required ML timeline features are unavailable in project context: {missing_features}."
        if details:
            msg += f" Details: {details}"
        super().__init__(message=msg, validation_errors=missing_features)


def extract_timeline_features(context: ProjectContextResponse) -> TimelineFeatureVector:
    """Extract and validate the 7-predictor feature vector from canonical ProjectContext.
    
    Source priority:
      1. `context.project.settings.get("ml_timeline_inputs", {})`
      2. `context.project.settings` (top-level keys)
      
    Guarantees:
      - Zero silent imputation or heuristic proxy invention.
      - If any required feature is absent or invalid, raises TimelineFeatureUnavailableError.
    """
    settings: dict[str, Any] = context.project.settings or {}
    source_dict = settings.get("ml_timeline_inputs", settings)
    if not isinstance(source_dict, dict):
        source_dict = settings

    required_keys = [
        "afp",
        "input_count",
        "output_count",
        "enquiry_count",
        "file_count",
        "interface_count",
        "resource_level",
    ]

    missing = [k for k in required_keys if source_dict.get(k) is None]
    if missing:
        raise TimelineFeatureUnavailableError(
            missing_features=missing,
            details="Configure required timeline fields in Project.settings to enable Timeline Prediction.",
        )

    try:
        raw_res = source_dict["resource_level"]
        res_val = ResourceLevel(int(raw_res)) if not isinstance(raw_res, ResourceLevel) else raw_res

        return TimelineFeatureVector(
            afp=float(source_dict["afp"]),
            input_count=float(source_dict["input_count"]),
            output_count=float(source_dict["output_count"]),
            enquiry_count=float(source_dict["enquiry_count"]),
            file_count=float(source_dict["file_count"]),
            interface_count=float(source_dict["interface_count"]),
            resource_level=res_val,
        )
    except ValidationError as ve:
        error_msgs = [f"{err['loc'][0]}: {err['msg']}" for err in ve.errors()]
        raise TimelineFeatureUnavailableError(
            missing_features=[],
            details="; ".join(error_msgs),
        ) from ve
    except (ValueError, TypeError, KeyError) as exc:
        raise TimelineFeatureUnavailableError(
            missing_features=[],
            details=f"Invalid feature values: {exc}",
        ) from exc
