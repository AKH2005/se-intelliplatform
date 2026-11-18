from typing import Any, Literal
from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(".env", "backend/.env"),
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

    # Authentication & JWT Security Settings
    SECRET_KEY: str = Field(
        default="se-intelliplatform-super-secret-jwt-key-for-capstone-development-2026",
        description="Cryptographic secret key for signing JWT tokens",
    )
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(
        default=60 * 24,
        description="JWT token validity duration in minutes (default: 24h)",
    )

    # CORS Configuration
    CORS_ORIGINS: list[str] = Field(
        default=[
            "http://localhost:3000",
            "http://localhost:5173",
            "http://localhost:5174",
            "http://127.0.0.1:5173",
            "http://127.0.0.1:5174",
            "http://localhost:4173",
            "http://127.0.0.1:4173",
            "http://localhost:8000",
            "http://127.0.0.1:8000",
            "http://localhost:8001",
            "http://127.0.0.1:8001",
            "https://se-intelliplatform.vercel.app",
            "https://se-intelliplatform-frontend.vercel.app",
            "https://se-intelliplatform-backend.onrender.com",
        ],
        description="Allowed CORS origins for frontend web application",
    )
    CORS_ORIGIN_REGEX: str | None = Field(
        default=r"^https:\/\/.*(\.vercel\.app|\.onrender\.com)$",
        description="Allowed CORS origin regex for Vercel preview and production deployments",
    )

    # Application Live Preview Runtime Settings
    PREVIEW_RUNTIME_URL: str = Field(
        default="http://127.0.0.1:8001/",
        description="URL for Live Application Preview runtime",
    )

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

    # LLM Provider Settings (Vendor-neutral AI infrastructure)
    LLM_PROVIDER: str = Field(default="groq", description="Active LLM provider adapter")
    LLM_MODEL: str = Field(default="openai/gpt-oss-20b", description="Default model name")
    LLM_MODEL_GROQ: str = Field(default="openai/gpt-oss-20b", description="Default Groq model")
    LLM_MODEL_GEMINI: str = Field(default="gemini-2.5-flash", description="Default Gemini model")
    LLM_MODEL_FAST: str = Field(default="openai/gpt-oss-20b", description="Fast low-latency model")
    LLM_TIMEOUT: float = Field(default=30.0, description="Provider timeout in seconds")
    LLM_MAX_RETRIES: int = Field(default=3, description="Maximum transient retries")
    LLM_API_KEY: str | None = Field(default=None, description="Optional provider API key")
    GROQ_API_KEY: str | None = Field(default=None, description="Groq API key")
    GEMINI_API_KEY: str | None = Field(default=None, description="Google Gemini API key")

    # Logging Settings
    LOG_LEVEL: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = Field(
        default="INFO", description="Log verbosity level"
    )
    LOG_FORMAT: Literal["json", "text"] = Field(
        default="json", description="Log output format"
    )

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors_origins(cls, v: Any) -> list[str]:
        if isinstance(v, str):
            import json
            try:
                parsed = json.loads(v)
                if isinstance(parsed, list):
                    return parsed
            except Exception:
                pass
            return [origin.strip() for origin in v.split(",") if origin.strip()]
        return v

    @field_validator("LOG_LEVEL", mode="before")
    @classmethod
    def normalize_log_level(cls, v: str) -> str:
        if isinstance(v, str):
            return v.upper()
        return v

    @model_validator(mode="after")
    def assemble_urls_and_validate(self) -> "Settings":
        import sys, os
        # Build DATABASE_URL if omitted
        if not self.DATABASE_URL:
            self.DATABASE_URL = (
                f"postgresql+psycopg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@"
                f"{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
            )
        elif self.DATABASE_URL.startswith("postgres://"):
            # Ensure async psycopg driver is explicitly targeted for Neon/Postgres URLs
            self.DATABASE_URL = self.DATABASE_URL.replace("postgres://", "postgresql+psycopg://", 1)
        elif self.DATABASE_URL.startswith("postgresql://"):
            # Ensure async psycopg driver is explicitly targeted
            self.DATABASE_URL = self.DATABASE_URL.replace("postgresql://", "postgresql+psycopg://", 1)
        elif "sqlite" in self.DATABASE_URL and ("pytest" in sys.modules or os.environ.get("ENVIRONMENT") == "testing"):
            if self.POSTGRES_HOST == "localhost" and self.POSTGRES_PORT == 5432:
                self.DATABASE_URL = (
                    f"postgresql+psycopg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@"
                    f"{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
                )

        # Build REDIS_URL if omitted
        if not self.REDIS_URL:
            self.REDIS_URL = f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/0"

        # Force mock provider in testing environment to preserve test determinism
        if self.ENVIRONMENT == "testing":
            self.LLM_PROVIDER = "mock"

        # Fail-fast security validation: Prevent default insecure credentials in production
        if self.ENVIRONMENT in ("production", "staging"):
            if not self.DATABASE_URL or "sqlite" in self.DATABASE_URL.lower():
                raise ValueError(
                    f"A valid PostgreSQL DATABASE_URL pointing to the production database (e.g. Neon PostgreSQL) "
                    f"is required in {self.ENVIRONMENT} environment. SQLite databases are strictly prohibited in production."
                )
            is_using_default_pass = self.POSTGRES_PASSWORD == "postgres_password" and (
                not self.DATABASE_URL or "postgres_password" in self.DATABASE_URL
            )
            if is_using_default_pass:
                raise ValueError(
                    f"Insecure default POSTGRES_PASSWORD is prohibited in {self.ENVIRONMENT} environment."
                )
            if self.DEBUG:
                raise ValueError(
                    f"DEBUG mode must be set to false in {self.ENVIRONMENT} environment."
                )
            known_insecure_secrets = {
                "se-intelliplatform-super-secret-jwt-key-for-capstone-development-2026",
                "secret",
                "changeme",
                "password",
                "your-secret-key",
                "secret-key",
                "supersecret",
            }
            if (
                not self.SECRET_KEY
                or self.SECRET_KEY.strip() in known_insecure_secrets
                or len(self.SECRET_KEY.strip()) < 32
            ):
                raise ValueError(
                    f"Insecure, default, or weak SECRET_KEY is strictly prohibited in {self.ENVIRONMENT} environment. "
                    f"A high-entropy SECRET_KEY of at least 32 characters must be provided via the SECRET_KEY environment variable. "
                    f"Generate a secure key with `openssl rand -hex 32` or `python -c \"import secrets; print(secrets.token_hex(32))\"`."
                )

        return self


# Global singleton settings instance
settings = Settings()
