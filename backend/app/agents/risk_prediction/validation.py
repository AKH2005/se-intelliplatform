"""Deterministic Domain Validation for Risk Prediction Agent."""

import math
import re
from typing import Any

from app.agents.contracts import ValidationResult
from app.agents.risk_prediction.contracts import (
    RiskLevel,
    RiskPredictionOutput,
    map_risk_score_to_level,
)
from app.schemas.context import ProjectContextResponse

# Prohibited confidence / overstatement phrases (enforcing Section 10)
PROHIBITED_CONFIDENCE_PATTERNS = [
    r"highly\s+accurate",
    r"high\s+confidence",
    r"reliable\s+prediction",
    r"\d+%\s*accurate",
    r"\d+%\s*confident",
    r"chance\s+of\s+being\s+risky",
    r"probability\s+of\s+risk",
]

REQUIRED_FEATURE_KEYS = {
    "project_size",
    "team_experience_level",
    "estimated_effort_hours",
    "complexity_level",
    "requirement_stability",
}


def validate_risk_prediction_output(
    output: RiskPredictionOutput,
    context: ProjectContextResponse,
) -> ValidationResult:
    """Perform strict deterministic validation on RiskPredictionOutput.
    
    Validates:
      1. Numerical validity: predicted_risk_score is finite and within [1.0, 10.0]
      2. Deterministic risk level: matches application policy mapping
      3. Feature summary: contains all 5 required human-readable features
      4. Provenance: metadata is non-empty and well-formed
      5. Limitations: non-empty list acknowledging empirical constraints
      6. Language compliance: zero prohibited confidence or overstatement terms
    """
    errors: list[str] = []

    # 1. Numerical Validity
    score = output.predicted_risk_score
    if not isinstance(score, (int, float)) or math.isnan(score) or math.isinf(score):
        errors.append(f"predicted_risk_score must be a finite float, got '{score}'.")
    elif score < 1.0 or score > 10.0:
        errors.append(
            f"predicted_risk_score {score:.4f} is outside the valid target scale [1.0, 10.0]."
        )

    # 2. Risk Level Mapping Invariant
    if not errors:
        expected_level = map_risk_score_to_level(score)
        if output.risk_level != expected_level:
            errors.append(
                f"risk_level '{output.risk_level.value}' does not match deterministic mapping "
                f"for score {score:.4f} (expected '{expected_level.value}')."
            )

    # 3. Feature Summary Invariant
    if not isinstance(output.feature_summary, dict):
        errors.append("feature_summary must be a dictionary.")
    else:
        missing_features = REQUIRED_FEATURE_KEYS - set(output.feature_summary.keys())
        if missing_features:
            errors.append(f"feature_summary is missing required features: {sorted(missing_features)}.")
        for k in REQUIRED_FEATURE_KEYS:
            if output.feature_summary.get(k) is None:
                errors.append(f"feature_summary['{k}'] cannot be None.")

    # 4. Model Provenance Invariant
    prov = output.model_provenance
    if not prov.model_name.strip():
        errors.append("model_provenance.model_name cannot be empty.")
    if not prov.model_version.strip():
        errors.append("model_provenance.model_version cannot be empty.")
    if not prov.algorithm.strip():
        errors.append("model_provenance.algorithm cannot be empty.")
    if not prov.training_dataset.strip():
        errors.append("model_provenance.training_dataset cannot be empty.")
    if not prov.feature_schema_version.strip():
        errors.append("model_provenance.feature_schema_version cannot be empty.")
    if not prov.artifact_checksum.strip() or len(prov.artifact_checksum) != 64:
        errors.append("model_provenance.artifact_checksum must be a valid 64-character SHA-256 hash.")

    # 5. Limitations Invariant
    if not output.limitations:
        errors.append("limitations list cannot be empty.")
    elif len(output.limitations) < 3:
        errors.append("limitations list must comprehensively document empirical model constraints.")

    # 6. Prohibited Overstatement Language
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
