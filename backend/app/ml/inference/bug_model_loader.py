"""Safe Model Loader and Artifact Verification for Bug / Defect Prediction Pipeline.

Enforces strict integrity verification:
  1. Artifact existence check
  2. SHA-256 byte checksum validation against metadata
  3. Feature schema version verification
  4. Deterministic pipeline caching
  5. Clear, non-silent failure modes (no synthetic fallback models)
"""

import hashlib
import json
import logging
from pathlib import Path
from typing import Any
import joblib
import numpy as np
import pandas as pd

from app.ml.schemas.bug_features import BugFeatureSchema, BugFeatureVector

logger = logging.getLogger(__name__)

# Default artifact locations relative to backend/app/ml/artifacts
DEFAULT_ARTIFACT_DIR = Path(__file__).resolve().parent.parent / "artifacts"
DEFAULT_MODEL_FILE = "bug_model_v1.joblib"
DEFAULT_METADATA_FILE = "bug_model_v1_metadata.json"


class BugModelUnavailableError(Exception):
    """Raised when the requested bug ML model artifact or metadata is missing or inaccessible."""
    pass


class BugModelChecksumMismatchError(Exception):
    """Raised when the artifact SHA-256 checksum does not match authoritative metadata."""
    pass


class BugModelLoader:
    """Authoritative loader and runtime inference adapter for Bug / Defect Prediction models."""

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
        """Load and parse bug model metadata."""
        if self._cached_metadata is not None:
            return self._cached_metadata

        if not self.metadata_path.exists():
            raise BugModelUnavailableError(
                f"Bug model metadata not found at '{self.metadata_path}'. "
                "Train the model first using app.ml.training.train_bug_model."
            )

        try:
            with open(self.metadata_path, "r", encoding="utf-8") as f:
                metadata = json.load(f)
        except Exception as exc:
            raise BugModelUnavailableError(f"Failed to read model metadata: {exc}") from exc

        # Schema version check
        schema_version = metadata.get("feature_schema_version")
        if schema_version != BugFeatureSchema.VERSION:
            raise BugModelUnavailableError(
                f"Feature schema version mismatch: model expects '{schema_version}', "
                f"application supports '{BugFeatureSchema.VERSION}'."
            )

        self._cached_metadata = metadata
        return metadata

    def load_model(self) -> Any:
        """Load, verify, and return the trained scikit-learn pipeline."""
        if self._cached_model is not None:
            return self._cached_model

        if not self.model_path.exists():
            raise BugModelUnavailableError(
                f"Bug model artifact not found at '{self.model_path}'. "
                "Train the model first using app.ml.training.train_bug_model."
            )

        metadata = self.load_metadata()
        expected_checksum = metadata.get("artifact_sha256") or metadata.get("sha256_checksum")
        if not expected_checksum:
            raise BugModelUnavailableError("Model metadata does not specify artifact_sha256.")

        actual_checksum = self.calculate_sha256(self.model_path)
        if actual_checksum != expected_checksum:
            raise BugModelChecksumMismatchError(
                f"Artifact checksum verification failed for '{self.model_path}'. "
                f"Expected: {expected_checksum}, Actual: {actual_checksum}."
            )

        try:
            pipeline = joblib.load(self.model_path)
            self._cached_model = pipeline
            logger.info(
                f"Successfully loaded and verified Bug Prediction model "
                f"[{metadata.get('model_name')} v{metadata.get('model_version')}] "
                f"checksum={actual_checksum[:12]}..."
            )
            return pipeline
        except Exception as exc:
            raise BugModelUnavailableError(f"Failed to deserialize model artifact: {exc}") from exc

    def predict(self, feature_vector: BugFeatureVector) -> bool:
        """Run inference on a single validated feature vector.

        Returns:
            Boolean defect prediction (True if predicted defective, False otherwise).
        """
        pipeline = self.load_model()
        data_dict = feature_vector.to_model_input_dict()
        df = pd.DataFrame([data_dict])
        prediction = pipeline.predict(df)[0]
        # Map integer/boolean prediction to standard python bool
        return bool(prediction == 1 or prediction is True or str(prediction).lower() == "true")

    def predict_proba(self, feature_vector: BugFeatureVector) -> float:
        """Compute the raw positive-class probability estimate for a feature vector.

        Notice: This is strictly the classifier's raw positive-class probability estimate.
        It is NOT a business confidence score, severity rating, certainty score, or
        likelihood of project failure.

        Returns:
            Raw positive-class probability estimate in [0.0, 1.0].
        """
        pipeline = self.load_model()
        if not hasattr(pipeline, "predict_proba"):
            raise BugModelUnavailableError(
                f"Configured model pipeline '{type(pipeline).__name__}' does not support predict_proba."
            )

        data_dict = feature_vector.to_model_input_dict()
        df = pd.DataFrame([data_dict])
        proba = pipeline.predict_proba(df)[0]

        # The positive class is class index 1 (or corresponding to True/1)
        classes = getattr(pipeline, "classes_", None)
        if classes is not None and len(classes) == 2:
            # Check which class corresponds to positive class (1 or 'true')
            pos_idx = 1
            for idx, cls_label in enumerate(classes):
                if str(cls_label).lower() in ("true", "1"):
                    pos_idx = idx
                    break
            raw_prob = float(proba[pos_idx])
        else:
            raw_prob = float(proba[1]) if len(proba) > 1 else float(proba[0])

        return float(np.clip(raw_prob, 0.0, 1.0))

    def reset_cache(self) -> None:
        """Clear cached in-memory model and metadata (primarily for tests)."""
        self._cached_model = None
        self._cached_metadata = None


# Module-level default singleton loader
_default_bug_loader: BugModelLoader | None = None


def get_bug_model_loader() -> BugModelLoader:
    """Retrieve or initialize the singleton BugModelLoader."""
    global _default_bug_loader
    if _default_bug_loader is None:
        _default_bug_loader = BugModelLoader()
    return _default_bug_loader


def predict_defect(feature_vector: BugFeatureVector) -> bool:
    """Convenience function predicting defect class using the default loader."""
    return get_bug_model_loader().predict(feature_vector)


def predict_defect_proba(feature_vector: BugFeatureVector) -> float:
    """Convenience function computing raw positive-class probability estimate."""
    return get_bug_model_loader().predict_proba(feature_vector)
