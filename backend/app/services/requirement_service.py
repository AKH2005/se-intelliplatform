"""Requirement Domain Service Encapsulating Business and Persistence Logic."""

import logging
import uuid
from typing import Sequence
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.models.project import Project
from app.models.requirement import (
    Requirement,
    RequirementPriority,
    RequirementStatus,
    RequirementType,
)
from app.schemas.requirement import RequirementCreate, RequirementUpdate

logger = logging.getLogger(__name__)


class RequirementService:
    """Encapsulates business operations and query logic for Requirement entities."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def _verify_project_exists(self, project_id: uuid.UUID) -> Project:
        """Verify the parent project exists or raise NotFoundError."""
        statement = select(Project).where(Project.id == project_id)
        result = await self.session.execute(statement)
        project = result.scalar_one_or_none()
        if not project:
            raise NotFoundError(resource_type="Project", identifier=project_id)
        return project

    async def create_requirement(
        self,
        project_id: uuid.UUID,
        req_in: RequirementCreate,
    ) -> Requirement:
        """Create a new requirement associated with the target project."""
        await self._verify_project_exists(project_id)

        requirement = Requirement(
            project_id=project_id,
            title=req_in.title,
            description=req_in.description,
            type=req_in.type,
            priority=req_in.priority,
            status=req_in.status,
            is_archived=False,
        )

        self.session.add(requirement)
        await self.session.commit()
        await self.session.refresh(requirement)
        logger.info(
            f"Created requirement '{requirement.title[:30]}' [id={requirement.id}] "
            f"for project [id={project_id}]"
        )
        return requirement

    async def get_by_id(
        self,
        project_id: uuid.UUID,
        requirement_id: uuid.UUID,
    ) -> Requirement:
        """Retrieve a single requirement by ID scoped to its project."""
        statement = select(Requirement).where(
            Requirement.id == requirement_id,
            Requirement.project_id == project_id,
        )
        result = await self.session.execute(statement)
        requirement = result.scalar_one_or_none()
        if not requirement:
            raise NotFoundError(resource_type="Requirement", identifier=requirement_id)
        return requirement

    async def list_requirements(
        self,
        project_id: uuid.UUID,
        skip: int = 0,
        limit: int = 50,
        type: RequirementType | None = None,
        priority: RequirementPriority | None = None,
        status: RequirementStatus | None = None,
        include_archived: bool = False,
    ) -> tuple[Sequence[Requirement], int]:
        """Return paginated requirements for a project with optional domain filters."""
        await self._verify_project_exists(project_id)

        query = select(Requirement).where(Requirement.project_id == project_id)
        count_query = (
            select(func.count())
            .select_from(Requirement)
            .where(Requirement.project_id == project_id)
        )

        if not include_archived:
            query = query.where(Requirement.is_archived.is_(False))
            count_query = count_query.where(Requirement.is_archived.is_(False))

        if type is not None:
            query = query.where(Requirement.type == type)
            count_query = count_query.where(Requirement.type == type)

        if priority is not None:
            query = query.where(Requirement.priority == priority)
            count_query = count_query.where(Requirement.priority == priority)

        if status is not None:
            query = query.where(Requirement.status == status)
            count_query = count_query.where(Requirement.status == status)

        query = query.order_by(Requirement.created_at.desc()).offset(skip).limit(limit)

        total_count = (await self.session.execute(count_query)).scalar_one()
        results = (await self.session.execute(query)).scalars().all()

        return results, total_count

    async def update_requirement(
        self,
        project_id: uuid.UUID,
        requirement_id: uuid.UUID,
        update_in: RequirementUpdate,
    ) -> Requirement:
        """Apply partial updates to an existing requirement."""
        requirement = await self.get_by_id(project_id, requirement_id)

        update_data = update_in.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(requirement, field, value)

        await self.session.commit()
        await self.session.refresh(requirement)
        logger.info(
            f"Updated requirement [id={requirement.id}] on project [id={project_id}]"
        )
        return requirement

    async def archive_requirement(
        self,
        project_id: uuid.UUID,
        requirement_id: uuid.UUID,
    ) -> Requirement:
        """Soft-archive a requirement preserving full history for SDLC intelligence.
        
        Per Phase 2 architecture, requirements are never physically deleted via
        the API, as requirement history provides critical engineering context.
        """
        requirement = await self.get_by_id(project_id, requirement_id)
        requirement.is_archived = True
        await self.session.commit()
        await self.session.refresh(requirement)
        logger.info(
            f"Archived requirement [id={requirement.id}] on project [id={project_id}]"
        )
        return requirement

    async def hard_delete_requirement(
        self,
        project_id: uuid.UUID,
        requirement_id: uuid.UUID,
    ) -> None:
        """Physically delete requirement (reserved strictly for test fixture teardown)."""
        requirement = await self.get_by_id(project_id, requirement_id)
        await self.session.delete(requirement)
        await self.session.commit()
        logger.info(f"Physically deleted requirement [id={requirement_id}]")
