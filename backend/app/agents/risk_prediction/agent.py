"""Risk Prediction Agent Implementation."""

import logging
from typing import Any

from app.agents.base import AbstractBaseAgent
from app.agents.contracts import (
    AgentMetadata,
    AgentType,
    ValidationResult,
)
from app.agents.providers.base import AbstractLLMProvider
from app.agents.risk_prediction.contracts import (
    DEFAULT_MODEL_LIMITATIONS,
    RiskModelProvenance,
    RiskPredictionCandidate,
    RiskPredictionOutput,
    map_risk_score_to_level,
)
from app.agents.risk_prediction.validation import validate_risk_prediction_output
from app.ml.features.risk_features import extract_risk_features
from app.ml.inference.model_loader import get_risk_model_loader
from app.ml.schemas.risk_features import RiskFeatureVector
from app.schemas.context import ProjectContextResponse

logger = logging.getLogger(__name__)


class RiskPredictionAgent(AbstractBaseAgent[RiskPredictionOutput]):
    """Supervised ML intelligence agent responsible for software project risk prediction.
    
    Guarantees:
      - Strictly local ML inference: Employs verified scikit-learn Ridge regression pipeline.
      - Zero LLM generation of risk scores or probabilities: All scores are continuous floats
        derived from the trained regression model on an empirical ~1.0 – 10.0 scale.
      - Deterministic risk-band mapping: Categorical risk level (LOW, MEDIUM, HIGH, CRITICAL)
        is an explicit application policy mapping, never an ML output.
      - Complete provenance: Captures artifact SHA-256 checksum and schema versions.
      - Honest limitations: Explicitly acknowledges weak predictive power (Test R² = -0.0087).
      - Single execution authority: Orchestrated exclusively through AgentExecutor.
    """

    @property
    def metadata(self) -> AgentMetadata:
        return AgentMetadata(
            agent_id="risk-prediction",
            name="Risk Prediction Agent",
            description="Predicts continuous software project risk scores and deterministic risk levels using verified supervised machine learning models.",
            version="1.0.0",
            agent_type=AgentType.ANALYSIS,
        )

    @property
    def output_schema(self) -> type[RiskPredictionOutput]:
        return RiskPredictionOutput

    async def initialize(self) -> None:
        """Lifecycle Hook 1: Pre-execution model and metadata verification."""
        loader = get_risk_model_loader()
        # Verify metadata and artifact existence/checksum early
        loader.load_metadata()

    async def analyze(
        self,
        context: ProjectContextResponse,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Lifecycle Hook 2: Deterministic feature extraction from canonical context.
        
        Extracts validated 5-predictor feature vector from context.project.settings.
        Raises MLFeatureUnavailableError if any required predictor is missing (zero silent imputation).
        """
        feature_vector: RiskFeatureVector = extract_risk_features(context)
        return {
            "context": context,
            "feature_vector": feature_vector,
        }

    async def generate(
        self,
        analysis_result: dict[str, Any],
        provider: AbstractLLMProvider,
        **kwargs: Any,
    ) -> RiskPredictionOutput:
        """Lifecycle Hook 3: Run local verified ML inference and construct structured candidate.
        
        The provider argument is accepted to fulfill the AbstractBaseAgent interface contract,
        but local ML execution is strictly isolated from external LLM providers.
        """
        feature_vector: RiskFeatureVector = analysis_result["feature_vector"]
        loader = get_risk_model_loader()

        # 1. Run local model inference
        predicted_score = loader.predict(feature_vector)

        # 2. Deterministic risk level mapping
        risk_level = map_risk_score_to_level(predicted_score)

        # 3. Model provenance from verified metadata
        meta = loader.load_metadata()
        provenance = RiskModelProvenance(
            model_name=meta.get("model_name", "se_risk_regressor"),
            model_version=meta.get("model_version", "1.0.0"),
            algorithm=meta.get("algorithm", "Ridge"),
            training_dataset=meta.get("training_dataset", "Reduced_Software_Project_Risk_Dataset_585.csv"),
            feature_schema_version=meta.get("feature_schema_version", "1.0.0"),
            artifact_checksum=meta.get("sha256_checksum", ""),
        )

        # 4. Human-readable feature summary
        feature_summary = {
            "project_size": feature_vector.project_size.value,
            "team_experience_level": feature_vector.team_experience_level.value,
            "estimated_effort_hours": float(feature_vector.estimated_effort_hours),
            "complexity_level": feature_vector.complexity_level.value,
            "requirement_stability": feature_vector.requirement_stability.value,
        }

        # 5. Objective, limitation-acknowledging summary
        summary = (
            f"Predicted project risk score is {predicted_score:.2f} (scale 1.0–10.0), "
            f"categorized under application policy as {risk_level.value} risk. "
            f"Derived via {provenance.algorithm} regression trained on {provenance.training_dataset}. "
            f"Notice: Model demonstrates weak empirical correlation (Test R² = -0.0087); "
            f"estimates serve as initial baseline indicators rather than definitive risk determinants."
        )

        # 6. Build Candidate
        candidate = RiskPredictionCandidate(
            summary=summary,
            predicted_risk_score=predicted_score,
            risk_level=risk_level,
            feature_summary=feature_summary,
            model_provenance=provenance,
            limitations=list(DEFAULT_MODEL_LIMITATIONS),
        )

        # 7. Build Output from candidate
        output = RiskPredictionOutput(
            summary=candidate.summary,
            predicted_risk_score=candidate.predicted_risk_score,
            risk_level=candidate.risk_level,
            feature_summary=candidate.feature_summary,
            model_provenance=candidate.model_provenance,
            limitations=candidate.limitations,
        )

        return output

    def validate_output(
        self,
        output: RiskPredictionOutput,
        context: ProjectContextResponse,
    ) -> ValidationResult:
        """Lifecycle Hook 4: Deterministic domain validation hook."""
        return validate_risk_prediction_output(output=output, context=context)
