"""API v1 Central Router Aggregator."""

from fastapi import APIRouter

from app.api.v1.endpoints import agents, context, health, projects, requirements, workflows

api_v1_router = APIRouter()

api_v1_router.include_router(health.router, tags=["Health"])
api_v1_router.include_router(projects.router, prefix="/projects", tags=["Projects"])
api_v1_router.include_router(
    requirements.router,
    prefix="/projects/{project_id}/requirements",
    tags=["Requirements"],
)
api_v1_router.include_router(
    context.router,
    prefix="/projects/{project_id}/context",
    tags=["Context"],
)
api_v1_router.include_router(agents.router, prefix="/agents", tags=["Agents"])
api_v1_router.include_router(workflows.router, prefix="/workflows", tags=["Workflows"])
api_v1_router.include_router(
    workflows.project_workflows_router,
    prefix="/projects/{project_id}/workflows",
    tags=["Workflows"],
)

