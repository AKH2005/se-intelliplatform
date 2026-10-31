"""Project Files and Code Studio REST API Endpoints."""

import uuid
from typing import Annotated
from fastapi import APIRouter, Depends, Path, Query, status

from app.api.dependencies import (
    get_current_user_optional,
    get_development_version_service,
)
from app.core.exceptions import ForbiddenError
from app.models.user import User
from app.schemas.code_studio import (
    FileContentResponse,
    FileTreeResponse,
    SaveFileRequest,
    SaveFileResponse,
)
from app.services.development_version_service import DevelopmentVersionService

router = APIRouter()


@router.get(
    "",
    response_model=FileTreeResponse,
    status_code=status.HTTP_200_OK,
    summary="Get hierarchical file tree for project",
    description="Returns a hierarchical directory and file tree for the project's active or specified version.",
)
async def get_project_file_tree(
    project_id: Annotated[uuid.UUID, Path(description="Project UUID")],
    service: Annotated[DevelopmentVersionService, Depends(get_development_version_service)],
    current_user: Annotated[User | None, Depends(get_current_user_optional)] = None,
    version_id: Annotated[uuid.UUID | None, Query(description="Optional specific version UUID")] = None,
) -> FileTreeResponse:
    """Retrieve hierarchical file tree for active or specified version."""
    project = await service._resolve_project(project_id)
    if project.owner_id is not None:
        if current_user is None or project.owner_id != current_user.id:
            raise ForbiddenError("You do not have permission to access files in this project.")
    return await service.get_file_tree(project_id, version_id=version_id)


@router.get(
    "/{file_path:path}",
    response_model=FileContentResponse,
    status_code=status.HTTP_200_OK,
    summary="Get content and metadata for a single project file",
    description="Retrieves the UTF-8 source content, language metadata, and version hashes for a file.",
)
async def get_project_file_content(
    project_id: Annotated[uuid.UUID, Path(description="Project UUID")],
    file_path: Annotated[str, Path(description="Normalized project-relative file path")],
    service: Annotated[DevelopmentVersionService, Depends(get_development_version_service)],
    current_user: Annotated[User | None, Depends(get_current_user_optional)] = None,
    version_id: Annotated[uuid.UUID | None, Query(description="Optional specific version UUID")] = None,
) -> FileContentResponse:
    """Retrieve content of an individual file in active or specified version."""
    project = await service._resolve_project(project_id)
    if project.owner_id is not None:
        if current_user is None or project.owner_id != current_user.id:
            raise ForbiddenError("You do not have permission to access files in this project.")
    return await service.get_file_content_by_path(project_id, file_path=file_path, version_id=version_id)


@router.put(
    "/{file_path:path}",
    response_model=SaveFileResponse,
    status_code=status.HTTP_200_OK,
    summary="Save changes to a file and create an immutable child version",
    description="Validates code syntax, checks optimistic concurrency, preserves unrelated files, and creates an immutable child version.",
)
async def save_project_file_content(
    project_id: Annotated[uuid.UUID, Path(description="Project UUID")],
    file_path: Annotated[str, Path(description="Normalized project-relative file path")],
    request: SaveFileRequest,
    service: Annotated[DevelopmentVersionService, Depends(get_development_version_service)],
    current_user: Annotated[User | None, Depends(get_current_user_optional)] = None,
) -> SaveFileResponse:
    """Safely edit and save a file, creating an immutable child version."""
    return await service.save_file_content(
        project_id=project_id,
        file_path=file_path,
        request=request,
        current_user=current_user,
    )
