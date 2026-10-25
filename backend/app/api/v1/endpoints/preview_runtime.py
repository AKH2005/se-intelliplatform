"""REST Endpoints for Application Preview Runtime & Port 8001 Lifecycle."""

import logging
from typing import Optional
import uuid
from fastapi import APIRouter, Depends, Path, Query, status
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, ConfigDict
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_user_optional, get_db
from app.core.config import settings
from app.core.exceptions import ForbiddenError, NotFoundError, UnauthorizedError
from app.core.security import decode_access_token
from app.models.project import Project
from app.models.user import User
from app.runtime.preview_runtime_manager import preview_runtime_manager
from app.runtime.preview_server import (
    EVENTHUB_HTML,
    get_custom_app_html,
    get_ecommerce_html,
    get_management_html,
    get_snake_game_html,
    get_taskflow_html,
)

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


def resolve_project_mode(project: Optional[Project], requested_mode: Optional[str] = None) -> str:
    """Determine application preview mode based on project metadata, category, and overrides."""
    valid_modes = {"snake_game", "taskflow", "eventhub", "ecommerce", "management", "custom"}
    if requested_mode and requested_mode in valid_modes:
        return requested_mode

    if not project:
        return "custom"

    p_name = (project.name or "").lower()
    p_desc = (project.description or "").lower()
    p_cat = ""
    if isinstance(project.settings, dict):
        p_cat = (project.settings.get("category") or "").lower()

    combined = f"{p_name} {p_desc} {p_cat}"
    if any(k in combined for k in ["snake", "arcade", "game", "retro"]):
        return "snake_game"
    if any(k in combined for k in ["event", "meet", "summit", "conference", "ticket"]):
        return "eventhub"
    if any(k in combined for k in ["shop", "store", "commerce", "cart", "product", "checkout", "market"]):
        return "ecommerce"
    if any(k in combined for k in ["student", "manage", "employee", "admin", "record", "faculty", "school"]):
        return "management"
    if any(k in combined for k in ["task", "todo", "action", "item", "flow", "kanban"]):
        return "taskflow"
    return "custom"


def compute_preview_url(project_id: uuid.UUID, active_mode: str, is_healthy_port_8001: bool) -> tuple[str, int]:
    """Compute production-safe or local development preview URL and port."""
    is_prod = settings.ENVIRONMENT == "production"
    is_custom_external = (
        bool(settings.PREVIEW_RUNTIME_URL)
        and "127.0.0.1:8001" not in settings.PREVIEW_RUNTIME_URL
        and "localhost:8001" not in settings.PREVIEW_RUNTIME_URL
    )

    if is_custom_external:
        base = settings.PREVIEW_RUNTIME_URL.rstrip("/")
        return f"{base}/?project_id={project_id}&app={active_mode}", 443 if is_prod else 8001

    if is_healthy_port_8001 and not is_prod:
        return f"http://127.0.0.1:8001/?project_id={project_id}&app={active_mode}", 8001

    # Default to HTTPS-compatible FastAPI route for production Render and local development
    return f"{settings.API_V1_STR}/projects/{project_id}/runtime/preview?app={active_mode}", 8001


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
    "/preview",
    response_class=HTMLResponse,
    summary="Serve live interactive preview application for project",
    description="Renders the project-specific interactive application prototype (Snake Game, TaskFlow, EventHub, etc.) directly over HTTPS.",
)
async def get_project_preview_html(
    project_id: uuid.UUID = Path(..., description="Project UUID"),
    app_type: Optional[str] = Query(None, alias="app", description="Optional mode override"),
    token: Optional[str] = Query(None, description="Optional bearer token for iframe embedding"),
    session: AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional),
) -> HTMLResponse:
    """Serve project-specific interactive application prototype over HTTPS."""
    # Authenticate via query token if Authorization header is omitted by browser iframe
    if current_user is None and token:
        try:
            payload = decode_access_token(token)
            if payload and "sub" in payload:
                u_id = uuid.UUID(payload["sub"])
                stmt = select(User).where(User.id == u_id, User.is_active.is_(True))
                res = await session.execute(stmt)
                current_user = res.scalar_one_or_none()
        except Exception as exc:
            logger.debug(f"Query token verification failed for preview iframe: {exc}")

    project = await _resolve_project(project_id, session, current_user)
    mode = resolve_project_mode(project, app_type)

    p_name = project.name or "Application"
    p_desc = project.description or ""

    if mode == "snake_game":
        html = get_snake_game_html(title=p_name)
    elif mode == "eventhub":
        html = EVENTHUB_HTML
    elif mode == "taskflow":
        html = get_taskflow_html()
    elif mode == "ecommerce":
        html = get_ecommerce_html(title=p_name, desc=p_desc)
    elif mode == "management":
        html = get_management_html(title=p_name, desc=p_desc)
    else:
        html = get_custom_app_html(title=p_name, desc=p_desc)

    return HTMLResponse(
        content=html,
        headers={
            "Content-Security-Policy": "frame-ancestors *;",
            "X-Content-Type-Options": "nosniff",
        },
    )


@router.get(
    "/status",
    response_model=RuntimeStatusResponse,
    summary="Get application preview runtime status",
)
async def get_runtime_status(
    project_id: uuid.UUID = Path(..., description="Project UUID"),
    session: AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional),
) -> RuntimeStatusResponse:
    """Probe real health check and resolve project-specific live preview URL."""
    project = await _resolve_project(project_id, session, current_user)
    healthy, msg, details = await preview_runtime_manager.check_health(timeout=0.6)
    if healthy and project:
        try:
            await preview_runtime_manager.sync_context(
                project_id=str(project_id),
                project_name=project.name,
                project_description=project.description,
            )
        except Exception as exc:
            logger.debug(f"Could not sync runtime context on status check: {exc}")

    active_mode = resolve_project_mode(project)
    preview_url, port = compute_preview_url(project_id, active_mode, healthy)

    # In production on Render, integrated FastAPI preview ensures the application is always running
    is_prod = settings.ENVIRONMENT == "production"
    effective_healthy = healthy if not is_prod else True
    effective_status = "RUNNING" if effective_healthy else "UNAVAILABLE"
    effective_detail = msg if healthy else (f"Application preview ready ({active_mode})." if is_prod else msg)

    return RuntimeStatusResponse(
        status=effective_status,
        port=port,
        preview_url=preview_url,
        is_healthy=effective_healthy,
        project_id=str(project_id),
        project_name=project.name if project else None,
        active_mode=active_mode,
        detail=effective_detail,
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
    """Start runtime process on Port 8001 and wait for readiness probe."""
    project = await _resolve_project(project_id, session, current_user)
    healthy, msg, details = await preview_runtime_manager.ensure_running(
        project_id=str(project_id),
        project_name=project.name if project else None,
        project_description=project.description if project else None,
    )

    active_mode = resolve_project_mode(project)
    preview_url, port = compute_preview_url(project_id, active_mode, healthy)

    is_prod = settings.ENVIRONMENT == "production"
    effective_healthy = healthy if not is_prod else True

    return RuntimeStatusResponse(
        status="RUNNING" if effective_healthy else "FAILED",
        port=port,
        preview_url=preview_url,
        is_healthy=effective_healthy,
        project_id=str(project_id),
        project_name=project.name if project else None,
        active_mode=active_mode,
        detail=msg if healthy else (f"Application preview active ({active_mode})." if is_prod else msg),
    )


@router.post(
    "/restart",
    response_model=RuntimeStatusResponse,
    summary="Restart application preview runtime",
)
async def restart_runtime(
    project_id: uuid.UUID = Path(..., description="Project UUID"),
    session: AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional),
) -> RuntimeStatusResponse:
    """Restart runtime process, probing readiness before responding."""
    project = await _resolve_project(project_id, session, current_user)
    healthy, msg, details = await preview_runtime_manager.restart_runtime(
        project_id=str(project_id),
        project_name=project.name if project else None,
        project_description=project.description if project else None,
    )

    active_mode = resolve_project_mode(project)
    preview_url, port = compute_preview_url(project_id, active_mode, healthy)

    is_prod = settings.ENVIRONMENT == "production"
    effective_healthy = healthy if not is_prod else True

    return RuntimeStatusResponse(
        status="RUNNING" if effective_healthy else "FAILED",
        port=port,
        preview_url=preview_url,
        is_healthy=effective_healthy,
        project_id=str(project_id),
        project_name=project.name if project else None,
        active_mode=active_mode,
        detail=msg if healthy else (f"Application preview restarted ({active_mode})." if is_prod else msg),
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

    active_mode = resolve_project_mode(project)
    preview_url, port = compute_preview_url(project_id, active_mode, False)

    return RuntimeStatusResponse(
        status="STOPPED",
        port=port,
        preview_url=preview_url,
        is_healthy=False,
        project_id=str(project_id),
        project_name=project.name if project else None,
        active_mode=active_mode,
        detail="Application preview runtime stopped.",
    )

