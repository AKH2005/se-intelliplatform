from typing import Literal
from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Application
    PROJECT_NAME: str = Field(default="SE IntelliPlatform", description="Application name")
    VERSION: str = Field(default="0.1.0", description="Application semantic version")
    ENVIRONMENT: Literal["development", "testing", "staging", "production"] = Field(
        default="development", description="Runtime environment"
    )
    DEBUG: bool = Field(default=False, description="Debug mode flag")
    API_V1_STR: str = Field(default="/api/v1", description="Version 1 API prefix")

    # Database Settings
    POSTGRES_HOST: str = Field(default="localhost", description="PostgreSQL host")
    POSTGRES_PORT: int = Field(default=5432, description="PostgreSQL port")
    POSTGRES_USER: str = Field(default="postgres", description="PostgreSQL username")
    POSTGRES_PASSWORD: str = Field(default="postgres_password", description="PostgreSQL password")
    POSTGRES_DB: str = Field(default="se_intelliplatform", description="PostgreSQL database name")
    DATABASE_URL: str | None = Field(
        default=None,
        description="Async PostgreSQL connection string (postgresql+psycopg://)",
    )

    # Redis Settings (Infrastructure preparation for Phase 2+)
    REDIS_HOST: str = Field(default="localhost", description="Redis host")
    REDIS_PORT: int = Field(default=6379, description="Redis port")
    REDIS_URL: str | None = Field(
        default=None,
        description="Redis connection URL",
    )

    # Logging Settings
    LOG_LEVEL: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = Field(
        default="INFO", description="Log verbosity level"
    )
    LOG_FORMAT: Literal["json", "text"] = Field(
        default="json", description="Log output format"
    )

    @field_validator("LOG_LEVEL", mode="before")
    @classmethod
    def normalize_log_level(cls, v: str) -> str:
        if isinstance(v, str):
            return v.upper()
        return v

    @model_validator(mode="after")
    def assemble_urls_and_validate(self) -> "Settings":
        # Build DATABASE_URL if omitted
        if not self.DATABASE_URL:
            self.DATABASE_URL = (
                f"postgresql+psycopg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@"
                f"{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
            )
        elif self.DATABASE_URL.startswith("postgresql://"):
            # Ensure async psycopg driver is explicitly targeted
            self.DATABASE_URL = self.DATABASE_URL.replace("postgresql://", "postgresql+psycopg://", 1)

        # Build REDIS_URL if omitted
        if not self.REDIS_URL:
            self.REDIS_URL = f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/0"

        # Fail-fast security validation: Prevent default insecure credentials in production
        if self.ENVIRONMENT in ("production", "staging"):
            if self.POSTGRES_PASSWORD == "postgres_password":
                raise ValueError(
                    f"Insecure default POSTGRES_PASSWORD is prohibited in {self.ENVIRONMENT} environment."
                )
            if self.DEBUG:
                raise ValueError(
                    f"DEBUG mode must be set to false in {self.ENVIRONMENT} environment."
                )

        return self


# Global singleton settings instance
settings = Settings()
