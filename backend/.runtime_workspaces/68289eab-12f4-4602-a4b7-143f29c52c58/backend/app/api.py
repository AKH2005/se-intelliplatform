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
            "role": "Novice Ninja",
        }
    }

@router.post("/api/auth/logout")
async def logout():
    return {"status": "success", "message": "Logged out successfully"}


@router.post("/api/auth/forgot-password")
async def forgot_password(email: str):
    return {
        "status": "success",
        "message": f"Password reset instructions dispatched to {email}",
        "reset_token": "pwd-reset-simulated-token-2026",
    }
