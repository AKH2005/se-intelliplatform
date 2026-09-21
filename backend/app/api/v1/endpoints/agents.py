"""Agent Framework Metadata and Discovery API Endpoints."""

from fastapi import APIRouter

from app.agents.contracts import AgentMetadata
from app.agents.registry import agent_registry

router = APIRouter()


@router.get(
    "",
    response_model=list[AgentMetadata],
    summary="List registered framework agents",
    description=(
        "Returns declarative metadata for all agents registered with the platform framework. "
        "Exposes only safe identity and capability schemas without arbitrary execution capabilities."
    ),
)
async def list_registered_agents() -> list[AgentMetadata]:
    return agent_registry.list_agents()
