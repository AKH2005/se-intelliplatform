from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, HTMLResponse
import os

from app.config import settings
from app.api import router as scores_router

app = FastAPI(
    title="Carrom Master",
    description="A realistic digital carrom game that offers immersive gameplay, precise physics, and competitive multiplayer modes, allowing players to master the classic board game from any device.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(scores_router, prefix="/api")
app.include_router(scores_router)

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
    return HTMLResponse("<h1>Carrom Master Ready</h1>")
