"""Feature extraction engine for Bug / Defect Prediction model inference.

Extracts validated feature vectors from canonical Project Context without
silent imputation, arbitrary defaults, or heuristic proxy metrics.
"""

from typing import Any
from pydantic import ValidationError

from app.agents.exceptions import AgentValidationError
from app.ml.schemas.bug_features import BugFeatureSchema, BugFeatureVector
from app.schemas.context import ProjectContextResponse


class BugFeatureUnavailableError(AgentValidationError, ValueError):
    """Raised when required runtime static-code metrics are missing from project context."""

    def __init__(self, missing_features: list[str], details: str | None = None) -> None:
        self.missing_features = missing_features
        msg = f"Required ML bug prediction features are unavailable in project context: {missing_features}."
        if details:
            msg += f" Details: {details}"
        super().__init__(message=msg, validation_errors=missing_features)


def extract_bug_features(context: ProjectContextResponse) -> BugFeatureVector:
    """Extract and validate the 21-predictor static-code metric feature vector from ProjectContext.

    Source priority:
      1. `context.project.settings.get("ml_bug_inputs", {})`
      2. `context.project.settings` (top-level keys)

    Guarantees:
      - Zero silent imputation or heuristic proxy invention from requirements, effort, or size.
      - If any required feature is absent, raises BugFeatureUnavailableError.
      - If target 'defects' is supplied, raises BugFeatureUnavailableError (leakage prevention).
    """
    settings: dict[str, Any] = context.project.settings or {}
    source_dict = settings.get("ml_bug_inputs", settings)
    if not isinstance(source_dict, dict):
        source_dict = settings

    # Leakage check: target 'defects' must never be supplied as an input feature
    if "defects" in source_dict:
        raise BugFeatureUnavailableError(
            missing_features=[],
            details="Target 'defects' is not an allowed feature and cannot enter the input vector.",
        )

    # Check for presence of all 21 approved metrics (accepting either alias or field name)
    missing: list[str] = []
    vector_payload: dict[str, Any] = {}

    alias_mapping = {
        "loc": ["loc"],
        "v(g)": ["v(g)", "v_g"],
        "ev(g)": ["ev(g)", "ev_g"],
        "iv(g)": ["iv(g)", "iv_g"],
        "n": ["n"],
        "v": ["v"],
        "l": ["l"],
        "d": ["d"],
        "i": ["i"],
        "e": ["e"],
        "b": ["b"],
        "t": ["t"],
        "lOCode": ["lOCode", "locode"],
        "lOComment": ["lOComment", "locomment"],
        "lOBlank": ["lOBlank", "loblank"],
        "locCodeAndComment": ["locCodeAndComment", "loccodeandcomment"],
        "uniq_Op": ["uniq_Op", "uniq_op"],
        "uniq_Opnd": ["uniq_Opnd", "uniq_opnd"],
        "total_Op": ["total_Op", "total_op"],
        "total_Opnd": ["total_Opnd", "total_opnd"],
        "branchCount": ["branchCount", "branchcount"],
    }

    for canonical_name, candidates in alias_mapping.items():
        found = False
        for candidate in candidates:
            if candidate in source_dict and source_dict[candidate] is not None:
                vector_payload[canonical_name] = source_dict[candidate]
                found = True
                break
        if not found:
            missing.append(canonical_name)

    if missing:
        raise BugFeatureUnavailableError(
            missing_features=missing,
            details="Configure required static-code metric fields in Project.settings to enable Bug Prediction.",
        )

    try:
        return BugFeatureVector(**vector_payload)
    except ValidationError as ve:
        error_msgs = [f"{err['loc'][0]}: {err['msg']}" for err in ve.errors()]
        raise BugFeatureUnavailableError(
            missing_features=[],
            details="; ".join(error_msgs),
        ) from ve
    except (ValueError, TypeError) as exc:
        raise BugFeatureUnavailableError(
            missing_features=[],
            details=f"Invalid static-code metric values: {exc}",
        ) from exc
