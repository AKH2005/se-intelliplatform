"""API v1 Central Router Aggregator."""

from fastapi import APIRouter

from app.api.v1.endpoints import health, projects

api_v1_router = APIRouter()

api_v1_router.include_router(health.router, tags=["Health"])
api_v1_router.include_router(projects.router, prefix="/projects", tags=["Projects"])
