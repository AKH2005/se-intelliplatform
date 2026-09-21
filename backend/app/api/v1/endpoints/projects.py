"""Project Management API Endpoints."""

import uuid
from typing import Annotated
from fastapi import APIRouter, Depends, Query, status

from app.api.dependencies import get_project_service
from app.models.project import ProjectStatus
from app.schemas.project import ProjectCreate, ProjectResponse, ProjectUpdate
from app.services.project_service import ProjectService

router = APIRouter()


@router.post(
    "",
    response_model=ProjectResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new project",
    description="Registers a new project with a unique slug and initialized configuration settings.",
)
async def create_project(
    project_in: ProjectCreate,
    service: Annotated[ProjectService, Depends(get_project_service)],
) -> ProjectResponse:
    project = await service.create_project(project_in)
    return ProjectResponse.model_validate(project)


@router.get(
    "",
    response_model=list[ProjectResponse],
    summary="List all projects",
    description="Retrieves a paginated list of projects, optionally filtered by lifecycle status.",
)
async def list_projects(
    service: Annotated[ProjectService, Depends(get_project_service)],
    skip: Annotated[int, Query(ge=0, description="Offset for pagination")] = 0,
    limit: Annotated[int, Query(ge=1, le=100, description="Maximum items to return")] = 50,
    status: Annotated[ProjectStatus | None, Query(description="Filter by project status")] = None,
) -> list[ProjectResponse]:
    projects, _ = await service.list_projects(skip=skip, limit=limit, status=status)
    return [ProjectResponse.model_validate(p) for p in projects]


@router.get(
    "/{project_id}",
    response_model=ProjectResponse,
    summary="Get project by ID",
    description="Fetches detailed project metadata for a specific project UUID.",
)
async def get_project(
    project_id: uuid.UUID,
    service: Annotated[ProjectService, Depends(get_project_service)],
) -> ProjectResponse:
    project = await service.get_by_id(project_id)
    return ProjectResponse.model_validate(project)


@router.patch(
    "/{project_id}",
    response_model=ProjectResponse,
    summary="Update project metadata",
    description="Applies partial updates to an existing project's attributes.",
)
async def update_project(
    project_id: uuid.UUID,
    project_in: ProjectUpdate,
    service: Annotated[ProjectService, Depends(get_project_service)],
) -> ProjectResponse:
    project = await service.update_project(project_id, project_in)
    return ProjectResponse.model_validate(project)


@router.delete(
    "/{project_id}",
    response_model=ProjectResponse,
    summary="Archive project (Soft Delete)",
    description="Safely archives a project, preserving its historical context without physical data loss.",
)
async def archive_project(
    project_id: uuid.UUID,
    service: Annotated[ProjectService, Depends(get_project_service)],
) -> ProjectResponse:
    project = await service.archive_project(project_id)
    return ProjectResponse.model_validate(project)
