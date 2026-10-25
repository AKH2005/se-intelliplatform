"""Project Management API Endpoints with Multi-Tenancy & Authorization."""

import uuid
from typing import Annotated, Any
from fastapi import APIRouter, Depends, Query, Response, status

from app.api.dependencies import (
    get_current_user_optional,
    get_project_download_service,
    get_project_service,
)
from app.core.exceptions import ForbiddenError
from app.models.project import ProjectStatus
from app.models.user import User
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
    current_user: Annotated[User | None, Depends(get_current_user_optional)] = None,
) -> ProjectResponse:
    owner_id = current_user.id if current_user else None
    project = await service.create_project(project_in, owner_id=owner_id)
    return ProjectResponse.model_validate(project)


@router.get(
    "",
    response_model=list[ProjectResponse],
    summary="List all projects",
    description="Retrieves a paginated list of projects, optionally filtered by lifecycle status.",
)
async def list_projects(
    service: Annotated[ProjectService, Depends(get_project_service)],
    current_user: Annotated[User | None, Depends(get_current_user_optional)] = None,
    skip: Annotated[int, Query(ge=0, description="Offset for pagination")] = 0,
    limit: Annotated[int, Query(ge=1, le=100, description="Maximum items to return")] = 50,
    status: Annotated[ProjectStatus | None, Query(description="Filter by project status")] = None,
) -> list[ProjectResponse]:
    owner_id = current_user.id if current_user else None
    projects, _ = await service.list_projects(skip=skip, limit=limit, status=status, owner_id=owner_id)
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
    current_user: Annotated[User | None, Depends(get_current_user_optional)] = None,
) -> ProjectResponse:
    project = await service.get_by_id(project_id)
    if project.owner_id is not None:
        if current_user is None or project.owner_id != current_user.id:
            raise ForbiddenError("You do not have permission to access this project.")
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
    current_user: Annotated[User | None, Depends(get_current_user_optional)] = None,
) -> ProjectResponse:
    project = await service.get_by_id(project_id)
    if project.owner_id is not None:
        if current_user is None or project.owner_id != current_user.id:
            raise ForbiddenError("You do not have permission to modify this project.")
    updated_project = await service.update_project(project_id, project_in)
    return ProjectResponse.model_validate(updated_project)


@router.delete(
    "/{project_id}",
    response_model=ProjectResponse,
    summary="Archive project (Soft Delete)",
    description="Safely archives a project, preserving its historical context without physical data loss.",
)
async def archive_project(
    project_id: uuid.UUID,
    service: Annotated[ProjectService, Depends(get_project_service)],
    current_user: Annotated[User | None, Depends(get_current_user_optional)] = None,
) -> ProjectResponse:
    project = await service.get_by_id(project_id)
    if project.owner_id is not None:
        if current_user is None or project.owner_id != current_user.id:
            raise ForbiddenError("You do not have permission to archive this project.")
    archived_project = await service.archive_project(project_id)
    return ProjectResponse.model_validate(archived_project)


@router.get(
    "/{project_id}/download",
    summary="Download project code as ZIP archive",
    description="Generates and streams an authenticated, security-filtered ZIP archive containing all project source files.",
    responses={
        200: {
            "content": {"application/zip": {}},
            "description": "Project source code ZIP archive.",
        }
    },
)
async def download_project_code(
    project_id: uuid.UUID,
    download_service: Annotated[Any, Depends(get_project_download_service)],
    current_user: Annotated[User | None, Depends(get_current_user_optional)] = None,
    version_id: Annotated[uuid.UUID | None, Query(description="Optional specific version UUID")] = None,
) -> Response:
    """Download the complete source package for an authorized project."""
    zip_bytes, zip_filename = await download_service.generate_project_zip(
        project_id=project_id,
        version_id=version_id,
        user=current_user,
    )
    return Response(
        content=zip_bytes,
        media_type="application/zip",
        headers={
            "Content-Disposition": f'attachment; filename="{zip_filename}"',
            "Content-Length": str(len(zip_bytes)),
        },
    )


@router.post(
    "/{project_id}/restore",
    response_model=ProjectResponse,
    summary="Restore an archived project",
    description="Restores an archived project back to active IN_PROGRESS status.",
)
async def restore_project(
    project_id: uuid.UUID,
    service: Annotated[ProjectService, Depends(get_project_service)],
    current_user: Annotated[User | None, Depends(get_current_user_optional)] = None,
) -> ProjectResponse:
    project = await service.get_by_id(project_id)
    if project.owner_id is not None:
        if current_user is None or project.owner_id != current_user.id:
            raise ForbiddenError("You do not have permission to restore this project.")
    restored = await service.restore_project(project_id)
    return ProjectResponse.model_validate(restored)


@router.post(
    "/{project_id}/duplicate",
    response_model=ProjectResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Duplicate a project",
    description="Clones the project metadata, settings, and canonical requirements into a new project.",
)
async def duplicate_project(
    project_id: uuid.UUID,
    service: Annotated[ProjectService, Depends(get_project_service)],
    current_user: Annotated[User | None, Depends(get_current_user_optional)] = None,
) -> ProjectResponse:
    project = await service.get_by_id(project_id)
    if project.owner_id is not None:
        if current_user is None or project.owner_id != current_user.id:
            raise ForbiddenError("You do not have permission to duplicate this project.")
    owner_id = current_user.id if current_user else None
    duplicated = await service.duplicate_project(project_id, owner_id=owner_id)
    return ProjectResponse.model_validate(duplicated)


@router.delete(
    "/{project_id}/permanent",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Permanently delete project",
    description="Physically and permanently deletes a project and all associated cascades.",
)
async def permanent_delete_project(
    project_id: uuid.UUID,
    service: Annotated[ProjectService, Depends(get_project_service)],
    current_user: Annotated[User | None, Depends(get_current_user_optional)] = None,
) -> None:
    project = await service.get_by_id(project_id)
    if project.owner_id is not None:
        if current_user is None or project.owner_id != current_user.id:
            raise ForbiddenError("You do not have permission to delete this project.")
    await service.hard_delete_project(project_id)


@router.get(
    "/{project_id}/activity",
    response_model=list[dict[str, Any]],
    summary="Get project activity timeline",
    description="Retrieves a chronological audit log of meaningful project lifecycle events.",
)
async def get_project_activity(
    project_id: uuid.UUID,
    service: Annotated[ProjectService, Depends(get_project_service)],
    current_user: Annotated[User | None, Depends(get_current_user_optional)] = None,
) -> list[dict[str, Any]]:
    project = await service.get_by_id(project_id)
    if project.owner_id is not None:
        if current_user is None or project.owner_id != current_user.id:
            raise ForbiddenError("You do not have permission to view activity for this project.")
    return await service.get_activity_history(project_id)

