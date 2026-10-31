"""Preview Application Root Route Compatibility Handler.

Intercepts root-level API requests (/tasks, /api/tasks, /scores, /metrics, etc.)
issued by Live Preview iframes running under the FastAPI backend origin.
Extracts project context from X-Project-ID, query parameters, or Referer header,
and provides seamless, project-isolated responses via PreviewApiService.
"""

from typing import Any, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_db
from app.services.preview_api_service import PreviewApiService

preview_root_router = APIRouter(tags=["Live Preview Root Compatibility"])


def extract_preview_project_id(request: Request) -> Optional[str]:
    """Resolve project ID from request headers, query string, or Referer."""
    h_pid = request.headers.get("X-Project-ID")
    if h_pid:
        return h_pid.strip()
    q_pid = request.query_params.get("project_id")
    if q_pid:
        return q_pid.strip()
    referer = request.headers.get("referer") or request.headers.get("Referer") or ""
    if "/projects/" in referer:
        try:
            part = referer.split("/projects/")[1].split("/")[0].split("?")[0]
            if len(part) >= 32:
                return part.strip()
        except Exception:
            pass
    return None


# ==========================================
# Tasks APIs
# ==========================================
@preview_root_router.get("/tasks")
@preview_root_router.get("/api/tasks")
async def get_preview_tasks(request: Request, session: AsyncSession = Depends(get_db)):
    project_id = extract_preview_project_id(request)
    tasks = await PreviewApiService.get_tasks(project_id, session=session)
    return JSONResponse(status_code=200, content=tasks)


@preview_root_router.post("/tasks", status_code=status.HTTP_201_CREATED)
@preview_root_router.post("/api/tasks", status_code=status.HTTP_201_CREATED)
async def create_preview_task(request: Request, session: AsyncSession = Depends(get_db)):
    project_id = extract_preview_project_id(request)
    body = await request.json()
    created = await PreviewApiService.create_task(body, project_id, session=session)
    return JSONResponse(status_code=201, content=created)


@preview_root_router.get("/tasks/{task_id}")
@preview_root_router.get("/api/tasks/{task_id}")
async def get_preview_task(task_id: int, request: Request, session: AsyncSession = Depends(get_db)):
    project_id = extract_preview_project_id(request)
    task = await PreviewApiService.get_task(task_id, project_id, session=session)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return JSONResponse(status_code=200, content=task)


@preview_root_router.put("/tasks/{task_id}")
@preview_root_router.put("/api/tasks/{task_id}")
async def update_preview_task(task_id: int, request: Request, session: AsyncSession = Depends(get_db)):
    project_id = extract_preview_project_id(request)
    body = await request.json()
    task = await PreviewApiService.update_task(task_id, body, project_id, session=session)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return JSONResponse(status_code=200, content=task)


@preview_root_router.delete("/tasks/{task_id}")
@preview_root_router.delete("/api/tasks/{task_id}")
async def delete_preview_task(task_id: int, request: Request, session: AsyncSession = Depends(get_db)):
    project_id = extract_preview_project_id(request)
    success = await PreviewApiService.delete_task(task_id, project_id, session=session)
    if not success:
        raise HTTPException(status_code=404, detail="Task not found")
    return JSONResponse(status_code=200, content={"status": "DELETED", "id": task_id})


# ==========================================
# Scores APIs (Snake Game)
# ==========================================
@preview_root_router.get("/scores")
@preview_root_router.get("/api/scores")
async def get_preview_scores(request: Request, session: AsyncSession = Depends(get_db)):
    project_id = extract_preview_project_id(request)
    scores = await PreviewApiService.get_scores(project_id, session=session)
    return JSONResponse(status_code=200, content=scores)


@preview_root_router.post("/scores", status_code=status.HTTP_201_CREATED)
@preview_root_router.post("/api/scores", status_code=status.HTTP_201_CREATED)
async def create_preview_score(request: Request, session: AsyncSession = Depends(get_db)):
    project_id = extract_preview_project_id(request)
    body = await request.json()
    score = body.get("score", 0)
    player = body.get("player_name") or body.get("player") or "Player 1"
    res = await PreviewApiService.add_score(score, player, project_id, session=session)
    return JSONResponse(status_code=201, content=res)


# ==========================================
# Metrics APIs (Executive Analytics)
# ==========================================
@preview_root_router.get("/metrics")
@preview_root_router.get("/api/metrics")
@preview_root_router.get("/api/analytics/{subpath:path}")
async def get_preview_metrics(request: Request):
    project_id = extract_preview_project_id(request)
    metrics = PreviewApiService.get_analytics_metrics(project_id)
    return JSONResponse(status_code=200, content=metrics)


# ==========================================
# Preview Auth Mock
# ==========================================
@preview_root_router.get("/api/auth/me")
async def get_preview_auth_me():
    return JSONResponse(status_code=200, content={
        "authenticated": True,
        "user": {"name": "Developer User", "email": "developer@se-intelliplatform.local"}
    })


@preview_root_router.post("/api/auth/login")
async def preview_auth_login():
    return JSONResponse(status_code=200, content={
        "status": "SUCCESS",
        "token": "preview-session-token",
        "user": {"name": "Developer User"}
    })


@preview_root_router.post("/api/auth/logout")
async def preview_auth_logout():
    return JSONResponse(status_code=200, content={"status": "SUCCESS"})


# ==========================================
# EventHub & E-Commerce Fallbacks
# ==========================================
@preview_root_router.get("/api/registrations")
@preview_root_router.get("/api/events")
async def get_preview_events():
    return JSONResponse(status_code=200, content=[])


@preview_root_router.get("/api/ecommerce/{subpath:path}")
async def get_preview_ecommerce(subpath: str):
    return JSONResponse(status_code=200, content=[])

