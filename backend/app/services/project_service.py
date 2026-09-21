"""Project Domain Service Implementing Project Lifecycle Operations."""

import logging
import uuid
from typing import Sequence
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictError, NotFoundError
from app.models.project import Project, ProjectStatus
from app.schemas.project import ProjectCreate, ProjectUpdate

logger = logging.getLogger(__name__)


class ProjectService:
    """Encapsulates business and persistence logic for Project entities."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create_project(self, project_in: ProjectCreate) -> Project:
        """Create a new project ensuring slug uniqueness."""
        # Check existing slug
        existing = await self.get_by_slug(project_in.slug)
        if existing:
            raise ConflictError(
                message=f"Project with slug '{project_in.slug}' already exists.",
                field="slug",
                value=project_in.slug,
            )

        project = Project(
            name=project_in.name,
            slug=project_in.slug,
            description=project_in.description,
            status=project_in.status,
            settings=project_in.settings,
        )

        self.session.add(project)
        try:
            await self.session.commit()
            await self.session.refresh(project)
            logger.info(f"Created project '{project.name}' [id={project.id}, slug={project.slug}]")
            return project
        except IntegrityError as exc:
            await self.session.rollback()
            raise ConflictError(
                message=f"Project with slug '{project_in.slug}' already exists.",
                field="slug",
                value=project_in.slug,
            ) from exc

    async def get_by_id(self, project_id: uuid.UUID) -> Project:
        """Retrieve a single project by UUID primary key or raise NotFoundError."""
        statement = select(Project).where(Project.id == project_id)
        result = await self.session.execute(statement)
        project = result.scalar_one_or_none()
        if not project:
            raise NotFoundError(resource_type="Project", identifier=project_id)
        return project

    async def get_by_slug(self, slug: str) -> Project | None:
        """Retrieve a project by unique slug or return None."""
        statement = select(Project).where(Project.slug == slug)
        result = await self.session.execute(statement)
        return result.scalar_one_or_none()

    async def list_projects(
        self,
        skip: int = 0,
        limit: int = 50,
        status: ProjectStatus | None = None,
    ) -> tuple[Sequence[Project], int]:
        """Return a paginated list of projects along with the total count."""
        query = select(Project)
        count_query = select(func.count()).select_from(Project)

        if status is not None:
            query = query.where(Project.status == status)
            count_query = count_query.where(Project.status == status)

        query = query.order_by(Project.created_at.desc()).offset(skip).limit(limit)

        total_count = (await self.session.execute(count_query)).scalar_one()
        results = (await self.session.execute(query)).scalars().all()

        return results, total_count

    async def update_project(self, project_id: uuid.UUID, update_in: ProjectUpdate) -> Project:
        """Apply partial updates to an existing project."""
        project = await self.get_by_id(project_id)

        update_data = update_in.model_dump(exclude_unset=True)

        # If slug is being updated, verify it is not already taken by another project
        if "slug" in update_data and update_data["slug"] != project.slug:
            existing_with_slug = await self.get_by_slug(update_data["slug"])
            if existing_with_slug and existing_with_slug.id != project.id:
                raise ConflictError(
                    message=f"Project with slug '{update_data['slug']}' already exists.",
                    field="slug",
                    value=update_data["slug"],
                )

        for field, value in update_data.items():
            setattr(project, field, value)

        try:
            await self.session.commit()
            await self.session.refresh(project)
            logger.info(f"Updated project [id={project.id}, slug={project.slug}]")
            return project
        except IntegrityError as exc:
            await self.session.rollback()
            raise ConflictError(
                message="Integrity error during project update.",
            ) from exc

    async def archive_project(self, project_id: uuid.UUID) -> Project:
        """Lifecycle-safe soft deletion by setting status to ARCHIVED."""
        project = await self.get_by_id(project_id)
        project.status = ProjectStatus.ARCHIVED
        await self.session.commit()
        await self.session.refresh(project)
        logger.info(f"Archived project [id={project.id}]")
        return project

    async def hard_delete_project(self, project_id: uuid.UUID) -> None:
        """Physically delete project from database (reserved for test teardown / admin purge)."""
        project = await self.get_by_id(project_id)
        await self.session.delete(project)
        await self.session.commit()
        logger.info(f"Permanently deleted project [id={project_id}]")
