"""API Dependencies and Inversion of Control."""

from collections.abc import AsyncGenerator
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.services.project_service import ProjectService


async def get_project_service(
    session: AsyncSession = Depends(get_db),
) -> ProjectService:
    """Dependency injecting a project service with an active session."""
    return ProjectService(session=session)
