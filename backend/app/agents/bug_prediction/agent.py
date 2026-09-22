"""Bug / Defect Prediction Agent Implementation."""

import logging
from typing import Any

from app.agents.base import AbstractBaseAgent
from app.agents.bug_prediction.contracts import (
    DEFAULT_BUG_LIMITATIONS,
    BugModelProvenance,
    BugPredictionCandidate,
    BugPredictionOutput,
    DefectPredictionLabel,
)
from app.agents.bug_prediction.validation import validate_bug_prediction_output
from app.agents.contracts import (
    AgentMetadata,
    AgentType,
    ValidationResult,
)
from app.agents.providers.base import AbstractLLMProvider
from app.ml.features.bug_features import extract_bug_features
from app.ml.inference.bug_model_loader import get_bug_model_loader
from app.ml.schemas.bug_features import BugFeatureSchema, BugFeatureVector
from app.schemas.context import ProjectContextResponse

logger = logging.getLogger(__name__)


class BugPredictionAgent(AbstractBaseAgent[BugPredictionOutput]):
    """Supervised ML intelligence agent responsible for software module defect susceptibility prediction.

    Guarantees:
      - Strictly local ML inference: Employs verified scikit-learn LogisticRegression pipeline.
      - Zero LLM generation of predictions: Classification and probability estimates are derived
        directly from empirical static-code metrics via verified local ML models.
      - Honest limitations: Explicitly acknowledges moderate predictive performance
        (Test Recall = 0.4851, Test F1 = 0.4333, Test PR-AUC = 0.4254).
      - Single execution authority: Orchestrated exclusively through AgentExecutor.
      - Read-only: Does not mutate project, requirements, or database state.
    """

    @property
    def metadata(self) -> AgentMetadata:
        return AgentMetadata(
            agent_id="bug-prediction",
            name="Bug Prediction Agent",
            description="Predicts software module defect susceptibility using verified supervised machine learning models on static-code metrics.",
            version="1.0.0",
            agent_type=AgentType.ANALYSIS,
        )

    @property
    def output_schema(self) -> type[BugPredictionOutput]:
        return BugPredictionOutput

    async def initialize(self) -> None:
        """Lifecycle Hook 1: Pre-execution model and metadata verification."""
        loader = get_bug_model_loader()
        # Verify metadata, schema version, and artifact existence/checksum early
        loader.load_metadata()

    async def analyze(
        self,
        context: ProjectContextResponse,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Lifecycle Hook 2: Deterministic feature extraction from canonical context.

        Extracts validated 21-predictor feature vector from context.project.settings.
        Raises BugFeatureUnavailableError if any required predictor is missing (zero silent imputation).
        """
        feature_vector: BugFeatureVector = extract_bug_features(context)
        return {
            "context": context,
            "feature_vector": feature_vector,
        }

    async def generate(
        self,
        analysis_result: dict[str, Any],
        provider: AbstractLLMProvider,
        **kwargs: Any,
    ) -> BugPredictionOutput:
        """Lifecycle Hook 3: Run local verified ML inference and construct structured candidate.

        The provider argument is accepted to fulfill the AbstractBaseAgent interface contract,
        but local ML execution is strictly isolated from external LLM providers.
        """
        feature_vector: BugFeatureVector = analysis_result["feature_vector"]
        loader = get_bug_model_loader()

        # 1. Run local model inference
        is_defective = loader.predict(feature_vector)
        prediction_label = DefectPredictionLabel.DEFECTIVE if is_defective else DefectPredictionLabel.NON_DEFECTIVE
        predicted_probability = loader.predict_proba(feature_vector)

        # 2. Model provenance from verified metadata
        meta = loader.load_metadata()
        provenance = BugModelProvenance(
            model_name=meta.get("model_name", "se_bug_classifier"),
            model_version=meta.get("model_version", "1.0.0"),
            algorithm=meta.get("algorithm", "LogisticRegression"),
            training_dataset=meta.get("dataset", {}).get("name", "JM1") if isinstance(meta.get("dataset"), dict) else "JM1",
            feature_schema_version=meta.get("feature_schema_version", "1.0.0"),
            artifact_checksum=meta.get("artifact_sha256") or meta.get("sha256_checksum", ""),
        )

        # 3. Validated input features summary matching JM1 names
        feature_summary = feature_vector.to_model_input_dict()

        # 4. Objective, limitation-acknowledging summary
        summary = (
            f"Module defect susceptibility is evaluated as {prediction_label.value} "
            f"with a raw model positive-class probability estimate of {predicted_probability:.4f}. "
            f"Derived via {provenance.algorithm} (class_weight='balanced') trained on the NASA {provenance.training_dataset} dataset. "
            f"Notice: Model provides an empirical defect classification signal (held-out test Recall = 0.4851, F1 = 0.4333); "
            f"it serves as an advisory quality indicator, not a definitive guarantee that the module is defective or defect-free."
        )

        # 5. Build Candidate
        candidate = BugPredictionCandidate(
            summary=summary,
            prediction_label=prediction_label,
            predicted_probability=predicted_probability,
            target=BugFeatureSchema.TARGET_COLUMN,
            model_provenance=provenance,
            feature_names=list(BugFeatureSchema.APPROVED_FEATURES),
            feature_summary=feature_summary,
            limitations=list(DEFAULT_BUG_LIMITATIONS),
        )

        # 6. Build Output from candidate
        output = BugPredictionOutput(
            agent_id=candidate.agent_id,
            agent_version=candidate.agent_version,
            summary=candidate.summary,
            prediction_label=candidate.prediction_label,
            predicted_probability=candidate.predicted_probability,
            target=candidate.target,
            model_provenance=candidate.model_provenance,
            feature_names=candidate.feature_names,
            feature_summary=candidate.feature_summary,
            limitations=candidate.limitations,
        )

        return output

    def validate_output(
        self,
        output: BugPredictionOutput,
        context: ProjectContextResponse,
    ) -> ValidationResult:
        """Lifecycle Hook 4: Deterministic domain validation hook."""
        return validate_bug_prediction_output(output=output, context=context)
