"""REST Endpoints for Application Preview Runtime & Port 8001 Lifecycle."""

import logging
from typing import Optional
import uuid
from fastapi import APIRouter, Depends, Path, Query, status
from pydantic import BaseModel, ConfigDict
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_user_optional, get_db
from app.core.config import settings
from app.core.exceptions import ForbiddenError, NotFoundError, UnauthorizedError
from app.models.project import Project
from app.models.user import User
from app.runtime.preview_runtime_manager import preview_runtime_manager

logger = logging.getLogger(__name__)

router = APIRouter()


class RuntimeStatusResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")

    status: str  # "RUNNING", "READY", "UNAVAILABLE", "STARTING", "BUILDING", "FAILED", "STOPPED", "IDLE"
    port: int = 8001
    preview_url: str = settings.PREVIEW_RUNTIME_URL
    is_healthy: bool
    project_id: Optional[str] = None
    project_name: Optional[str] = None
    active_mode: str = "taskflow"
    detail: str


async def _resolve_project(
    project_id: uuid.UUID,
    session: AsyncSession,
    user: Optional[User] = None,
) -> Project:
    stmt = select(Project).where(Project.id == project_id)
    res = await session.execute(stmt)
    proj = res.scalar_one_or_none()
    if not proj:
        raise NotFoundError("Project", str(project_id))

    if proj.owner_id is not None:
        if user is None:
            raise UnauthorizedError("Authentication required to access this project's preview runtime")
        if proj.owner_id != user.id:
            raise ForbiddenError("You do not have permission to access this project's preview runtime")

    return proj


@router.get(
    "/status",
    response_model=RuntimeStatusResponse,
    summary="Get application preview runtime status on Port 8001",
)
async def get_runtime_status(
    project_id: uuid.UUID = Path(..., description="Project UUID"),
    session: AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional),
) -> RuntimeStatusResponse:
    """Probe real health check of the port 8001 application preview runtime."""
    project = await _resolve_project(project_id, session, current_user)
    healthy, msg, details = await preview_runtime_manager.check_health(timeout=1.0)
    if healthy and project:
        try:
            await preview_runtime_manager.sync_context(
                project_id=str(project_id),
                project_name=project.name,
                project_description=project.description,
            )
        except Exception as exc:
            logger.debug(f"Could not sync runtime context on status check: {exc}")

    # Determine mode
    p_name = (project.name if project else "").lower()
    p_desc = (project.description if project and project.description else "").lower()
    if any(k in p_name or k in p_desc for k in ["task", "todo"]):
        active_mode = "taskflow"
    elif any(k in p_name or k in p_desc for k in ["event"]):
        active_mode = "eventhub"
    elif any(k in p_name or k in p_desc for k in ["snake", "game"]):
        active_mode = "snake_game"
    elif any(k in p_name or k in p_desc for k in ["shop", "store", "commerce", "cart", "product"]):
        active_mode = "ecommerce"
    elif any(k in p_name or k in p_desc for k in ["student", "manage", "employee", "admin"]):
        active_mode = "management"
    else:
        active_mode = details.get("active_mode", "taskflow")

    return RuntimeStatusResponse(
        status="RUNNING" if healthy else "UNAVAILABLE",
        port=8001,
        preview_url=settings.PREVIEW_RUNTIME_URL,
        is_healthy=healthy,
        project_id=str(project_id),
        project_name=project.name if project else None,
        active_mode=active_mode,
        detail=msg,
    )


@router.post(
    "/start",
    response_model=RuntimeStatusResponse,
    summary="Ensure application preview runtime is started and verified healthy",
)
async def start_runtime(
    project_id: uuid.UUID = Path(..., description="Project UUID"),
    session: AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional),
) -> RuntimeStatusResponse:
    """Start runtime process on Port 8001 and wait for successful readiness health probe."""
    project = await _resolve_project(project_id, session, current_user)
    healthy, msg, details = await preview_runtime_manager.ensure_running(
        project_id=str(project_id),
        project_name=project.name if project else None,
        project_description=project.description if project else None,
    )

    p_name = (project.name if project else "").lower()
    p_desc = (project.description if project and project.description else "").lower()
    if any(k in p_name or k in p_desc for k in ["task", "todo"]):
        active_mode = "taskflow"
    elif any(k in p_name or k in p_desc for k in ["event"]):
        active_mode = "eventhub"
    elif any(k in p_name or k in p_desc for k in ["snake", "game"]):
        active_mode = "snake_game"
    elif any(k in p_name or k in p_desc for k in ["shop", "store", "commerce", "cart", "product"]):
        active_mode = "ecommerce"
    elif any(k in p_name or k in p_desc for k in ["student", "manage", "employee", "admin"]):
        active_mode = "management"
    else:
        active_mode = details.get("active_mode", "taskflow")

    return RuntimeStatusResponse(
        status="RUNNING" if healthy else "FAILED",
        port=8001,
        preview_url=settings.PREVIEW_RUNTIME_URL,
        is_healthy=healthy,
        project_id=str(project_id),
        project_name=project.name if project else None,
        active_mode=active_mode,
        detail=msg,
    )


@router.post(
    "/restart",
    response_model=RuntimeStatusResponse,
    summary="Restart application preview runtime on Port 8001",
)
async def restart_runtime(
    project_id: uuid.UUID = Path(..., description="Project UUID"),
    session: AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional),
) -> RuntimeStatusResponse:
    """Terminate and re-spawn runtime process, probing readiness health before responding."""
    project = await _resolve_project(project_id, session, current_user)
    healthy, msg, details = await preview_runtime_manager.restart_runtime(
        project_id=str(project_id),
        project_name=project.name if project else None,
        project_description=project.description if project else None,
    )

    p_name = (project.name if project else "").lower()
    p_desc = (project.description if project and project.description else "").lower()
    if any(k in p_name or k in p_desc for k in ["task", "todo"]):
        active_mode = "taskflow"
    elif any(k in p_name or k in p_desc for k in ["event"]):
        active_mode = "eventhub"
    elif any(k in p_name or k in p_desc for k in ["snake", "game"]):
        active_mode = "snake_game"
    elif any(k in p_name or k in p_desc for k in ["shop", "store", "commerce", "cart", "product"]):
        active_mode = "ecommerce"
    elif any(k in p_name or k in p_desc for k in ["student", "manage", "employee", "admin"]):
        active_mode = "management"
    else:
        active_mode = details.get("active_mode", "taskflow")

    return RuntimeStatusResponse(
        status="RUNNING" if healthy else "FAILED",
        port=8001,
        preview_url=settings.PREVIEW_RUNTIME_URL,
        is_healthy=healthy,
        project_id=str(project_id),
        project_name=project.name if project else None,
        active_mode=active_mode,
        detail=msg,
    )


@router.post(
    "/stop",
    response_model=RuntimeStatusResponse,
    summary="Stop application preview runtime process",
)
async def stop_runtime(
    project_id: uuid.UUID = Path(..., description="Project UUID"),
    session: AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional),
) -> RuntimeStatusResponse:
    """Stop runtime process gracefully."""
    project = await _resolve_project(project_id, session, current_user)
    preview_runtime_manager.stop_runtime()

    return RuntimeStatusResponse(
        status="STOPPED",
        port=8001,
        preview_url=settings.PREVIEW_RUNTIME_URL,
        is_healthy=False,
        project_id=str(project_id),
        project_name=project.name if project else None,
        active_mode="taskflow",
        detail="Application preview runtime stopped.",
    )
