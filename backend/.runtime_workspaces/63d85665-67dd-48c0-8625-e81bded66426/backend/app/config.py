"""Configuration and environment settings."""

import os
from pydantic import BaseModel


class Settings(BaseModel):
    app_name: str = "Carrom Master"
    environment: str = os.getenv("APP_ENV", "development")
    allowed_origins: list[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:8001",
        "http://127.0.0.1:8001",
        "*",
    ]


def get_settings() -> Settings:
    return Settings()
