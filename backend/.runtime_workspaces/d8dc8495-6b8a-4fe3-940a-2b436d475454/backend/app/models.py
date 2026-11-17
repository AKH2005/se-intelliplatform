from pydantic import BaseModel
from typing import Optional

class User(BaseModel):
    id: str
    email: str
    name: str
    level: int = 1
    role: str = "Shadow Warrior"
    is_active: bool = True

class UserLoginRequest(BaseModel):
    email: str
    password: str

class UserRegisterRequest(BaseModel):
    email: str
    password: str
    name: Optional[str] = None

class AuthResponse(BaseModel):
    status: str
    token: str
    user: User


class AnalyticsFilterParams(BaseModel):
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    metric_type: Optional[str] = "all"

class AnalyticsMetricsResponse(BaseModel):
    status: str
    filter: dict
    metrics: dict
