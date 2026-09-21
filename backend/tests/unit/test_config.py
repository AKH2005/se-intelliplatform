"""Unit Tests for Configuration and Environment Parsing."""

import pytest
from pydantic import ValidationError

from app.core.config import Settings


def test_valid_default_configuration():
    """Verify default development configuration loads successfully."""
    s = Settings(
        ENVIRONMENT="development",
        DEBUG=True,
        POSTGRES_USER="postgres",
        POSTGRES_PASSWORD="postgres_password",
        POSTGRES_HOST="localhost",
        POSTGRES_PORT=5432,
        POSTGRES_DB="se_intelliplatform",
    )
    assert s.PROJECT_NAME == "SE IntelliPlatform"
    assert s.ENVIRONMENT == "development"
    assert s.DEBUG is True
    assert "postgresql+psycopg://" in s.DATABASE_URL
    assert "localhost:5432/se_intelliplatform" in s.DATABASE_URL
    assert s.REDIS_URL == "redis://localhost:6379/0"


def test_custom_database_url_normalization():
    """Verify that a standard postgresql:// URL gets converted to postgresql+psycopg://."""
    s = Settings(
        DATABASE_URL="postgresql://user:pass@dbhost:5433/customdb",
    )
    assert s.DATABASE_URL == "postgresql+psycopg://user:pass@dbhost:5433/customdb"


def test_log_level_normalization():
    """Verify lowercase log levels are normalized to uppercase."""
    s = Settings(LOG_LEVEL="debug")
    assert s.LOG_LEVEL == "DEBUG"


def test_insecure_production_password_fails_fast():
    """Verify that running in production with default password raises validation error."""
    with pytest.raises(ValidationError) as exc_info:
        Settings(
            ENVIRONMENT="production",
            POSTGRES_PASSWORD="postgres_password",
            DEBUG=False,
        )
    assert "Insecure default POSTGRES_PASSWORD is prohibited" in str(exc_info.value)


def test_production_with_debug_enabled_fails_fast():
    """Verify that running in production with DEBUG=True raises validation error."""
    with pytest.raises(ValidationError) as exc_info:
        Settings(
            ENVIRONMENT="production",
            POSTGRES_PASSWORD="a-very-secure-production-password-123",
            DEBUG=True,
        )
    assert "DEBUG mode must be set to false" in str(exc_info.value)
