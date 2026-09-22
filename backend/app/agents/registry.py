"""Lightweight Agent Registry for Platform Extension."""

import logging
from typing import Any
from app.agents.base import AbstractBaseAgent
from app.agents.contracts import AgentMetadata
from app.agents.exceptions import AgentNotFoundError
from app.core.exceptions import ConflictError

logger = logging.getLogger(__name__)


class AgentRegistry:
    """Registry maintaining registered platform agent definitions.
    
    Acts strictly as an extension and discovery mechanism. It does NOT perform
    orchestration or dependency pipeline scheduling.
    """

    def __init__(self) -> None:
        self._agents: dict[str, AbstractBaseAgent[Any]] = {}

    def register(self, agent: AbstractBaseAgent[Any]) -> None:
        """Register an agent implementation with the platform."""
        meta = agent.metadata
        if meta.agent_id in self._agents:
            raise ConflictError(
                message=f"Agent with ID '{meta.agent_id}' is already registered.",
                field="agent_id",
                value=meta.agent_id,
            )
        self._agents[meta.agent_id] = agent
        logger.info(f"Registered agent '{meta.name}' [{meta.agent_id} v{meta.version}]")

    def has(self, agent_id: str) -> bool:
        """Check if an agent ID is already registered."""
        return agent_id in self._agents

    def get(self, agent_id: str) -> AbstractBaseAgent[Any]:
        """Retrieve a registered agent by ID or raise AgentNotFoundError."""
        if agent_id not in self._agents:
            raise AgentNotFoundError(agent_id=agent_id)
        return self._agents[agent_id]

    def list_agents(self) -> list[AgentMetadata]:
        """Return metadata for all registered agents."""
        return [agent.metadata for agent in self._agents.values()]

    def clear(self) -> None:
        """Clear all registered agents (primarily for test teardown)."""
        self._agents.clear()


# Global framework agent registry singleton
agent_registry = AgentRegistry()


def register_default_agents(registry: AgentRegistry | None = None) -> None:
    """Register built-in platform agents in an idempotent manner.
    
    Guarantees:
    - Repeated calls do not raise duplicate registration ConflictErrors.
    - Custom/isolated AgentRegistry instances can be passed for test isolation.
    - Importing agent packages does not mutate registry state automatically.
    """
    target = registry if registry is not None else agent_registry
    from app.agents.architecture_recommendation.agent import ArchitectureRecommendationAgent
    from app.agents.database_design.agent import DatabaseDesignAgent
    from app.agents.requirement_analysis.agent import RequirementAnalysisAgent
    from app.agents.risk_prediction.agent import RiskPredictionAgent
    from app.agents.timeline_prediction.agent import TimelinePredictionAgent

    req_agent = RequirementAnalysisAgent()
    if not target.has(req_agent.metadata.agent_id):
        target.register(req_agent)

    arch_agent = ArchitectureRecommendationAgent()
    if not target.has(arch_agent.metadata.agent_id):
        target.register(arch_agent)

    db_agent = DatabaseDesignAgent()
    if not target.has(db_agent.metadata.agent_id):
        target.register(db_agent)

    risk_agent = RiskPredictionAgent()
    if not target.has(risk_agent.metadata.agent_id):
        target.register(risk_agent)

    timeline_agent = TimelinePredictionAgent()
    if not target.has(timeline_agent.metadata.agent_id):
        target.register(timeline_agent)


