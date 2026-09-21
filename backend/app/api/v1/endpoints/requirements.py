"""Requirement Management API Endpoints."""

import uuid
from typing import Annotated
from fastapi import APIRouter, Depends, Query, status

from app.api.dependencies import get_requirement_service
from app.models.requirement import (
    RequirementPriority,
    RequirementStatus,
    RequirementType,
)
from app.schemas.requirement import (
    RequirementCreate,
    RequirementResponse,
    RequirementUpdate,
)
from app.services.requirement_service import RequirementService

router = APIRouter()


@router.post(
    "",
    response_model=RequirementResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a project requirement",
    description="Registers a new requirement belonging to the specified project.",
)
async def create_requirement(
    project_id: uuid.UUID,
    req_in: RequirementCreate,
    service: Annotated[RequirementService, Depends(get_requirement_service)],
) -> RequirementResponse:
    requirement = await service.create_requirement(project_id, req_in)
    return RequirementResponse.model_validate(requirement)


@router.get(
    "",
    response_model=list[RequirementResponse],
    summary="List project requirements",
    description="Retrieves a paginated list of requirements for a project, with optional domain filtering.",
)
async def list_requirements(
    project_id: uuid.UUID,
    service: Annotated[RequirementService, Depends(get_requirement_service)],
    skip: Annotated[int, Query(ge=0, description="Offset for pagination")] = 0,
    limit: Annotated[int, Query(ge=1, le=100, description="Maximum items to return")] = 50,
    type: Annotated[RequirementType | None, Query(description="Filter by requirement type")] = None,
    priority: Annotated[RequirementPriority | None, Query(description="Filter by priority")] = None,
    req_status: Annotated[RequirementStatus | None, Query(alias="status", description="Filter by lifecycle status")] = None,
    include_archived: Annotated[bool, Query(description="Whether to include archived requirements")] = False,
) -> list[RequirementResponse]:
    requirements, _ = await service.list_requirements(
        project_id=project_id,
        skip=skip,
        limit=limit,
        type=type,
        priority=priority,
        status=req_status,
        include_archived=include_archived,
    )
    return [RequirementResponse.model_validate(r) for r in requirements]


@router.get(
    "/{requirement_id}",
    response_model=RequirementResponse,
    summary="Get requirement by ID",
    description="Retrieves detailed metadata for a specific requirement scoped to the project.",
)
async def get_requirement(
    project_id: uuid.UUID,
    requirement_id: uuid.UUID,
    service: Annotated[RequirementService, Depends(get_requirement_service)],
) -> RequirementResponse:
    requirement = await service.get_by_id(project_id, requirement_id)
    return RequirementResponse.model_validate(requirement)


@router.patch(
    "/{requirement_id}",
    response_model=RequirementResponse,
    summary="Update requirement",
    description="Applies partial updates to a project requirement.",
)
async def update_requirement(
    project_id: uuid.UUID,
    requirement_id: uuid.UUID,
    update_in: RequirementUpdate,
    service: Annotated[RequirementService, Depends(get_requirement_service)],
) -> RequirementResponse:
    requirement = await service.update_requirement(project_id, requirement_id, update_in)
    return RequirementResponse.model_validate(requirement)


@router.delete(
    "/{requirement_id}",
    response_model=RequirementResponse,
    summary="Archive requirement (Soft Delete)",
    description="Safely archives a requirement, preserving its historical context for future SDLC intelligence.",
)
async def archive_requirement(
    project_id: uuid.UUID,
    requirement_id: uuid.UUID,
    service: Annotated[RequirementService, Depends(get_requirement_service)],
) -> RequirementResponse:
    requirement = await service.archive_requirement(project_id, requirement_id)
    return RequirementResponse.model_validate(requirement)
