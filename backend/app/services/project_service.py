"""Project Domain Service Implementing Project Lifecycle Operations."""

import logging
import uuid
from typing import Any, Sequence
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

    async def create_project(self, project_in: ProjectCreate, owner_id: uuid.UUID | None = None) -> Project:
        """Create a new project ensuring slug uniqueness and assigning owner if present."""
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
            owner_id=owner_id,
        )

        self.session.add(project)
        try:
            await self.session.commit()
            await self.session.refresh(project)
            logger.info(f"Created project '{project.name}' [id={project.id}, slug={project.slug}, owner={owner_id}]")
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
        owner_id: uuid.UUID | None = None,
    ) -> tuple[Sequence[Project], int]:
        """Return a paginated list of projects along with the total count."""
        query = select(Project)
        count_query = select(func.count()).select_from(Project)

        if owner_id is not None:
            query = query.where((Project.owner_id == owner_id) | (Project.owner_id.is_(None)))
            count_query = count_query.where((Project.owner_id == owner_id) | (Project.owner_id.is_(None)))

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

    async def restore_project(self, project_id: uuid.UUID) -> Project:
        """Restore an archived project back to IN_PROGRESS status."""
        project = await self.get_by_id(project_id)
        project.status = ProjectStatus.IN_PROGRESS
        await self.session.commit()
        await self.session.refresh(project)
        logger.info(f"Restored project [id={project.id}] from archive to IN_PROGRESS")
        return project

    async def duplicate_project(self, project_id: uuid.UUID, owner_id: uuid.UUID | None = None) -> Project:
        """Duplicate an existing project including its configuration settings and canonical requirements."""
        from app.models.requirement import Requirement

        original = await self.get_by_id(project_id)

        # Generate a unique slug for the duplicate
        base_slug = f"{original.slug}-copy"
        candidate_slug = base_slug
        counter = 1
        while await self.get_by_slug(candidate_slug):
            candidate_slug = f"{base_slug}-{counter}"
            counter += 1

        new_project = Project(
            name=f"{original.name} (Copy)",
            slug=candidate_slug,
            description=original.description,
            status=ProjectStatus.DRAFT,
            settings=dict(original.settings or {}),
            owner_id=owner_id or original.owner_id,
        )
        self.session.add(new_project)
        await self.session.flush()

        # Clone canonical requirements
        stmt_reqs = select(Requirement).where(Requirement.project_id == project_id)
        req_res = await self.session.execute(stmt_reqs)
        for req in req_res.scalars().all():
            cloned_req = Requirement(
                project_id=new_project.id,
                title=req.title,
                description=req.description,
                type=req.type,
                priority=req.priority,
                status=req.status,
            )
            self.session.add(cloned_req)

        await self.session.commit()
        await self.session.refresh(new_project)
        logger.info(f"Duplicated project {original.id} -> {new_project.id} with slug '{new_project.slug}'")
        return new_project

    async def hard_delete_project(self, project_id: uuid.UUID) -> None:
        """Physically delete project from database (reserved for test teardown / admin purge)."""
        project = await self.get_by_id(project_id)
        await self.session.delete(project)
        await self.session.commit()
        logger.info(f"Permanently deleted project [id={project_id}]")

    async def get_activity_history(self, project_id: uuid.UUID) -> list[dict[str, Any]]:
        """Retrieve authoritative activity history timeline for a project."""
        from app.models.requirement import Requirement
        from app.models.development_version import DevelopmentVersion
        from app.models.workflow_execution import WorkflowExecution

        project = await self.get_by_id(project_id)
        activities: list[dict[str, Any]] = []

        # 1. Project creation event
        activities.append({
            "id": f"proj-create-{project.id}",
            "event_type": "PROJECT_CREATED",
            "title": f"Project '{project.name}' created",
            "description": project.description or "Initial project registration.",
            "timestamp": project.created_at.isoformat() if project.created_at else None,
            "status": project.status.value,
            "metadata": {"slug": project.slug},
        })

        # 2. Requirements added
        stmt_reqs = select(Requirement).where(Requirement.project_id == project_id).order_by(Requirement.created_at.desc())
        req_res = await self.session.execute(stmt_reqs)
        for req in req_res.scalars().all():
            activities.append({
                "id": f"req-{req.id}",
                "event_type": "REQUIREMENT_ADDED",
                "title": f"Requirement: {req.title}",
                "description": req.description[:120] + "..." if len(req.description) > 120 else req.description,
                "timestamp": req.created_at.isoformat() if req.created_at else None,
                "status": req.status.value,
                "metadata": {"type": req.type.value, "priority": req.priority.value},
            })

        # 3. Workflow executions / AI generation runs
        stmt_wf = select(WorkflowExecution).where(WorkflowExecution.project_id == project_id).order_by(WorkflowExecution.started_at.desc())
        wf_res = await self.session.execute(stmt_wf)
        for wf in wf_res.scalars().all():
            activities.append({
                "id": f"wf-{wf.workflow_execution_id}",
                "event_type": "WORKFLOW_EXECUTION",
                "title": f"Workflow '{wf.workflow_id}' ({wf.status.value})",
                "description": f"Executed {wf.completed_steps}/{wf.step_count} steps.",
                "timestamp": wf.started_at.isoformat() if wf.started_at else None,
                "status": wf.status.value,
                "metadata": {
                    "workflow_id": wf.workflow_id,
                    "errors": wf.errors or [],
                },
            })

        # 4. Development Versions
        stmt_ver = select(DevelopmentVersion).where(DevelopmentVersion.project_id == project_id).order_by(DevelopmentVersion.created_at.desc())
        ver_res = await self.session.execute(stmt_ver)
        for ver in ver_res.scalars().all():
            activities.append({
                "id": f"ver-{ver.id}",
                "event_type": "VERSION_GENERATED",
                "title": f"Version {ver.version_number} Generated ({ver.status.value})",
                "description": f"Generated {ver.file_count} files ({ver.total_size_bytes} bytes). Reason: {ver.source_reason}.",
                "timestamp": ver.created_at.isoformat() if ver.created_at else None,
                "status": ver.status.value,
                "metadata": {
                    "version_number": ver.version_number,
                    "file_count": ver.file_count,
                    "content_hash": ver.content_hash,
                },
            })

        # Sort all activities by timestamp descending
        activities.sort(key=lambda a: a.get("timestamp") or "", reverse=True)
        return activities
