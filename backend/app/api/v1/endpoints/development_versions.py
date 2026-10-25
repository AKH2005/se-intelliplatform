"""Development Versions REST Endpoints for Phase 11H."""

import uuid
from typing import Annotated
from fastapi import APIRouter, Depends, Path, Query, status
from fastapi.responses import PlainTextResponse

from app.api.dependencies import get_development_version_service
from app.schemas.development_version import (
    ActivateVersionRequest,
    DevelopmentChangeResponse,
    DevelopmentVersionListResponse,
    DevelopmentVersionResponse,
    RollbackVersionRequest,
    RunVerificationRequest,
    VerificationSnapshot,
    VersionComparisonResponse,
)
from app.services.development_version_service import DevelopmentVersionService

router = APIRouter()


@router.get(
    "",
    response_model=DevelopmentVersionListResponse,
    status_code=status.HTTP_200_OK,
    summary="List development versions for project",
    description="Returns all registered software development versions for a project with active pointer marked.",
)
async def list_development_versions(
    project_id: Annotated[uuid.UUID, Path(description="Project UUID")],
    service: Annotated[DevelopmentVersionService, Depends(get_development_version_service)],
) -> DevelopmentVersionListResponse:
    """List all development versions for a project."""
    return await service.list_versions(project_id)


@router.get(
    "/active",
    response_model=DevelopmentVersionResponse | None,
    status_code=status.HTTP_200_OK,
    summary="Get currently active development version",
    description="Retrieves the project's designated active version or None if not yet set.",
)
async def get_active_development_version(
    project_id: Annotated[uuid.UUID, Path(description="Project UUID")],
    service: Annotated[DevelopmentVersionService, Depends(get_development_version_service)],
) -> DevelopmentVersionResponse | None:
    """Get active version for project."""
    return await service.get_active_version(project_id)


@router.get(
    "/compare",
    response_model=VersionComparisonResponse,
    status_code=status.HTTP_200_OK,
    summary="Compare two development versions",
    description="Computes deterministic textual unified diffs and requirement deltas between two versions.",
)
async def compare_development_versions(
    project_id: Annotated[uuid.UUID, Path(description="Project UUID")],
    from_version_id: Annotated[uuid.UUID, Query(description="Origin version UUID", alias="from_version")],
    to_version_id: Annotated[uuid.UUID, Query(description="Target version UUID", alias="to_version")],
    service: Annotated[DevelopmentVersionService, Depends(get_development_version_service)],
) -> VersionComparisonResponse:
    """Compare two versions."""
    return await service.compare_versions(
        project_id=project_id,
        from_version_id=from_version_id,
        to_version_id=to_version_id,
    )


@router.get(
    "/{version_id}",
    response_model=DevelopmentVersionResponse,
    status_code=status.HTTP_200_OK,
    summary="Get development version detail",
    description="Retrieves comprehensive metadata and file manifest for a specific version.",
)
async def get_development_version(
    project_id: Annotated[uuid.UUID, Path(description="Project UUID")],
    version_id: Annotated[uuid.UUID, Path(description="Version UUID")],
    service: Annotated[DevelopmentVersionService, Depends(get_development_version_service)],
) -> DevelopmentVersionResponse:
    """Get version by UUID."""
    return await service.get_version(project_id, version_id)


@router.get(
    "/{version_id}/files/{file_path:path}",
    response_class=PlainTextResponse,
    status_code=status.HTTP_200_OK,
    summary="Get single file content for a version",
    description="Retrieves the exact UTF-8 source content of a file belonging to this version.",
)
async def get_development_version_file_content(
    project_id: Annotated[uuid.UUID, Path(description="Project UUID")],
    version_id: Annotated[uuid.UUID, Path(description="Version UUID")],
    file_path: Annotated[str, Path(description="Project-relative file path")],
    service: Annotated[DevelopmentVersionService, Depends(get_development_version_service)],
) -> str:
    """Fetch file source code."""
    return await service.get_version_file_content(project_id, version_id, file_path)


@router.get(
    "/{version_id}/verification",
    response_model=VerificationSnapshot,
    status_code=status.HTTP_200_OK,
    summary="Get detailed verification snapshot for version",
    description="Retrieves granular multi-stage verification status and blocking issues.",
)
async def get_development_version_verification(
    project_id: Annotated[uuid.UUID, Path(description="Project UUID")],
    version_id: Annotated[uuid.UUID, Path(description="Version UUID")],
    service: Annotated[DevelopmentVersionService, Depends(get_development_version_service)],
) -> VerificationSnapshot:
    """Retrieve verification snapshot."""
    version = await service.get_version(project_id, version_id)
    if not version.verification_summary:
        # Re-evaluate on-demand if summary not cached
        return await service.reevaluate_verification(project_id, version_id)
    return version.verification_summary


@router.get(
    "/{version_id}/changes",
    response_model=list[DevelopmentChangeResponse],
    status_code=status.HTTP_200_OK,
    summary="Get change history for a version",
    description="Retrieves chronological audit log entries relating to this version.",
)
async def get_development_version_changes(
    project_id: Annotated[uuid.UUID, Path(description="Project UUID")],
    version_id: Annotated[uuid.UUID, Path(description="Version UUID")],
    service: Annotated[DevelopmentVersionService, Depends(get_development_version_service)],
) -> list[DevelopmentChangeResponse]:
    """Retrieve audit changes for version."""
    return await service.list_changes(project_id, version_id)


@router.post(
    "/{version_id}/activate",
    response_model=DevelopmentVersionResponse,
    status_code=status.HTTP_200_OK,
    summary="Explicitly activate a verified development version",
    description="Sets the project-level active version pointer to this version and marks the previous active version superseded.",
)
async def activate_development_version(
    project_id: Annotated[uuid.UUID, Path(description="Project UUID")],
    version_id: Annotated[uuid.UUID, Path(description="Version UUID")],
    service: Annotated[DevelopmentVersionService, Depends(get_development_version_service)],
    request: ActivateVersionRequest | None = None,
) -> DevelopmentVersionResponse:
    """Activate version."""
    reason = request.reason if request else None
    return await service.activate_version(project_id, version_id, reason=reason)


@router.post(
    "/{version_id}/rollback",
    response_model=DevelopmentVersionResponse,
    status_code=status.HTTP_200_OK,
    summary="Roll back active project pointer to a historical verified version",
    description="Non-destructively points the active version to an earlier verified version and records an audit log.",
)
async def rollback_development_version(
    project_id: Annotated[uuid.UUID, Path(description="Project UUID")],
    version_id: Annotated[uuid.UUID, Path(description="Version UUID")],
    service: Annotated[DevelopmentVersionService, Depends(get_development_version_service)],
    request: RollbackVersionRequest | None = None,
) -> DevelopmentVersionResponse:
    """Roll back active version."""
    reason = request.reason if request else None
    return await service.rollback_version(project_id, version_id, reason=reason)


@router.post(
    "/{version_id}/verify",
    response_model=VerificationSnapshot,
    status_code=status.HTTP_200_OK,
    summary="Re-evaluate deterministic verification gate for version",
    description="Recomputes the verification gate rules across static analysis, sandbox, and AI tests without creating a new code version.",
)
async def verify_development_version(
    project_id: Annotated[uuid.UUID, Path(description="Project UUID")],
    version_id: Annotated[uuid.UUID, Path(description="Version UUID")],
    service: Annotated[DevelopmentVersionService, Depends(get_development_version_service)],
    request: RunVerificationRequest | None = None,
) -> VerificationSnapshot:
    """Re-evaluate verification gate."""
    return await service.reevaluate_verification(project_id, version_id)
