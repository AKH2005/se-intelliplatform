from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    PROJECT_NAME: str = "UniSphere University Management System"
    VERSION: str = "1.0.0"
    API_V1_PREFIX: str = "/api"
    
    SECRET_KEY: str = "unisphere-super-secret-jwt-key-2026-university-mgmt"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 hours
    
    DATABASE_URL: str = "sqlite:///./unisphere.db"

    class Config:
        env_file = ".env"
        extra = "ignore"

settings = Settings()
