"""Configuration and environment settings."""

import os
from pydantic import BaseModel


class Settings(BaseModel):
    app_name: str = "Executive Analytics Dashboard"
    environment: str = os.getenv("APP_ENV", "development")
    allowed_origins: list[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "*",
    ]


def get_settings() -> Settings:
    return Settings()
