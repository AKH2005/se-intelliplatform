"""REST API Endpoints for Multi-Environment Development & Deployment (Phase 13)."""

import logging
import uuid
from fastapi import APIRouter, Depends, Path, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_db
from app.models.environment import EnvironmentType
from app.schemas.environment import (
    DeploymentRecordResponse,
    DeployVersionRequest,
    EnvironmentResponse,
    PromoteVersionRequest,
    PromotionEligibilityResponse,
    RollbackEnvironmentRequest,
)
from app.services.environment_service import EnvironmentService

logger = logging.getLogger(__name__)

router = APIRouter()


def _get_service(session: AsyncSession = Depends(get_db)) -> EnvironmentService:
    return EnvironmentService(session=session)


@router.get(
    "",
    response_model=list[EnvironmentResponse],
    summary="List all environments for project",
)
async def list_environments(
    project_id: uuid.UUID = Path(..., description="Project UUID"),
    service: EnvironmentService = Depends(_get_service),
) -> list[EnvironmentResponse]:
    """Retrieve all project-scoped environments (DEVELOPMENT, STAGING, PRODUCTION)."""
    envs = await service.get_or_create_project_environments(project_id)
    out = []
    for e in envs:
        resp = EnvironmentResponse(
            id=e.id,
            project_id=e.project_id,
            environment_type=e.environment_type,
            name=e.name,
            status=e.status,
            current_version_id=e.current_version_id,
            current_version_number=e.current_version.version_number if e.current_version else None,
            current_version_status=e.current_version.status.value if e.current_version else None,
            current_version_hash=e.current_version.content_hash if e.current_version else None,
            is_production=e.is_production,
            configuration=e.configuration or {},
            last_deployed_at=e.last_deployed_at,
            created_at=e.created_at,
            updated_at=e.updated_at,
        )
        out.append(resp)
    return out


@router.get(
    "/deployments/all",
    response_model=list[DeploymentRecordResponse],
    summary="List all project deployments",
)
async def list_all_project_deployments(
    project_id: uuid.UUID = Path(..., description="Project UUID"),
    limit: int = Query(50, ge=1, le=100),
    service: EnvironmentService = Depends(_get_service),
) -> list[DeploymentRecordResponse]:
    """Retrieve append-only history of all deployments across project environments."""
    records = await service.list_deployments(project_id=project_id, limit=limit)
    out = []
    for r in records:
        out.append(
            DeploymentRecordResponse(
                id=r.id,
                project_id=r.project_id,
                environment_id=r.environment_id,
                environment_type=r.environment.environment_type if r.environment else EnvironmentType.DEVELOPMENT,
                version_id=r.version_id,
                version_number=r.version.version_number if r.version else None,
                previous_version_id=r.previous_version_id,
                previous_version_number=r.previous_version.version_number if r.previous_version else None,
                operation=r.operation,
                source_environment_id=r.source_environment_id,
                source_environment_type=r.source_environment.environment_type if r.source_environment else None,
                status=r.status,
                requested_by=r.requested_by,
                started_at=r.started_at,
                completed_at=r.completed_at,
                verification_summary=r.verification_summary,
                failure_reason=r.failure_reason,
                rollback_target_deployment_id=r.rollback_target_deployment_id,
                metadata_payload=r.metadata_payload or {},
                created_at=r.created_at,
            )
        )
    return out


@router.get(
    "/eligibility",
    response_model=PromotionEligibilityResponse,
    summary="Check promotion eligibility",
)
async def check_promotion_eligibility(
    project_id: uuid.UUID = Path(..., description="Project UUID"),
    version_id: uuid.UUID = Query(..., description="Candidate version UUID"),
    target: EnvironmentType | None = Query(None, description="Target environment type (STAGING or PRODUCTION)"),
    source: EnvironmentType | None = Query(None, description="Optional source environment type"),
    target_environment: EnvironmentType | None = Query(None, description="Target environment type alias"),
    source_environment: EnvironmentType | None = Query(None, description="Source environment type alias"),
    service: EnvironmentService = Depends(_get_service),
) -> PromotionEligibilityResponse:
    """Evaluate deterministic promotion policy for candidate version."""
    dest = target or target_environment
    if not dest:
        from fastapi import HTTPException
        raise HTTPException(status_code=422, detail="Query parameter 'target' or 'target_environment' must be provided.")
    src = source or source_environment
    return await service.check_promotion_eligibility(
        project_id=project_id,
        version_id=version_id,
        target_env_type=dest,
        source_env_type=src,
    )


@router.post(
    "/promote",
    response_model=DeploymentRecordResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Promote version to environment",
)
async def promote_version(
    payload: PromoteVersionRequest,
    project_id: uuid.UUID = Path(..., description="Project UUID"),
    service: EnvironmentService = Depends(_get_service),
) -> DeploymentRecordResponse:
    """Promote a verified version from source to target environment with deterministic gating."""
    r = await service.promote_version(
        project_id=project_id,
        version_id=payload.version_id,
        target_env_type=payload.target_environment,
        source_env_type=payload.source_environment,
        requested_by=payload.requested_by,
        notes=payload.notes,
    )
    return DeploymentRecordResponse(
        id=r.id,
        project_id=r.project_id,
        environment_id=r.environment_id,
        environment_type=r.environment.environment_type if r.environment else payload.target_environment,
        version_id=r.version_id,
        version_number=r.version.version_number if r.version else None,
        previous_version_id=r.previous_version_id,
        previous_version_number=r.previous_version.version_number if r.previous_version else None,
        operation=r.operation,
        source_environment_id=r.source_environment_id,
        source_environment_type=r.source_environment.environment_type if r.source_environment else None,
        status=r.status,
        requested_by=r.requested_by,
        started_at=r.started_at,
        completed_at=r.completed_at,
        verification_summary=r.verification_summary,
        failure_reason=r.failure_reason,
        rollback_target_deployment_id=r.rollback_target_deployment_id,
        metadata_payload=r.metadata_payload or {},
        created_at=r.created_at,
    )


@router.get(
    "/{env_id_or_type}",
    response_model=EnvironmentResponse,
    summary="Get single environment details",
)
async def get_environment_details(
    project_id: uuid.UUID = Path(..., description="Project UUID"),
    env_id_or_type: str = Path(..., description="Environment UUID or EnvironmentType (DEVELOPMENT, STAGING, PRODUCTION)"),
    service: EnvironmentService = Depends(_get_service),
) -> EnvironmentResponse:
    """Retrieve detailed state of a single environment."""
    e = await service.get_environment(project_id, env_id_or_type)
    return EnvironmentResponse(
        id=e.id,
        project_id=e.project_id,
        environment_type=e.environment_type,
        name=e.name,
        status=e.status,
        current_version_id=e.current_version_id,
        current_version_number=e.current_version.version_number if e.current_version else None,
        current_version_status=e.current_version.status.value if e.current_version else None,
        current_version_hash=e.current_version.content_hash if e.current_version else None,
        is_production=e.is_production,
        configuration=e.configuration or {},
        last_deployed_at=e.last_deployed_at,
        created_at=e.created_at,
        updated_at=e.updated_at,
    )


@router.get(
    "/{env_id_or_type}/deployments",
    response_model=list[DeploymentRecordResponse],
    summary="List deployments for environment",
)
async def list_environment_deployments(
    project_id: uuid.UUID = Path(..., description="Project UUID"),
    env_id_or_type: str = Path(..., description="Environment UUID or EnvironmentType"),
    limit: int = Query(50, ge=1, le=100),
    service: EnvironmentService = Depends(_get_service),
) -> list[DeploymentRecordResponse]:
    """Retrieve deployment history for a specific environment."""
    env = await service.get_environment(project_id, env_id_or_type)
    records = await service.list_deployments(project_id=project_id, environment_id=env.id, limit=limit)
    out = []
    for r in records:
        out.append(
            DeploymentRecordResponse(
                id=r.id,
                project_id=r.project_id,
                environment_id=r.environment_id,
                environment_type=env.environment_type,
                version_id=r.version_id,
                version_number=r.version.version_number if r.version else None,
                previous_version_id=r.previous_version_id,
                previous_version_number=r.previous_version.version_number if r.previous_version else None,
                operation=r.operation,
                source_environment_id=r.source_environment_id,
                source_environment_type=r.source_environment.environment_type if r.source_environment else None,
                status=r.status,
                requested_by=r.requested_by,
                started_at=r.started_at,
                completed_at=r.completed_at,
                verification_summary=r.verification_summary,
                failure_reason=r.failure_reason,
                rollback_target_deployment_id=r.rollback_target_deployment_id,
                metadata_payload=r.metadata_payload or {},
                created_at=r.created_at,
            )
        )
    return out


@router.post(
    "/{env_id_or_type}/deploy",
    response_model=DeploymentRecordResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Directly deploy version to environment",
)
async def deploy_to_environment(
    payload: DeployVersionRequest,
    project_id: uuid.UUID = Path(..., description="Project UUID"),
    env_id_or_type: str = Path(..., description="Environment UUID or EnvironmentType"),
    service: EnvironmentService = Depends(_get_service),
) -> DeploymentRecordResponse:
    """Deploy a verified version to an environment."""
    r = await service.deploy_version(
        project_id=project_id,
        environment_id_or_type=env_id_or_type,
        version_id=payload.version_id,
        requested_by=payload.requested_by,
        notes=payload.notes,
    )
    return DeploymentRecordResponse(
        id=r.id,
        project_id=r.project_id,
        environment_id=r.environment_id,
        environment_type=r.environment.environment_type if r.environment else EnvironmentType.DEVELOPMENT,
        version_id=r.version_id,
        version_number=r.version.version_number if r.version else None,
        previous_version_id=r.previous_version_id,
        previous_version_number=r.previous_version.version_number if r.previous_version else None,
        operation=r.operation,
        source_environment_id=r.source_environment_id,
        source_environment_type=r.source_environment.environment_type if r.source_environment else None,
        status=r.status,
        requested_by=r.requested_by,
        started_at=r.started_at,
        completed_at=r.completed_at,
        verification_summary=r.verification_summary,
        failure_reason=r.failure_reason,
        rollback_target_deployment_id=r.rollback_target_deployment_id,
        metadata_payload=r.metadata_payload or {},
        created_at=r.created_at,
    )


@router.post(
    "/{env_id_or_type}/rollback",
    response_model=DeploymentRecordResponse,
    status_code=status.HTTP_200_OK,
    summary="Roll back environment to earlier version",
)
async def rollback_environment(
    payload: RollbackEnvironmentRequest,
    project_id: uuid.UUID = Path(..., description="Project UUID"),
    env_id_or_type: str = Path(..., description="Environment UUID or EnvironmentType"),
    service: EnvironmentService = Depends(_get_service),
) -> DeploymentRecordResponse:
    """Non-destructively roll back an environment to an earlier verified version."""
    r = await service.rollback_environment(
        project_id=project_id,
        environment_id_or_type=env_id_or_type,
        target_version_id=payload.target_version_id,
        requested_by=payload.requested_by,
        reason=payload.reason,
    )
    return DeploymentRecordResponse(
        id=r.id,
        project_id=r.project_id,
        environment_id=r.environment_id,
        environment_type=r.environment.environment_type if r.environment else EnvironmentType.DEVELOPMENT,
        version_id=r.version_id,
        version_number=r.version.version_number if r.version else None,
        previous_version_id=r.previous_version_id,
        previous_version_number=r.previous_version.version_number if r.previous_version else None,
        operation=r.operation,
        source_environment_id=r.source_environment_id,
        source_environment_type=r.source_environment.environment_type if r.source_environment else None,
        status=r.status,
        requested_by=r.requested_by,
        started_at=r.started_at,
        completed_at=r.completed_at,
        verification_summary=r.verification_summary,
        failure_reason=r.failure_reason,
        rollback_target_deployment_id=r.rollback_target_deployment_id,
        metadata_payload=r.metadata_payload or {},
        created_at=r.created_at,
    )
