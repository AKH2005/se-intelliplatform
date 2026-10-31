"""Pytest Configuration, Fixtures, and Test Environment Setup."""

import os
import sys

# Configure Windows event loop policy for async compatibility
if sys.platform == "win32":
    import asyncio
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

from collections.abc import AsyncGenerator
import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.pool import StaticPool
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

# Set testing environment before importing app
TEST_DB_URL = os.environ.get("TEST_DATABASE_URL", "sqlite+aiosqlite:///:memory:")
os.environ["ENVIRONMENT"] = "testing"
os.environ["DEBUG"] = "true"
os.environ["LOG_LEVEL"] = "WARNING"
os.environ["DATABASE_URL"] = TEST_DB_URL

from app.core.config import settings
from app.core import database as db_module
from app.core.database import get_db
from app.main import app
from app.models.base import Base

test_engine = create_async_engine(
    TEST_DB_URL,
    echo=False,
    future=True,
    connect_args={"check_same_thread": False} if "sqlite" in TEST_DB_URL else {},
    poolclass=StaticPool if "sqlite" in TEST_DB_URL else None,
)

TestingSessionLocal = async_sessionmaker(
    bind=test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)

# Bind global core database engine & sessionmaker to test engine during test runs
db_module.engine = test_engine
db_module.AsyncSessionLocal = TestingSessionLocal


@pytest.fixture(autouse=True)
async def setup_database() -> AsyncGenerator[None, None]:
    """Create all database tables before each test and drop them after."""
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """Provide a transactional async session for database testing."""
    async with TestingSessionLocal() as session:
        yield session


@pytest.fixture
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """Provide an asynchronous HTTP test client with overridden database dependency."""
    async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as ac:
        yield ac

    app.dependency_overrides.clear()
