"""Agent Framework Package."""

from app.agents.base import AbstractBaseAgent
from app.agents.contracts import (
    AgentErrorDetail,
    AgentExecutionStatus,
    AgentMetadata,
    AgentResult,
    AgentType,
    ValidationResult,
)
from app.agents.exceptions import (
    AgentConfigurationError,
    AgentError,
    AgentExecutionError,
    AgentNotFoundError,
    AgentValidationError,
    ProviderError,
    TransientProviderError,
)
from app.agents.execution import AgentExecutor
from app.agents.providers.base import (
    AbstractLLMProvider,
    LLMMessage,
    LLMRequest,
    LLMResponse,
)
from app.agents.providers.mock import MockLLMProvider
from app.agents.architecture_recommendation.agent import ArchitectureRecommendationAgent
from app.agents.architecture_recommendation.contracts import ArchitectureRecommendationOutput
from app.agents.database_design.agent import DatabaseDesignAgent
from app.agents.database_design.contracts import DatabaseDesignOutput
from app.agents.registry import AgentRegistry, agent_registry, register_default_agents
from app.agents.requirement_analysis.agent import RequirementAnalysisAgent
from app.agents.requirement_analysis.contracts import RequirementAnalysisOutput
from app.agents.risk_prediction.agent import RiskPredictionAgent
from app.agents.risk_prediction.contracts import (
    DEFAULT_MODEL_LIMITATIONS,
    RiskLevel,
    RiskModelProvenance,
    RiskPredictionCandidate,
    RiskPredictionOutput,
)
from app.agents.validation import DeterministicValidator

__all__ = [
    "AbstractBaseAgent",
    "AgentMetadata",
    "AgentType",
    "AgentExecutionStatus",
    "ValidationResult",
    "AgentErrorDetail",
    "AgentResult",
    "AgentError",
    "ProviderError",
    "TransientProviderError",
    "AgentExecutionError",
    "AgentValidationError",
    "AgentConfigurationError",
    "AgentNotFoundError",
    "DeterministicValidator",
    "AgentRegistry",
    "agent_registry",
    "register_default_agents",
    "AgentExecutor",
    "AbstractLLMProvider",
    "LLMMessage",
    "LLMRequest",
    "LLMResponse",
    "MockLLMProvider",
    "RequirementAnalysisAgent",
    "RequirementAnalysisOutput",
    "ArchitectureRecommendationAgent",
    "ArchitectureRecommendationOutput",
    "DatabaseDesignAgent",
    "DatabaseDesignOutput",
    "RiskPredictionAgent",
    "RiskPredictionOutput",
    "RiskPredictionCandidate",
    "RiskLevel",
    "RiskModelProvenance",
    "DEFAULT_MODEL_LIMITATIONS",
]
