"""Project Context & Snapshot API Endpoints."""

import uuid
from typing import Annotated
from fastapi import APIRouter, Depends, Query, status

from app.api.dependencies import get_context_engine
from app.schemas.context import (
    ContextSnapshotCreate,
    ContextSnapshotResponse,
    ProjectContextResponse,
)
from app.services.context_engine import ProjectContextEngine

router = APIRouter()


@router.get(
    "",
    response_model=ProjectContextResponse,
    summary="Get canonical project context",
    description=(
        "Assembles and returns the canonical, validated project context representing current state. "
        "Includes active eligible requirements and deterministic statistics."
    ),
)
async def get_project_context(
    project_id: uuid.UUID,
    engine: Annotated[ProjectContextEngine, Depends(get_context_engine)],
) -> ProjectContextResponse:
    return await engine.generate_context(project_id)


@router.post(
    "/snapshots",
    response_model=ContextSnapshotResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create immutable context snapshot",
    description=(
        "Captures and commits an immutable point-in-time snapshot of the canonical project context. "
        "Assigns the next sequential version number for this project."
    ),
)
async def create_context_snapshot(
    project_id: uuid.UUID,
    snapshot_in: ContextSnapshotCreate,
    engine: Annotated[ProjectContextEngine, Depends(get_context_engine)],
) -> ContextSnapshotResponse:
    snapshot = await engine.create_snapshot(project_id, summary=snapshot_in.summary)
    return ContextSnapshotResponse.model_validate(snapshot)


@router.get(
    "/snapshots",
    response_model=list[ContextSnapshotResponse],
    summary="List project context snapshots",
    description="Retrieves historical immutable snapshots for a project ordered by version descending.",
)
async def list_context_snapshots(
    project_id: uuid.UUID,
    engine: Annotated[ProjectContextEngine, Depends(get_context_engine)],
    skip: Annotated[int, Query(ge=0, description="Offset for pagination")] = 0,
    limit: Annotated[int, Query(ge=1, le=100, description="Maximum items to return")] = 50,
) -> list[ContextSnapshotResponse]:
    snapshots, _ = await engine.list_snapshots(project_id=project_id, skip=skip, limit=limit)
    return [ContextSnapshotResponse.model_validate(s) for s in snapshots]


@router.get(
    "/snapshots/{version}",
    response_model=ContextSnapshotResponse,
    summary="Get context snapshot by version",
    description="Retrieves a specific immutable historical snapshot by integer version number.",
)
async def get_context_snapshot_by_version(
    project_id: uuid.UUID,
    version: int,
    engine: Annotated[ProjectContextEngine, Depends(get_context_engine)],
) -> ContextSnapshotResponse:
    snapshot = await engine.get_snapshot_by_version(project_id, version=version)
    return ContextSnapshotResponse.model_validate(snapshot)
