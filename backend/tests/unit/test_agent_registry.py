"""Unit Tests for AgentRegistry."""

import pytest
from pydantic import BaseModel

from app.agents.base import AbstractBaseAgent
from app.agents.contracts import AgentMetadata, AgentType
from app.agents.exceptions import AgentNotFoundError
from app.agents.registry import AgentRegistry
from app.core.exceptions import ConflictError


class DummyOutput(BaseModel):
    ok: bool = True


class DummyAgent(AbstractBaseAgent[DummyOutput]):
    def __init__(self, agent_id: str, version: str = "1.0.0") -> None:
        self._agent_id = agent_id
        self._version = version

    @property
    def metadata(self) -> AgentMetadata:
        return AgentMetadata(
            agent_id=self._agent_id,
            name=f"Agent {self._agent_id}",
            description="Dummy description",
            version=self._version,
            agent_type=AgentType.VALIDATION,
        )

    @property
    def output_schema(self) -> type[DummyOutput]:
        return DummyOutput

    async def analyze(self, context, **kwargs) -> dict:
        return {}

    async def generate(self, analysis_result, provider, **kwargs) -> DummyOutput:
        return DummyOutput()


def test_registry_register_and_get():
    """Verify registering an agent and retrieving it by ID."""
    reg = AgentRegistry()
    agent = DummyAgent("sample-agent-1")
    reg.register(agent)

    retrieved = reg.get("sample-agent-1")
    assert retrieved.metadata.agent_id == "sample-agent-1"


def test_registry_duplicate_registration_fails():
    """Verify duplicate agent_id registration raises ConflictError."""
    reg = AgentRegistry()
    a1 = DummyAgent("duplicate-agent")
    a2 = DummyAgent("duplicate-agent")

    reg.register(a1)
    with pytest.raises(ConflictError) as exc_info:
        reg.register(a2)
    assert "already registered" in str(exc_info.value)


def test_registry_unknown_agent_fails():
    """Verify querying unregistered agent raises AgentNotFoundError."""
    reg = AgentRegistry()
    with pytest.raises(AgentNotFoundError):
        reg.get("non-existent-agent-id")


def test_registry_list_agents():
    """Verify listing all registered agent metadata."""
    reg = AgentRegistry()
    reg.register(DummyAgent("agent-alpha", "1.0.0"))
    reg.register(DummyAgent("agent-beta", "2.1.0"))

    agents = reg.list_agents()
    assert len(agents) == 2
    ids = [a.agent_id for a in agents]
    assert "agent-alpha" in ids
    assert "agent-beta" in ids
