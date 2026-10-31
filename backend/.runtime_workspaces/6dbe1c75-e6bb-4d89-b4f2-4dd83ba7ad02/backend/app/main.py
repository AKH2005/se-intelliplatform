"""Main FastAPI entrypoint with CORS and Frontend Root Serving."""

import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from app.config import get_settings
from app.api import router as tasks_router

settings = get_settings()
app = FastAPI(title="Task Item Manager bdd4dd9f", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(tasks_router)


@app.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "healthy", "env": settings.environment}


for s_dir in ["frontend", "../frontend", "static"]:
    if os.path.exists(s_dir):
        app.mount("/static", StaticFiles(directory=s_dir), name="static")
        break


@app.get("/")
def root_index():
    for h_path in ["frontend/index.html", "../frontend/index.html", "index.html"]:
        if os.path.exists(h_path):
            return FileResponse(h_path)
    return HTMLResponse("<h1>Task Item Manager bdd4dd9f</h1>")
