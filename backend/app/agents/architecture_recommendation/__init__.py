"""Architecture Recommendation Agent Package."""

from app.agents.architecture_recommendation.agent import ArchitectureRecommendationAgent
from app.agents.architecture_recommendation.contracts import (
    ArchitectureRecommendationCandidate,
    ArchitectureRecommendationOutput,
    ArchitectureRequirementTrace,
    ArchitectureStyle,
    ArchitectureStyleRecommendation,
    ComponentRecommendation,
    DataFlowRecommendation,
    TechnologyCategory,
    TechnologyRecommendation,
    TradeOffAnalysis,
)
from app.agents.architecture_recommendation.validation import (
    validate_architecture_recommendation_output,
)

__all__ = [
    "ArchitectureRecommendationAgent",
    "ArchitectureStyle",
    "TechnologyCategory",
    "ArchitectureStyleRecommendation",
    "ComponentRecommendation",
    "DataFlowRecommendation",
    "TechnologyRecommendation",
    "TradeOffAnalysis",
    "ArchitectureRequirementTrace",
    "ArchitectureRecommendationCandidate",
    "ArchitectureRecommendationOutput",
    "validate_architecture_recommendation_output",
]
