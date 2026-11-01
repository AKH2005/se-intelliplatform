"""REST Endpoints for Application Preview Runtime & Port 8001 Lifecycle."""

import asyncio
import logging
from typing import Optional
import uuid
from fastapi import APIRouter, Depends, Header, HTTPException, Path, Query, Request, status
from fastapi.responses import HTMLResponse, JSONResponse, Response
from pydantic import BaseModel, ConfigDict
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_user, get_current_user_optional, get_db
from app.core.config import settings
from app.core.exceptions import ForbiddenError, NotFoundError, UnauthorizedError
from app.core.security import PREVIEW_TOKEN_EXPIRE_MINUTES, create_preview_token, decode_access_token, decode_preview_token
from app.models.development_version import DevelopmentVersion
from app.models.project import Project
from app.models.user import User
from app.runtime.preview_runtime_manager import preview_runtime_manager
from app.services.preview_api_service import PreviewApiService
from app.runtime.preview_server import (
    EVENTHUB_HTML,
    get_analytics_dashboard_html,
    get_custom_app_html,
    get_ecommerce_html,
    get_management_html,
    get_snake_game_html,
    get_taskflow_html,
)

logger = logging.getLogger(__name__)

router = APIRouter()


class PreviewTokenResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    preview_token: str
    token_type: str = "Bearer"
    expires_in: int = 900
    project_id: str
    scope: str = "preview"


class RuntimeStatusResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")

    status: str  # "RUNNING", "READY", "UNAVAILABLE", "NOT_STARTED", "STARTING", "BUILD_FAILED", "START_FAILED", "STOPPED", "BLOCKED", "UNKNOWN"
    port: int = 8001
    preview_url: str = settings.PREVIEW_RUNTIME_URL
    preview_token: Optional[str] = None
    is_healthy: bool
    project_id: Optional[str] = None
    project_name: Optional[str] = None
    active_mode: str = "taskflow"
    detail: str
    execution_type: str = "domain_prototype"  # "domain_prototype" | "isolated_container"
    container_status: str = "BLOCKED"  # "NOT_STARTED", "STARTING", "RUNNING", "BUILD_FAILED", "START_FAILED", "STOPPED", "BLOCKED", "UNKNOWN"
    container_detail: Optional[str] = (
        "Isolated container execution requires a running Docker daemon. "
        "Docker is unavailable on this host; custom container execution is safely blocked to protect host security."
    )
    active_version_id: Optional[str] = None
    active_version_number: Optional[int] = None


async def _resolve_active_version_info(project: Optional[Project], session: AsyncSession) -> tuple[Optional[str], Optional[int]]:
    if not project or not project.settings:
        return None, None
    active_id_str = project.settings.get("active_version_id")
    if not active_id_str:
        return None, None
    try:
        active_uuid = uuid.UUID(active_id_str)
        stmt = select(DevelopmentVersion.version_number).where(
            DevelopmentVersion.id == active_uuid,
            DevelopmentVersion.project_id == project.id,
        )
        res = await session.execute(stmt)
        ver_num = res.scalar_one_or_none()
        return active_id_str, ver_num
    except Exception:
        return active_id_str, None



def resolve_project_mode(project: Optional[Project], requested_mode: Optional[str] = None) -> str:
    """Determine application preview mode based on project metadata, category, and overrides."""
    valid_modes = {"analytics", "snake_game", "taskflow", "eventhub", "ecommerce", "management", "custom"}
    if requested_mode and requested_mode in valid_modes:
        return requested_mode

    if not project:
        return "custom"

    p_name = (project.name or "").lower()
    p_desc = (project.description or "").lower()
    p_cat = ""
    if isinstance(project.settings, dict):
        p_arch = (project.settings.get("archetype") or "").lower()
        if p_arch in valid_modes:
            return p_arch
        p_cat = (project.settings.get("category") or "").lower()

    combined = f"{p_name} {p_desc} {p_cat}".lower()
    if any(k in combined for k in ["snake", "arcade", "game", "retro", "2d arcade", "canvas"]):
        return "snake_game"
    if any(k in combined for k in ["teamconnect", "directory", "member", "employee", "roster", "staff", "faculty", "hr"]):
        return "management"
    if any(k in combined for k in ["analytics", "kpi", "dashboard", "metric", "executive", "revenue", "bi ", "intelligence", "finance"]):
        return "analytics"
    if any(k in combined for k in ["event", "meet", "summit", "conference", "ticket", "booking"]):
        return "eventhub"
    if any(k in combined for k in ["shop", "store", "commerce", "cart", "product", "checkout", "market", "catalog"]):
        return "ecommerce"
    if any(k in combined for k in ["kanban", "taskflow", "task-manager", "task manager", "todo", "to-do", "tasks", "task", "backlog", "scrum", "sprint"]):
        return "taskflow"
    if any(k in combined for k in ["team", "manage", "admin", "record", "school", "portal", "profile"]):
        return "management"
    return "custom"


def compute_preview_url(
    project_id: uuid.UUID,
    active_mode: str,
    is_healthy_port_8001: bool,
    preview_token: Optional[str] = None,
) -> tuple[str, int]:
    """Compute production-safe or local development preview URL and port."""
    is_prod = settings.ENVIRONMENT == "production"
    effective_port = 443 if is_prod else 8001
    is_custom_external = (
        bool(settings.PREVIEW_RUNTIME_URL)
        and "127.0.0.1:8001" not in settings.PREVIEW_RUNTIME_URL
        and "localhost:8001" not in settings.PREVIEW_RUNTIME_URL
    )

    token_suffix = f"&preview_token={preview_token}" if preview_token else ""

    if is_custom_external:
        base = settings.PREVIEW_RUNTIME_URL.rstrip("/")
        return f"{base}/?project_id={project_id}&app={active_mode}{token_suffix}", effective_port

    if is_healthy_port_8001 and not is_prod:
        return f"http://127.0.0.1:8001/?project_id={project_id}&app={active_mode}{token_suffix}", 8001

    # Default to HTTPS-compatible FastAPI route for production Render and local development
    return f"{settings.API_V1_STR}/projects/{project_id}/runtime/preview?app={active_mode}{token_suffix}", effective_port


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


@router.post(
    "/preview-token",
    response_model=PreviewTokenResponse,
    summary="Issue short-lived, project-scoped preview token",
)
async def issue_preview_token(
    project_id: uuid.UUID = Path(..., description="Project UUID"),
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> PreviewTokenResponse:
    """Issue a dedicated short-lived token strictly bound to this project, user, and preview scope."""
    project = await _resolve_project(project_id, session, current_user)
    token = create_preview_token(user_id=current_user.id, project_id=project_id)
    return PreviewTokenResponse(
        preview_token=token,
        token_type="Bearer",
        expires_in=PREVIEW_TOKEN_EXPIRE_MINUTES * 60,
        project_id=str(project_id),
        scope="preview",
    )


@router.get(
    "/preview-token",
    response_model=PreviewTokenResponse,
    summary="Issue short-lived, project-scoped preview token (GET)",
)
async def get_preview_token_endpoint(
    project_id: uuid.UUID = Path(..., description="Project UUID"),
    session: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> PreviewTokenResponse:
    """Issue a dedicated short-lived token strictly bound to this project, user, and preview scope."""
    project = await _resolve_project(project_id, session, current_user)
    token = create_preview_token(user_id=current_user.id, project_id=project_id)
    return PreviewTokenResponse(
        preview_token=token,
        token_type="Bearer",
        expires_in=PREVIEW_TOKEN_EXPIRE_MINUTES * 60,
        project_id=str(project_id),
        scope="preview",
    )



def inject_preview_bridge(html_content: str, project_id: str, preview_token: Optional[str] = None) -> str:
    """Inject client-side API bridge and fetch interceptor into preview HTML.

    Ensures relative API calls (/tasks, /api/tasks, /scores, /metrics, etc.) made by
    the generated application or preview prototype carry project identity and route
    seamlessly to the backend without 404 errors.
    """
    token_str = preview_token or ""
    bridge_script = f"""<script id="__SE_PREVIEW_BRIDGE__">
(function() {{
  window.__PREVIEW_PROJECT_ID__ = "{project_id}";
  window.__PREVIEW_TOKEN__ = "{token_str}";
  window.__PREVIEW_API_BASE__ = "/api/v1/projects/{project_id}/runtime/api";

  var origFetch = window.fetch;
  if (!origFetch) return;

  window.fetch = function(input, init) {{
    var url = typeof input === 'string' ? input : (input && input.url ? input.url : '');
    init = init || {{}};
    var headers = new Headers(init.headers || (typeof input === 'object' && input.headers ? input.headers : {{}}));

    if (window.__PREVIEW_PROJECT_ID__ && !headers.has('X-Project-ID')) {{
      headers.set('X-Project-ID', window.__PREVIEW_PROJECT_ID__);
    }}
    if (window.__PREVIEW_TOKEN__ && !headers.has('X-Preview-Token')) {{
      headers.set('X-Preview-Token', window.__PREVIEW_TOKEN__);
    }}
    init.headers = headers;

    var isApi = url.indexOf('/tasks') === 0 || url.indexOf('/api/tasks') === 0 ||
                url.indexOf('/scores') === 0 || url.indexOf('/api/scores') === 0 ||
                url.indexOf('/metrics') === 0 || url.indexOf('/api/metrics') === 0 ||
                url.indexOf('/analytics') === 0 || url.indexOf('/api/analytics') === 0 ||
                url.indexOf('/members') === 0 || url.indexOf('/api/members') === 0 ||
                url.indexOf('/api/auth') === 0 || url.indexOf('/api/events') === 0 ||
                url.indexOf('/api/registrations') === 0 || url.indexOf('/api/ecommerce') === 0;
    if (isApi) {{
      var cleanSubpath = url.indexOf('/api/') === 0 ? url.substring(5) : (url.indexOf('/') === 0 ? url.substring(1) : url);
      var rewrittenUrl = window.__PREVIEW_API_BASE__ + '/' + cleanSubpath;
      if (window.__PREVIEW_TOKEN__ && rewrittenUrl.indexOf('preview_token=') === -1) {{
        rewrittenUrl += (rewrittenUrl.indexOf('?') === -1 ? '?' : '&') + 'preview_token=' + encodeURIComponent(window.__PREVIEW_TOKEN__);
      }}
      return origFetch.call(this, rewrittenUrl, init).catch(function() {{
        return origFetch.call(this, input, init);
      }});
    }}

    return origFetch.call(this, input, init);
  }};
}})();
</script>"""

    if "</head>" in html_content:
        return html_content.replace("</head>", f"{bridge_script}\n</head>", 1)
    if "<body" in html_content:
        return html_content.replace("<body", f"{bridge_script}\n<body", 1)
    return f"{bridge_script}\n{html_content}"


@router.get(
    "/preview",
    response_class=HTMLResponse,
    summary="Serve live interactive preview application for project",
    description="Renders the real generated application or project prototype.",
)
async def get_project_preview_html(
    project_id: uuid.UUID = Path(..., description="Project UUID"),
    app_type: Optional[str] = Query(None, alias="app", description="Optional mode override"),
    mode_override: Optional[str] = Query(None, alias="mode", description="Optional mode override"),
    preview_token: Optional[str] = Query(None, description="Short-lived project-scoped preview token"),
    force_prototype: Optional[bool] = Query(False, description="Force archetype starter prototype"),
    session: AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional),
) -> HTMLResponse:
    """Serve project-specific interactive application prototype or real generated app.

    Security:
    - Never accepts long-lived main access tokens.
    - Requires short-lived token strictly with scope='preview' and matching project_id.
    - Rejects expired, invalid, tampered, and cross-project tokens.
    - Enforces Referrer-Policy: no-referrer and Cache-Control: no-store.
    """
    # 1. Authenticate via short-lived project-scoped preview token
    if current_user is None and preview_token:
        payload = decode_preview_token(preview_token, expected_project_id=project_id)
        if not payload:
            logger.warning("Rejected invalid, expired, cross-project, or untrusted preview token for project %s", project_id)
            raise UnauthorizedError("Invalid, expired, or untrusted preview token")
        try:
            u_id = uuid.UUID(payload["sub"])
            stmt = select(User).where(User.id == u_id, User.is_active.is_(True))
            res = await session.execute(stmt)
            current_user = res.scalar_one_or_none()
            if not current_user:
                raise UnauthorizedError("User associated with preview token is inactive or not found")
        except Exception:
            raise UnauthorizedError("Invalid user identity in preview token")

    # 2. Verify project ownership and tenant isolation
    project = await _resolve_project(project_id, session, current_user)
    effective_mode = app_type or mode_override
    mode = resolve_project_mode(project, effective_mode)

    p_name = project.name or "Application"
    p_desc = project.description or ""

    preview_headers = {
        "Content-Security-Policy": "frame-ancestors 'self' *;",
        "X-Content-Type-Options": "nosniff",
        "Referrer-Policy": "no-referrer",
        "Cache-Control": "no-store, no-cache, must-revalidate, max-age=0",
        "Pragma": "no-cache",
    }

    # 3. Resolve authoritative project files (e.g. from active DevelopmentVersion)
    files_map = {}
    try:
        from app.services.project_download_service import ProjectDownloadService
        pds = ProjectDownloadService(session)
        files_map = await pds.get_project_files(project_id)
    except Exception as exc:
        logger.debug("Could not load project files for preview HTML: %s", exc)
        files_map = {}

    # 4. If project has real generated files and prototype is not explicitly forced, serve actual generated app!
    if files_map and not force_prototype:
        html_content = files_map.get("frontend/index.html") or files_map.get("index.html")
        if not html_content:
            for k, v in files_map.items():
                if k.endswith(".html"):
                    html_content = v
                    break

        if not html_content:
            html_content = (
                f"<!DOCTYPE html><html><head><meta charset='UTF-8'><title>{p_name}</title></head>"
                f"<body style='font-family:sans-serif;padding:2rem;background:#0f172a;color:#f8fafc'>"
                f"<h1>{p_name}</h1><p>{p_desc}</p>"
                f"<p>Application initialized with {len(files_map)} files.</p></body></html>"
            )

        injected_html = inject_preview_bridge(html_content, str(project_id), preview_token)
        return HTMLResponse(content=injected_html, headers=preview_headers)

    # 5. If Port 8001 is active and healthy, proxy live HTML directly from port 8001
    healthy, _, _ = await preview_runtime_manager.check_health(project_id=str(project_id), timeout=2.0)
    if healthy and not effective_mode and not files_map:
        try:
            import urllib.request
            proxy_url = f"http://127.0.0.1:8001/?project_id={project_id}"
            req = urllib.request.Request(proxy_url, headers={"User-Agent": "SE-Preview-Proxy"})
            with urllib.request.urlopen(req, timeout=4.0) as resp:
                content = resp.read().decode("utf-8")
                injected_html = inject_preview_bridge(content, str(project_id), preview_token)
                return HTMLResponse(content=injected_html, headers=preview_headers)
        except Exception as exc:
            logger.debug("Direct proxy from port 8001 failed: %s", exc)

    # 6. Fall back to specialized archetype starter prototype
    if mode == "analytics":
        html = get_analytics_dashboard_html(title=p_name, desc=p_desc, project_id=str(project_id))
    elif mode == "snake_game":
        html = get_snake_game_html(title=p_name)
    elif mode == "eventhub":
        html = EVENTHUB_HTML
    elif mode == "taskflow":
        html = get_taskflow_html(str(project_id))
    elif mode == "ecommerce":
        html = get_ecommerce_html(title=p_name, desc=p_desc)
    elif mode == "management":
        html = get_management_html(title=p_name, desc=p_desc)
    else:
        html = get_custom_app_html(title=p_name, desc=p_desc)

    injected_html = inject_preview_bridge(html, str(project_id), preview_token)
    return HTMLResponse(content=injected_html, headers=preview_headers)


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
    healthy, msg, details = await preview_runtime_manager.check_health(project_id=str(project_id), timeout=0.8)
    if healthy and project and settings.ENVIRONMENT != "production":
        try:
            await preview_runtime_manager.sync_context(
                project_id=str(project_id),
                project_name=project.name,
                project_description=project.description,
            )
        except Exception as exc:
            logger.debug(f"Could not sync runtime context on status check: {exc}")

    active_mode = resolve_project_mode(project)
    is_prod = settings.ENVIRONMENT == "production"

    preview_tok = None
    if current_user is not None:
        preview_tok = create_preview_token(user_id=current_user.id, project_id=project_id)

    preview_url, port = compute_preview_url(project_id, active_mode, healthy, preview_token=preview_tok)
    act_ver_id, act_ver_num = await _resolve_active_version_info(project, session)

    effective_healthy = healthy if not is_prod else True
    status_str = details.get("status") or ("RUNNING" if effective_healthy else "UNAVAILABLE")
    container_status = details.get("container_status") or ("RUNNING" if effective_healthy else "STOPPED")
    execution_type = details.get("execution_type") or "isolated_container"
    effective_detail = details.get("detail") or msg

    return RuntimeStatusResponse(
        status=status_str,
        port=port,
        preview_url=preview_url,
        preview_token=preview_tok,
        is_healthy=effective_healthy,
        project_id=str(project_id),
        project_name=project.name if project else None,
        active_mode=active_mode,
        detail=effective_detail,
        execution_type=execution_type,
        container_status=container_status,
        container_detail=details.get("detail", msg),
        active_version_id=act_ver_id,
        active_version_number=act_ver_num,
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
        force_restart=True,
    )

    active_mode = resolve_project_mode(project)
    is_prod = settings.ENVIRONMENT == "production"

    preview_tok = None
    if current_user is not None:
        preview_tok = create_preview_token(user_id=current_user.id, project_id=project_id)

    preview_url, port = compute_preview_url(project_id, active_mode, healthy, preview_token=preview_tok)
    act_ver_id, act_ver_num = await _resolve_active_version_info(project, session)
    effective_healthy = healthy if not is_prod else True
    status_str = details.get("status") or ("RUNNING" if effective_healthy else "FAILED")
    if effective_healthy and status_str in ("ok", "ready", "SUCCESS"):
        status_str = "RUNNING"
    container_status = details.get("container_status") or ("RUNNING" if effective_healthy else "START_FAILED")
    execution_type = details.get("execution_type") or "isolated_container"

    return RuntimeStatusResponse(
        status=status_str,
        port=port,
        preview_url=preview_url,
        preview_token=preview_tok,
        is_healthy=effective_healthy,
        project_id=str(project_id),
        project_name=project.name if project else None,
        active_mode=active_mode,
        detail=msg if healthy else (f"Application preview active ({active_mode})." if is_prod else msg),
        execution_type=execution_type,
        container_status=container_status,
        container_detail=details.get("detail", msg),
        active_version_id=act_ver_id,
        active_version_number=act_ver_num,
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
    is_prod = settings.ENVIRONMENT == "production"

    preview_tok = None
    if current_user is not None:
        preview_tok = create_preview_token(user_id=current_user.id, project_id=project_id)

    preview_url, port = compute_preview_url(project_id, active_mode, healthy, preview_token=preview_tok)
    act_ver_id, act_ver_num = await _resolve_active_version_info(project, session)
    effective_healthy = healthy if not is_prod else True
    status_str = details.get("status") or ("RUNNING" if effective_healthy else "FAILED")
    if effective_healthy and status_str in ("ok", "ready", "SUCCESS"):
        status_str = "RUNNING"
    container_status = details.get("container_status") or ("RUNNING" if effective_healthy else "START_FAILED")
    execution_type = details.get("execution_type") or "isolated_container"

    return RuntimeStatusResponse(
        status=status_str,
        port=port,
        preview_url=preview_url,
        preview_token=preview_tok,
        is_healthy=effective_healthy,
        project_id=str(project_id),
        project_name=project.name if project else None,
        active_mode=active_mode,
        detail=msg if healthy else (f"Application preview restarted ({active_mode})." if is_prod else msg),
        execution_type=execution_type,
        container_status=container_status,
        container_detail=details.get("detail", msg),
        active_version_id=act_ver_id,
        active_version_number=act_ver_num,
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
    await asyncio.to_thread(preview_runtime_manager.stop_runtime, str(project_id))

    active_mode = resolve_project_mode(project)
    preview_tok = None
    if current_user is not None:
        preview_tok = create_preview_token(user_id=current_user.id, project_id=project_id)

    preview_url, port = compute_preview_url(project_id, active_mode, False, preview_token=preview_tok)
    act_ver_id, act_ver_num = await _resolve_active_version_info(project, session)

    return RuntimeStatusResponse(
        status="STOPPED",
        port=port,
        preview_url=preview_url,
        preview_token=preview_tok,
        is_healthy=False,
        project_id=str(project_id),
        project_name=project.name if project else None,
        active_mode=active_mode,
        detail="Application runtime stopped.",
        execution_type="isolated_container",
        container_status="STOPPED",
        container_detail="Application container stopped.",
        active_version_id=act_ver_id,
        active_version_number=act_ver_num,
    )





@router.api_route(
    "/api/{subpath:path}",
    methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS", "HEAD"],
    summary="Project-scoped Live Preview runtime API proxy",
)
async def project_preview_api_proxy(
    project_id: uuid.UUID = Path(..., description="Project UUID"),
    subpath: str = Path(..., description="API subpath"),
    request: Request = None,
    preview_token: Optional[str] = Query(None, description="Preview token"),
    x_preview_token: Optional[str] = Header(None, alias="X-Preview-Token"),
    session: AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional),
):
    """Serve or proxy project-specific API requests from the preview application."""
    effective_token = preview_token or x_preview_token
    # 1. Authenticate via short-lived preview token if user not signed in
    if current_user is None and effective_token:
        payload = decode_preview_token(effective_token, expected_project_id=project_id)
        if payload:
            try:
                u_id = uuid.UUID(payload["sub"])
                stmt = select(User).where(User.id == u_id, User.is_active.is_(True))
                res = await session.execute(stmt)
                current_user = res.scalar_one_or_none()
            except Exception:
                pass

    # 2. Verify project existence and ownership
    project = await _resolve_project(project_id, session, current_user)
    pid_str = str(project_id)
    method = request.method.upper()

    # Normalize subpath
    norm_subpath = subpath.strip("/")
    if norm_subpath.startswith("api/"):
        norm_subpath = norm_subpath[4:]

    # Handle Tasks
    if norm_subpath == "tasks":
        if method == "GET":
            tasks = await PreviewApiService.get_tasks(pid_str, session=session)
            return JSONResponse(status_code=200, content=tasks)
        elif method == "POST":
            body = await request.json()
            created = await PreviewApiService.create_task(body, pid_str, session=session)
            return JSONResponse(status_code=201, content=created)
    elif norm_subpath.startswith("tasks/"):
        parts = norm_subpath.split("/")
        try:
            task_id = int(parts[1])
        except (IndexError, ValueError):
            raise HTTPException(status_code=400, detail="Invalid task ID")
        if method == "GET":
            t = await PreviewApiService.get_task(task_id, pid_str, session=session)
            if not t:
                raise HTTPException(status_code=404, detail="Task not found")
            return JSONResponse(status_code=200, content=t)
        elif method in ("PUT", "PATCH"):
            body = await request.json()
            t = await PreviewApiService.update_task(task_id, body, pid_str, session=session)
            if not t:
                raise HTTPException(status_code=404, detail="Task not found")
            return JSONResponse(status_code=200, content=t)
        elif method == "DELETE":
            ok = await PreviewApiService.delete_task(task_id, pid_str, session=session)
            if not ok:
                raise HTTPException(status_code=404, detail="Task not found")
            return JSONResponse(status_code=200, content={"status": "DELETED", "id": task_id})

    # Handle Scores (Snake Game)
    elif norm_subpath == "scores":
        if method == "GET":
            scores = await PreviewApiService.get_scores(pid_str, session=session)
            return JSONResponse(status_code=200, content=scores)
        elif method == "POST":
            body = await request.json()
            score = body.get("score", 0)
            player = body.get("player_name") or body.get("player") or "Player 1"
            res = await PreviewApiService.add_score(score, player, pid_str, session=session)
            return JSONResponse(status_code=201, content=res)

    # Handle Metrics (Executive Analytics)
    elif norm_subpath in ("metrics", "analytics") or norm_subpath.startswith("analytics/"):
        metrics = PreviewApiService.get_analytics_metrics(pid_str)
        return JSONResponse(status_code=200, content=metrics)

    # Handle Directory Members (TeamConnect Directory)
    elif norm_subpath in ("members", "directory") or norm_subpath.startswith("members/"):
        if method == "GET":
            members = PreviewApiService.get_directory_members(pid_str)
            return JSONResponse(status_code=200, content=members)
        elif method == "POST":
            body = await request.json()
            new_id = f"mem-{uuid.uuid4().hex[:6]}"
            name_val = body.get("name", "New Team Member")
            initials = "".join([part[0] for part in name_val.split()[:2]]).upper() or "TM"
            new_member = {
                "id": new_id,
                "name": name_val,
                "role": body.get("role", "Software Engineer"),
                "department": body.get("department", "Engineering"),
                "email": body.get("email", f"member@{pid_str[:8]}.team"),
                "status": body.get("status", "ACTIVE"),
                "location": body.get("location", "Remote"),
                "avatar": initials,
                "bio": body.get("bio", "Newly joined team member."),
                "skills": body.get("skills") if isinstance(body.get("skills"), list) else [s.strip() for s in str(body.get("skills", "")).split(",") if s.strip()],
            }
            return JSONResponse(status_code=201, content=new_member)

    # Handle Auth Mock
    elif norm_subpath == "auth/me":
        u_name = current_user.name if current_user else "Preview Developer"
        u_email = current_user.email if current_user else "developer@se-intelliplatform.local"
        u_id = str(current_user.id) if current_user else "preview-user"
        return JSONResponse(status_code=200, content={
            "authenticated": True,
            "user": {"id": u_id, "name": u_name, "email": u_email}
        })
    elif norm_subpath == "auth/login":
        return JSONResponse(status_code=200, content={
            "status": "SUCCESS",
            "token": "preview-jwt-session-token",
            "user": {"name": current_user.name if current_user else "Preview Developer"}
        })
    elif norm_subpath == "auth/logout":
        return JSONResponse(status_code=200, content={"status": "SUCCESS", "message": "Logged out"})

    # Check if Port 8001 is running and healthy; if so, forward proxy
    healthy, _, _ = await preview_runtime_manager.check_health(project_id=pid_str, timeout=1.0)
    if healthy:
        try:
            import urllib.request
            target_url = f"http://127.0.0.1:8001/{subpath}"
            req_data = None
            if method in ("POST", "PUT", "PATCH"):
                req_data = await request.body()
            proxy_req = urllib.request.Request(
                target_url,
                data=req_data if req_data else None,
                headers={"Content-Type": "application/json", "User-Agent": "SE-Preview-Proxy"},
                method=method
            )
            with urllib.request.urlopen(proxy_req, timeout=4.0) as resp:
                resp_bytes = resp.read()
                return Response(
                    content=resp_bytes,
                    status_code=resp.status,
                    media_type=resp.headers.get("Content-Type", "application/json")
                )
        except Exception as exc:
            logger.debug("Proxy forward to Port 8001 failed: %s", exc)

    if norm_subpath in ("registrations", "events"):
        return JSONResponse(status_code=200, content=[])

    raise HTTPException(status_code=404, detail=f"Preview API endpoint '{subpath}' not found")
