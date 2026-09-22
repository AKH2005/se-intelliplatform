"""Deterministic Domain Validation for Bug / Defect Prediction Agent."""

import math
import re

from app.agents.bug_prediction.contracts import BugPredictionOutput, DefectPredictionLabel
from app.agents.contracts import ValidationResult
from app.ml.schemas.bug_features import BugFeatureSchema
from app.schemas.context import ProjectContextResponse

# Prohibited confidence / overstatement phrases (enforcing Sections 2 & 9)
PROHIBITED_CONFIDENCE_PATTERNS = [
    r"highly\s+accurate",
    r"high\s+confidence",
    r"highly\s+reliable",
    r"production-grade\s+defect\s+detection",
    r"(?<!not\s)(?<!not\sa\s)(?<!never\s)guaranteed",
    r"certainty\s+of\s+bugs",
    r"\d+%\s*accurate",
    r"\d+%\s*confident",
    r"zero\s+defects",
    r"defect-free\s+guarantee",
]


def validate_bug_prediction_output(
    output: BugPredictionOutput,
    context: ProjectContextResponse,
) -> ValidationResult:
    """Perform strict deterministic validation on BugPredictionOutput.

    Validates:
      1. Classification label: prediction_label in {DEFECTIVE, NON_DEFECTIVE}
      2. Probability validity: 0.0 <= predicted_probability <= 1.0 (finite float)
      3. Target metric: target == 'defects'
      4. Feature provenance: feature_names matches approved 21 predictors exactly
      5. Feature summary: contains all 21 required predictors with finite non-negative values
      6. Model provenance: metadata corresponds to verified JM1 artifact
      7. Limitations: non-empty list acknowledging empirical constraints
      8. Language compliance: zero prohibited confidence or overstatement terms
    """
    errors: list[str] = []

    # 1. Label Invariant
    if not isinstance(output.prediction_label, DefectPredictionLabel):
        try:
            DefectPredictionLabel(str(output.prediction_label))
        except ValueError:
            errors.append(
                f"prediction_label must be one of {[e.value for e in DefectPredictionLabel]}, "
                f"got '{output.prediction_label}'."
            )

    # 2. Probability Invariant
    prob = output.predicted_probability
    if not isinstance(prob, (int, float)) or math.isnan(prob) or math.isinf(prob):
        errors.append(f"predicted_probability must be a finite float, got '{prob}'.")
    elif not (0.0 <= prob <= 1.0):
        errors.append(f"predicted_probability must be between 0.0 and 1.0, got '{prob}'.")

    # 3. Target Invariant
    if output.target != BugFeatureSchema.TARGET_COLUMN:
        errors.append(
            f"target must be '{BugFeatureSchema.TARGET_COLUMN}', got '{output.target}'."
        )

    # 4. Feature Provenance Invariant
    if output.feature_names != BugFeatureSchema.APPROVED_FEATURES:
        errors.append(
            f"feature_names does not match approved predictors: "
            f"expected {BugFeatureSchema.APPROVED_FEATURES}, got {output.feature_names}."
        )

    # 5. Feature Summary Invariant
    if not isinstance(output.feature_summary, dict):
        errors.append("feature_summary must be a dictionary.")
    else:
        missing_keys = set(BugFeatureSchema.APPROVED_FEATURES) - set(output.feature_summary.keys())
        if missing_keys:
            errors.append(f"feature_summary is missing required keys: {sorted(missing_keys)}.")
        for k in BugFeatureSchema.APPROVED_FEATURES:
            val = output.feature_summary.get(k)
            if val is None:
                errors.append(f"feature_summary['{k}'] cannot be None.")
            elif not isinstance(val, (int, float)) or math.isnan(val) or math.isinf(val):
                errors.append(f"feature_summary['{k}'] must be a finite float, got '{val}'.")
            elif val < 0.0:
                errors.append(f"feature_summary['{k}'] must be non-negative, got '{val}'.")

    # 6. Model Provenance Invariant
    prov = output.model_provenance
    if not prov.model_name.strip():
        errors.append("model_provenance.model_name cannot be empty.")
    if prov.model_version != "1.0.0":
        errors.append(f"model_provenance.model_version must be '1.0.0', got '{prov.model_version}'.")
    if prov.algorithm != "LogisticRegression":
        errors.append(f"model_provenance.algorithm must be 'LogisticRegression', got '{prov.algorithm}'.")
    if prov.training_dataset != "JM1":
        errors.append(f"model_provenance.training_dataset must be 'JM1', got '{prov.training_dataset}'.")
    if not prov.artifact_checksum.strip() or len(prov.artifact_checksum) != 64:
        errors.append("model_provenance.artifact_checksum must be a valid 64-character SHA-256 hash.")

    # 7. Limitations Invariant
    if not output.limitations:
        errors.append("limitations list cannot be empty.")
    elif len(output.limitations) < 3:
        errors.append("limitations list must comprehensively document empirical model constraints.")

    # 8. Prohibited Overstatement Language
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
