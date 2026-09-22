"""Deterministic Domain Validation for Timeline Prediction Agent."""

import math
import re
from typing import Any

from app.agents.contracts import ValidationResult
from app.agents.timeline_prediction.contracts import TimelinePredictionOutput
from app.ml.schemas.timeline_features import TimelineFeatureSchema
from app.schemas.context import ProjectContextResponse

# Prohibited confidence / overstatement phrases (enforcing Sections 9 & 15)
PROHIBITED_CONFIDENCE_PATTERNS = [
    r"highly\s+accurate",
    r"high\s+confidence",
    r"highly\s+reliable",
    r"production-grade\s+forecasting",
    r"(?<!not\s)(?<!not\sa\s)(?<!never\s)guaranteed",
    r"precise\s+deadline",
    r"\d+%\s*accurate",
    r"\d+%\s*confident",
    r"probability\s+of",
]

REQUIRED_FEATURE_SUMMARY_KEYS = {
    "afp",
    "input_count",
    "output_count",
    "enquiry_count",
    "file_count",
    "interface_count",
    "resource_level",
}


def validate_timeline_prediction_output(
    output: TimelinePredictionOutput,
    context: ProjectContextResponse,
) -> ValidationResult:
    """Perform strict deterministic validation on TimelinePredictionOutput.
    
    Validates:
      1. Numerical validity: predicted_duration_months is finite float > 0.0
      2. Target metric: target == 'Duration' and target_unit == 'months'
      3. Feature provenance: feature_names matches approved 7 predictors
      4. Feature summary: contains all required features
      5. Model provenance: metadata corresponds to verified artifact
      6. Limitations: non-empty list acknowledging empirical constraints
      7. Language compliance: zero prohibited confidence or overstatement terms
    """
    errors: list[str] = []

    # 1. Numerical Validity
    duration = output.predicted_duration_months
    if not isinstance(duration, (int, float)) or math.isnan(duration) or math.isinf(duration):
        errors.append(f"predicted_duration_months must be a finite float, got '{duration}'.")
    elif duration <= 0.0:
        errors.append(f"predicted_duration_months must be strictly greater than 0.0, got '{duration}'.")

    # 2. Target Invariants
    if output.target != TimelineFeatureSchema.TARGET_COLUMN:
        errors.append(
            f"target must be '{TimelineFeatureSchema.TARGET_COLUMN}', got '{output.target}'."
        )
    if output.target_unit != TimelineFeatureSchema.TARGET_UNIT:
        errors.append(
            f"target_unit must be '{TimelineFeatureSchema.TARGET_UNIT}', got '{output.target_unit}'."
        )

    # 3. Feature Provenance Invariant
    if output.feature_names != TimelineFeatureSchema.APPROVED_FEATURES:
        errors.append(
            f"feature_names does not match approved predictors: "
            f"expected {TimelineFeatureSchema.APPROVED_FEATURES}, got {output.feature_names}."
        )

    # 4. Feature Summary Invariant
    if not isinstance(output.feature_summary, dict):
        errors.append("feature_summary must be a dictionary.")
    else:
        missing_keys = REQUIRED_FEATURE_SUMMARY_KEYS - set(output.feature_summary.keys())
        if missing_keys:
            errors.append(f"feature_summary is missing required keys: {sorted(missing_keys)}.")
        for k in REQUIRED_FEATURE_SUMMARY_KEYS:
            if output.feature_summary.get(k) is None:
                errors.append(f"feature_summary['{k}'] cannot be None.")

    # 5. Model Provenance Invariant
    prov = output.model_provenance
    if not prov.model_name.strip():
        errors.append("model_provenance.model_name cannot be empty.")
    if prov.model_version != "1.0.0":
        errors.append(f"model_provenance.model_version must be '1.0.0', got '{prov.model_version}'.")
    if prov.algorithm != "RandomForestRegressor":
        errors.append(f"model_provenance.algorithm must be 'RandomForestRegressor', got '{prov.algorithm}'.")
    if prov.training_dataset != "China":
        errors.append(f"model_provenance.training_dataset must be 'China', got '{prov.training_dataset}'.")
    if not prov.artifact_checksum.strip() or len(prov.artifact_checksum) != 64:
        errors.append("model_provenance.artifact_checksum must be a valid 64-character SHA-256 hash.")

    # 6. Limitations Invariant
    if not output.limitations:
        errors.append("limitations list cannot be empty.")
    elif len(output.limitations) < 3:
        errors.append("limitations list must comprehensively document empirical model constraints.")

    # 7. Prohibited Overstatement Language
    summary_lower = output.summary.lower()
    for pattern in PROHIBITED_CONFIDENCE_PATTERNS:
        if re.search(pattern, summary_lower):
            errors.append(
                f"summary contains prohibited overstatement/confidence language matching '{pattern}'."
            )

    return ValidationResult(
        is_valid=len(errors) == 0,
        errors=errors,
    )
