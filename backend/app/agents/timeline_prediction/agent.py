"""Timeline Prediction Agent Implementation."""

import logging
from typing import Any

from app.agents.base import AbstractBaseAgent
from app.agents.contracts import (
    AgentMetadata,
    AgentType,
    ValidationResult,
)
from app.agents.providers.base import AbstractLLMProvider
from app.agents.timeline_prediction.contracts import (
    DEFAULT_TIMELINE_LIMITATIONS,
    TimelineModelProvenance,
    TimelinePredictionCandidate,
    TimelinePredictionOutput,
)
from app.agents.timeline_prediction.validation import validate_timeline_prediction_output
from app.ml.features.timeline_features import extract_timeline_features
from app.ml.inference.timeline_model_loader import get_timeline_model_loader
from app.ml.schemas.timeline_features import TimelineFeatureSchema, TimelineFeatureVector
from app.schemas.context import ProjectContextResponse

logger = logging.getLogger(__name__)


class TimelinePredictionAgent(AbstractBaseAgent[TimelinePredictionOutput]):
    """Supervised ML intelligence agent responsible for software project duration prediction.
    
    Guarantees:
      - Strictly local ML inference: Employs verified scikit-learn RandomForestRegressor pipeline.
      - Zero LLM generation of duration estimates: Duration is a continuous numerical float
        in elapsed months derived from historical empirical function point metrics.
      - Honest limitations: Explicitly acknowledges moderate predictive performance
        (Test R² = 0.2362, Test MAE = 4.5926 months).
      - Single execution authority: Orchestrated exclusively through AgentExecutor.
      - Read-only: Does not modify requirements, context, or database project settings.
    """

    @property
    def metadata(self) -> AgentMetadata:
        return AgentMetadata(
            agent_id="timeline-prediction",
            name="Timeline Prediction Agent",
            description="Predicts continuous software project duration in elapsed months using verified supervised machine learning models.",
            version="1.0.0",
            agent_type=AgentType.ANALYSIS,
        )

    @property
    def output_schema(self) -> type[TimelinePredictionOutput]:
        return TimelinePredictionOutput

    async def initialize(self) -> None:
        """Lifecycle Hook 1: Pre-execution model and metadata verification."""
        loader = get_timeline_model_loader()
        # Verify metadata, schema version, and artifact existence/checksum early
        loader.load_metadata()

    async def analyze(
        self,
        context: ProjectContextResponse,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Lifecycle Hook 2: Deterministic feature extraction from canonical context.
        
        Extracts validated 7-predictor feature vector from context.project.settings.
        Raises TimelineFeatureUnavailableError if any required predictor is missing (zero silent imputation).
        """
        feature_vector: TimelineFeatureVector = extract_timeline_features(context)
        return {
            "context": context,
            "feature_vector": feature_vector,
        }

    async def generate(
        self,
        analysis_result: dict[str, Any],
        provider: AbstractLLMProvider,
        **kwargs: Any,
    ) -> TimelinePredictionOutput:
        """Lifecycle Hook 3: Run local verified ML inference and construct structured candidate.
        
        The provider argument is accepted to fulfill the AbstractBaseAgent interface contract,
        but local ML execution is strictly isolated from external LLM providers.
        """
        feature_vector: TimelineFeatureVector = analysis_result["feature_vector"]
        loader = get_timeline_model_loader()

        # 1. Run local model inference (continuous float in months)
        predicted_duration = loader.predict(feature_vector)
        estimated_duration = round(predicted_duration, 2)

        # 2. Model provenance from verified metadata
        meta = loader.load_metadata()
        provenance = TimelineModelProvenance(
            model_name=meta.get("model_name", "se_timeline_regressor"),
            model_version=meta.get("model_version", "1.0.0"),
            algorithm=meta.get("algorithm", "RandomForestRegressor"),
            training_dataset=meta.get("training_dataset", "China"),
            feature_schema_version=meta.get("feature_schema_version", "1.0.0"),
            artifact_checksum=meta.get("sha256_checksum", ""),
        )

        # 3. Human-readable feature summary
        feature_summary = {
            "afp": float(feature_vector.afp),
            "input_count": float(feature_vector.input_count),
            "output_count": float(feature_vector.output_count),
            "enquiry_count": float(feature_vector.enquiry_count),
            "file_count": float(feature_vector.file_count),
            "interface_count": float(feature_vector.interface_count),
            "resource_level": int(feature_vector.resource_level.value),
        }

        # 4. Objective, limitation-acknowledging summary
        summary = (
            f"Estimated project duration is {estimated_duration:.2f} months "
            f"({predicted_duration:.4f} months unrounded). "
            f"Derived via {provenance.algorithm} trained on the {provenance.training_dataset} software metrics dataset. "
            f"Notice: Model provides an empirical point estimate (held-out test R² = 0.2362, MAE = 4.5926 months); "
            f"it serves as an advisory planning indicator, not a contractual or fixed project deadline."
        )

        # 5. Build Candidate
        candidate = TimelinePredictionCandidate(
            summary=summary,
            predicted_duration_months=predicted_duration,
            estimated_duration_months=estimated_duration,
            target=TimelineFeatureSchema.TARGET_COLUMN,
            target_unit=TimelineFeatureSchema.TARGET_UNIT,
            model_provenance=provenance,
            feature_names=list(TimelineFeatureSchema.APPROVED_FEATURES),
            feature_summary=feature_summary,
            limitations=list(DEFAULT_TIMELINE_LIMITATIONS),
        )

        # 6. Build Output from candidate
        output = TimelinePredictionOutput(
            agent_id=candidate.agent_id,
            agent_version=candidate.agent_version,
            summary=candidate.summary,
            predicted_duration_months=candidate.predicted_duration_months,
            estimated_duration_months=candidate.estimated_duration_months,
            target=candidate.target,
            target_unit=candidate.target_unit,
            model_provenance=candidate.model_provenance,
            feature_names=candidate.feature_names,
            feature_summary=candidate.feature_summary,
            limitations=candidate.limitations,
        )

        return output

    def validate_output(
        self,
        output: TimelinePredictionOutput,
        context: ProjectContextResponse,
    ) -> ValidationResult:
        """Lifecycle Hook 4: Deterministic domain validation hook."""
        return validate_timeline_prediction_output(output=output, context=context)
