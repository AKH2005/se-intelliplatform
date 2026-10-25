from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.core.database import engine, Base
from app.api import (
    auth, departments, students, faculty, courses,
    attendance, assignments, examinations, announcements,
    dashboard, contact
)

# Ensure tables are created
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="UniSphere — Full-Stack University Management System API"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount API V1 Routers
app.include_router(auth.router, prefix=settings.API_V1_PREFIX)
app.include_router(departments.router, prefix=settings.API_V1_PREFIX)
app.include_router(students.router, prefix=settings.API_V1_PREFIX)
app.include_router(faculty.router, prefix=settings.API_V1_PREFIX)
app.include_router(courses.router, prefix=settings.API_V1_PREFIX)
app.include_router(attendance.router, prefix=settings.API_V1_PREFIX)
app.include_router(assignments.router, prefix=settings.API_V1_PREFIX)
app.include_router(examinations.router, prefix=settings.API_V1_PREFIX)
app.include_router(announcements.router, prefix=settings.API_V1_PREFIX)
app.include_router(dashboard.router, prefix=settings.API_V1_PREFIX)
app.include_router(contact.router, prefix=settings.API_V1_PREFIX)

@app.get("/")
def root():
    return {
        "app": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "status": "online",
        "docs_url": "/docs"
    }

@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "timestamp": "2026-10-24T23:59:00Z"
    }
