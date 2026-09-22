"""Safe Model Loader and Artifact Verification for Risk Prediction Pipeline.

Enforces strict integrity verification:
  1. Artifact existence check
  2. SHA-256 byte checksum validation
  3. Feature schema version verification
  4. Deterministic pipeline caching
  5. Clear, non-silent failure modes (no fake fallback models)
"""

import hashlib
import json
import logging
from pathlib import Path
from typing import Any
import joblib
import pandas as pd

from app.ml.schemas.risk_features import RiskFeatureSchema, RiskFeatureVector

logger = logging.getLogger(__name__)

# Default artifact locations relative to backend/app/ml/artifacts
DEFAULT_ARTIFACT_DIR = Path(__file__).resolve().parent.parent / "artifacts"
DEFAULT_MODEL_FILE = "risk_model_v1.joblib"
DEFAULT_METADATA_FILE = "risk_model_v1_metadata.json"


class ModelUnavailableError(Exception):
    """Raised when the requested ML model artifact or metadata is missing or inaccessible."""
    pass


class ModelChecksumMismatchError(Exception):
    """Raised when the artifact SHA-256 checksum does not match authoritative metadata."""
    pass


class RiskModelLoader:
    """Authoritative loader and runtime inference adapter for Risk Prediction models."""

    def __init__(
        self,
        artifact_dir: Path | str | None = None,
        model_filename: str = DEFAULT_MODEL_FILE,
        metadata_filename: str = DEFAULT_METADATA_FILE,
    ) -> None:
        self.artifact_dir = Path(artifact_dir) if artifact_dir else DEFAULT_ARTIFACT_DIR
        self.model_filename = model_filename
        self.metadata_filename = metadata_filename
        self._cached_model: Any | None = None
        self._cached_metadata: dict[str, Any] | None = None

    @property
    def model_path(self) -> Path:
        return self.artifact_dir / self.model_filename

    @property
    def metadata_path(self) -> Path:
        return self.artifact_dir / self.metadata_filename

    @staticmethod
    def calculate_sha256(file_path: Path) -> str:
        """Compute SHA-256 hash of file bytes."""
        hasher = hashlib.sha256()
        with open(file_path, "rb") as f:
            while chunk := f.read(65536):
                hasher.update(chunk)
        return hasher.hexdigest()

    def load_metadata(self) -> dict[str, Any]:
        """Load and parse model metadata."""
        if self._cached_metadata is not None:
            return self._cached_metadata

        if not self.metadata_path.exists():
            raise ModelUnavailableError(
                f"Risk model metadata not found at '{self.metadata_path}'. "
                "Train the model first using app.ml.training.train_risk_model."
            )

        try:
            with open(self.metadata_path, "r", encoding="utf-8") as f:
                metadata = json.load(f)
        except Exception as exc:
            raise ModelUnavailableError(f"Failed to read model metadata: {exc}") from exc

        # Schema version check
        schema_version = metadata.get("feature_schema_version")
        if schema_version != RiskFeatureSchema.VERSION:
            raise ModelUnavailableError(
                f"Feature schema version mismatch: model expects '{schema_version}', "
                f"application supports '{RiskFeatureSchema.VERSION}'."
            )

        self._cached_metadata = metadata
        return metadata

    def load_model(self) -> Any:
        """Load, verify, and return the trained scikit-learn pipeline."""
        if self._cached_model is not None:
            return self._cached_model

        if not self.model_path.exists():
            raise ModelUnavailableError(
                f"Risk model artifact not found at '{self.model_path}'. "
                "Train the model first using app.ml.training.train_risk_model."
            )

        metadata = self.load_metadata()
        expected_checksum = metadata.get("sha256_checksum")
        if not expected_checksum:
            raise ModelUnavailableError("Model metadata does not specify sha256_checksum.")

        actual_checksum = self.calculate_sha256(self.model_path)
        if actual_checksum != expected_checksum:
            raise ModelChecksumMismatchError(
                f"Artifact checksum verification failed for '{self.model_path}'. "
                f"Expected: {expected_checksum}, Actual: {actual_checksum}."
            )

        try:
            pipeline = joblib.load(self.model_path)
            self._cached_model = pipeline
            logger.info(
                f"Successfully loaded and verified Risk Prediction model "
                f"[{metadata.get('model_name')} v{metadata.get('model_version')}] "
                f"checksum={actual_checksum[:12]}..."
            )
            return pipeline
        except Exception as exc:
            raise ModelUnavailableError(f"Failed to deserialize model artifact: {exc}") from exc

    def predict(self, feature_vector: RiskFeatureVector) -> float:
        """Run inference on a single validated feature vector.
        
        Returns:
            Continuous predicted risk score (float).
        """
        pipeline = self.load_model()
        data_dict = feature_vector.to_model_input_dict()
        # Create single-row DataFrame matching training feature columns
        df = pd.DataFrame([data_dict])
        prediction = pipeline.predict(df)
        score = float(prediction[0])
        return score

    def reset_cache(self) -> None:
        """Clear cached in-memory model and metadata (primarily for tests)."""
        self._cached_model = None
        self._cached_metadata = None


# Module-level default singleton loader
_default_loader: RiskModelLoader | None = None


def get_risk_model_loader() -> RiskModelLoader:
    """Retrieve or initialize the singleton RiskModelLoader."""
    global _default_loader
    if _default_loader is None:
        _default_loader = RiskModelLoader()
    return _default_loader


def predict_risk(feature_vector: RiskFeatureVector) -> float:
    """Convenience function predicting risk using the default loader."""
    return get_risk_model_loader().predict(feature_vector)
