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
    """Verify that postgresql:// and postgres:// URLs get converted to postgresql+psycopg://, and existing postgresql+psycopg:// URLs are preserved."""
    # Standard postgresql://
    s1 = Settings(
        DATABASE_URL="postgresql://user:pass@dbhost:5433/customdb",
    )
    assert s1.DATABASE_URL == "postgresql+psycopg://user:pass@dbhost:5433/customdb"

    # Neon / cloud provider postgres:// scheme
    s2 = Settings(
        DATABASE_URL="postgres://neon_user:neon_pass@ep-cool-1234.us-east-2.aws.neon.tech/neondb?sslmode=require",
    )
    assert s2.DATABASE_URL == "postgresql+psycopg://neon_user:neon_pass@ep-cool-1234.us-east-2.aws.neon.tech/neondb?sslmode=require"

    # Already configured postgresql+psycopg:// scheme preserved
    s3 = Settings(
        DATABASE_URL="postgresql+psycopg://user:pass@dbhost:5432/existingdb",
    )
    assert s3.DATABASE_URL == "postgresql+psycopg://user:pass@dbhost:5432/existingdb"


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


def test_production_with_default_or_weak_secret_key_fails_fast():
    """Verify that production rejects default, weak, or missing SECRET_KEY."""
    # 1. Default dev secret in production
    with pytest.raises(ValidationError) as exc_info1:
        Settings(
            ENVIRONMENT="production",
            POSTGRES_PASSWORD="a-very-secure-production-password-123",
            DATABASE_URL="postgresql+psycopg://user:pass@proddb:5432/proddb",
            DEBUG=False,
            # using default SECRET_KEY
        )
    assert "Insecure, default, or weak SECRET_KEY is strictly prohibited" in str(exc_info1.value)

    # 2. Short secret in production
    with pytest.raises(ValidationError) as exc_info2:
        Settings(
            ENVIRONMENT="production",
            POSTGRES_PASSWORD="a-very-secure-production-password-123",
            DATABASE_URL="postgresql+psycopg://user:pass@proddb:5432/proddb",
            DEBUG=False,
            SECRET_KEY="short-secret-key-too-short",
        )
    assert "Insecure, default, or weak SECRET_KEY is strictly prohibited" in str(exc_info2.value)


def test_valid_production_configuration_passes():
    """Verify production environment succeeds with compliant credentials and 32+ char secret."""
    valid_key = "a" * 32
    s = Settings(
        ENVIRONMENT="production",
        POSTGRES_PASSWORD="a-very-secure-production-password-123",
        DATABASE_URL="postgresql+psycopg://user:pass@proddb:5432/proddb",
        DEBUG=False,
        SECRET_KEY=valid_key,
    )
    assert s.ENVIRONMENT == "production"
    assert s.DEBUG is False
    assert s.SECRET_KEY == valid_key


def test_development_allows_default_secret():
    """Verify local development environment allows default development secret."""
    s = Settings(
        ENVIRONMENT="development",
        DEBUG=True,
    )
    assert s.ENVIRONMENT == "development"
    assert s.SECRET_KEY == "se-intelliplatform-super-secret-jwt-key-for-capstone-development-2026"
