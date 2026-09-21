"""Integration Tests for Agents Metadata API."""

import pytest
from httpx import AsyncClient
from pydantic import BaseModel

from app.agents.base import AbstractBaseAgent
from app.agents.contracts import AgentMetadata, AgentType
from app.agents.registry import agent_registry


class MockApiAgentOutput(BaseModel):
    summary: str = "ok"


class ApiTestAgent(AbstractBaseAgent[MockApiAgentOutput]):
    @property
    def metadata(self) -> AgentMetadata:
        return AgentMetadata(
            agent_id="api-discovery-test-agent",
            name="API Discovery Test Agent",
            description="Exposes metadata via GET /api/v1/agents",
            version="1.0.0",
            agent_type=AgentType.ANALYSIS,
        )

    @property
    def output_schema(self) -> type[MockApiAgentOutput]:
        return MockApiAgentOutput

    async def analyze(self, context, **kwargs) -> dict:
        return {}

    async def generate(self, analysis_result, provider, **kwargs) -> MockApiAgentOutput:
        return MockApiAgentOutput()


@pytest.mark.asyncio
async def test_get_agents_metadata_list(client: AsyncClient):
    """Verify GET /api/v1/agents returns metadata for registered framework agents."""
    agent_registry.clear()
    agent_registry.register(ApiTestAgent())

    res = await client.get("/api/v1/agents")
    assert res.status_code == 200
    data = res.json()
    assert isinstance(data, list)
    assert len(data) == 1
    assert data[0]["agent_id"] == "api-discovery-test-agent"
    assert data[0]["name"] == "API Discovery Test Agent"
    assert data[0]["version"] == "1.0.0"
    assert data[0]["agent_type"] == "ANALYSIS"


@pytest.mark.asyncio
async def test_arbitrary_agent_execution_endpoint_not_exposed(client: AsyncClient):
    """Verify security constraint: arbitrary agent execution is not exposed over HTTP."""
    # Attempting to POST /api/v1/agents/run must return 404/405 (endpoint does not exist)
    res = await client.post("/api/v1/agents/run", json={})
    assert res.status_code in (404, 405)
