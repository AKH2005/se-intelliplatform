"""API Dependencies and Inversion of Control."""

from collections.abc import AsyncGenerator
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.services.context_engine import ProjectContextEngine
from app.services.project_service import ProjectService
from app.services.requirement_service import RequirementService


async def get_project_service(
    session: AsyncSession = Depends(get_db),
) -> ProjectService:
    """Dependency injecting a project service with an active session."""
    return ProjectService(session=session)


async def get_requirement_service(
    session: AsyncSession = Depends(get_db),
) -> RequirementService:
    """Dependency injecting a requirement service with an active session."""
    return RequirementService(session=session)


async def get_context_engine(
    session: AsyncSession = Depends(get_db),
) -> ProjectContextEngine:
    """Dependency injecting a project context engine with an active session."""
    return ProjectContextEngine(session=session)
