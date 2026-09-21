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
