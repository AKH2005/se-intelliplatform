from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
from typing import Optional

router = APIRouter()

class LoginRequest(BaseModel):
    email: str
    password: str

class RegisterRequest(BaseModel):
    email: str
    password: str
    name: Optional[str] = None

@router.post("/api/auth/login")
async def login(req: LoginRequest):
    if not req.email or not req.password:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email and password required")
    return {
        "status": "success",
        "token": "shadow-token-auth-verified-jwt-2026",
        "user": {
            "email": req.email,
            "name": req.email.split("@")[0].capitalize(),
            "level": 12,
            "role": "Shadow Master",
        }
    }

@router.post("/api/auth/register")
async def register(req: RegisterRequest):
    if not req.email or not req.password:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email and password required")
    return {
        "status": "success",
        "token": "shadow-token-registered-jwt-2026",
        "user": {
            "email": req.email,
            "name": req.name or req.email.split("@")[0].capitalize(),
            "level": 1,
            "role": "Executive",
        }
    }

@router.post("/api/auth/logout")
async def logout():
    return {"status": "success", "message": "Logged out successfully"}


@router.get("/api/analytics/filter")
async def filter_analytics(start_date: Optional[str] = None, end_date: Optional[str] = None, metric_type: Optional[str] = None):
    """Filter analytics metrics across specified date ranges."""
    return {
        "status": "success",
        "filter": {
            "start_date": start_date or "2026-01-01",
            "end_date": end_date or "2026-12-31",
            "metric_type": metric_type or "all",
        },
        "metrics": {
            "total_revenue": 1428500,
            "active_workspaces": 3842,
            "conversion_rate": 24.6,
            "retention_rate": 98.2,
            "data_points": [
                {"date": "2026-10-01", "revenue": 128000, "workspaces": 3400},
                {"date": "2026-11-01", "revenue": 139500, "workspaces": 3650},
                {"date": "2026-11-15", "revenue": 142850, "workspaces": 3842}
            ]
        }
    }
