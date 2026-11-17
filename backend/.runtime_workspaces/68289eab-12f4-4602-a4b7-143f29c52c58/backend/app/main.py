from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, HTMLResponse
import os

from app.config import settings
from app.api import router as shadow_router

app = FastAPI(
    title="Shadow Duel",
    description="A fast‑paced 2D fighting game where players control shadow avatars in dynamic arenas, combining fluid combat mechanics with strategic power‑ups. The game offers single‑player and online multiplayer modes, delivering an immersive experience across mobile and web platforms.",
    version="2.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(shadow_router, prefix="/api")
app.include_router(shadow_router)

@app.get("/health")
def health_check():
    return {"status": "healthy", "app": settings.app_name}

for s_dir in ['frontend', '../frontend', 'static']:
    if os.path.exists(s_dir):
        try:
            app.mount('/static', StaticFiles(directory=s_dir), name='static')
            break
        except Exception:
            pass

@app.get("/")
def serve_root():
    for p in ['frontend/index.html', '../frontend/index.html', 'index.html']:
        if os.path.exists(p):
            return FileResponse(p)
    return HTMLResponse("<h1>Shadow Duel Ready</h1>")

try:
    app.include_router(router)
except Exception:
    pass
