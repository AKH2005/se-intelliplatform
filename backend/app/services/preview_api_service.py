"""Unified Preview Application API Service.

Provides persistent, project-isolated API data for Live Preview applications
(TaskFlow/Kanban, Snake Game, Executive Analytics, EventHub, E-Commerce).
Uses the configured PostgreSQL database (Neon in production) via SQLAlchemy AsyncSession.
"""

from datetime import datetime, timezone
import logging
import uuid
from typing import Any, Optional, Union
from sqlalchemy import inspect, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core import database as db_module
from app.models.base import Base
from app.models.preview import PreviewScore, PreviewTask

logger = logging.getLogger(__name__)


def parse_project_uuid(project_id: Optional[Union[str, uuid.UUID]]) -> Optional[uuid.UUID]:
    """Parse string or UUID into valid uuid.UUID or None."""
    if not project_id:
        return None
    if isinstance(project_id, uuid.UUID):
        return project_id
    try:
        clean = str(project_id).strip()
        if not clean:
            return None
        return uuid.UUID(clean)
    except Exception:
        try:
            return uuid.uuid5(uuid.NAMESPACE_DNS, clean)
        except Exception:
            return None


class PreviewApiService:
    """Service for handling preview application APIs across FastAPI and preview runtime."""

    @staticmethod
    async def ensure_schema() -> None:
        """Ensure all required preview tables and columns exist on the active database engine."""
        try:
            async with db_module.engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)

                def _migrate_columns(sync_conn):
                    inspector = inspect(sync_conn)
                    tables = inspector.get_table_names()
                    if "preview_tasks" in tables:
                        cols = [c["name"] for c in inspector.get_columns("preview_tasks")]
                        if "project_id" not in cols:
                            try:
                                sync_conn.execute(text("ALTER TABLE preview_tasks ADD COLUMN project_id VARCHAR(64)"))
                            except Exception:
                                pass
                        if "created_at" not in cols:
                            try:
                                sync_conn.execute(text("ALTER TABLE preview_tasks ADD COLUMN created_at TIMESTAMP"))
                            except Exception:
                                pass
                        if "updated_at" not in cols:
                            try:
                                sync_conn.execute(text("ALTER TABLE preview_tasks ADD COLUMN updated_at TIMESTAMP"))
                            except Exception:
                                pass

                    if "preview_scores" in tables:
                        cols = [c["name"] for c in inspector.get_columns("preview_scores")]
                        if "project_id" not in cols:
                            try:
                                sync_conn.execute(text("ALTER TABLE preview_scores ADD COLUMN project_id VARCHAR(64)"))
                            except Exception:
                                pass
                        if "created_at" not in cols:
                            try:
                                sync_conn.execute(text("ALTER TABLE preview_scores ADD COLUMN created_at TIMESTAMP"))
                            except Exception:
                                pass
                        if "updated_at" not in cols:
                            try:
                                sync_conn.execute(text("ALTER TABLE preview_scores ADD COLUMN updated_at TIMESTAMP"))
                            except Exception:
                                pass

                await conn.run_sync(_migrate_columns)
        except Exception as exc:
            logger.warning("Could not auto-ensure preview database schema: %s", exc)

    @classmethod
    async def get_tasks(
        cls,
        project_id: Optional[Union[str, uuid.UUID]] = None,
        session: Optional[AsyncSession] = None,
    ) -> list[dict[str, Any]]:
        """Retrieve tasks, isolating by project_id while seeding defaults if empty."""
        p_uuid = parse_project_uuid(project_id)

        if session is not None:
            return await cls._get_tasks_with_session(p_uuid, session)

        async with db_module.AsyncSessionLocal() as local_session:
            return await cls._get_tasks_with_session(p_uuid, local_session)

    @classmethod
    async def _get_tasks_with_session(
        cls,
        p_uuid: Optional[uuid.UUID],
        session: AsyncSession,
    ) -> list[dict[str, Any]]:
        if p_uuid is not None:
            stmt = select(PreviewTask).where(PreviewTask.project_id == p_uuid).order_by(PreviewTask.id.asc())
        else:
            stmt = select(PreviewTask).where(PreviewTask.project_id.is_(None)).order_by(PreviewTask.id.asc())

        res = await session.execute(stmt)
        tasks = list(res.scalars().all())

        if not tasks:
            # Seed starter tasks for this project
            if p_uuid is not None:
                initial = [
                    PreviewTask(
                        project_id=p_uuid,
                        title="Review Architecture Blueprint",
                        description="Inspect domain models, services, and endpoints.",
                        priority="HIGH",
                        status="COMPLETED",
                        due_date="2026-11-15",
                    ),
                    PreviewTask(
                        project_id=p_uuid,
                        title="Implement Core Feature Set",
                        description="Build and integrate primary application logic.",
                        priority="HIGH",
                        status="IN_PROGRESS",
                        due_date="2026-11-20",
                    ),
                    PreviewTask(
                        project_id=p_uuid,
                        title="Verify Live Preview Integration",
                        description="Ensure end-to-end API communication and real-time UI updates.",
                        priority="MEDIUM",
                        status="PENDING",
                        due_date="2026-11-25",
                    ),
                ]
            else:
                initial = [
                    PreviewTask(
                        project_id=None,
                        title="Setup Project Scaffolding",
                        description="Initialize database models and API routes.",
                        priority="HIGH",
                        status="COMPLETED",
                        due_date="2026-10-15",
                    ),
                    PreviewTask(
                        project_id=None,
                        title="Design Task Management UI",
                        description="Create responsive task dashboard and action cards.",
                        priority="MEDIUM",
                        status="PENDING",
                        due_date="2026-10-20",
                    ),
                ]

            session.add_all(initial)
            await session.commit()
            for t in initial:
                await session.refresh(t)
            return [t.to_dict() for t in initial]

        return [t.to_dict() for t in tasks]

    @classmethod
    async def create_task(
        cls,
        data: dict[str, Any],
        project_id: Optional[Union[str, uuid.UUID]] = None,
        session: Optional[AsyncSession] = None,
    ) -> dict[str, Any]:
        """Create a new task scoped to project_id."""
        p_uuid = parse_project_uuid(project_id or data.get("project_id"))

        if session is not None:
            return await cls._create_task_with_session(data, p_uuid, session)

        async with db_module.AsyncSessionLocal() as local_session:
            return await cls._create_task_with_session(data, p_uuid, local_session)

    @classmethod
    async def _create_task_with_session(
        cls,
        data: dict[str, Any],
        p_uuid: Optional[uuid.UUID],
        session: AsyncSession,
    ) -> dict[str, Any]:
        task = PreviewTask(
            project_id=p_uuid,
            title=(data.get("title") or "Untitled Task").strip(),
            description=(data.get("description") or "").strip(),
            priority=(data.get("priority") or "MEDIUM").strip(),
            status=(data.get("status") or "PENDING").strip(),
            due_date=(data.get("due_date") or "2026-12-31").strip(),
        )
        session.add(task)
        await session.commit()
        await session.refresh(task)
        return task.to_dict()

    @classmethod
    async def get_task(
        cls,
        task_id: int,
        project_id: Optional[Union[str, uuid.UUID]] = None,
        session: Optional[AsyncSession] = None,
    ) -> Optional[dict[str, Any]]:
        """Retrieve single task by ID with optional project scoping."""
        p_uuid = parse_project_uuid(project_id)

        if session is not None:
            return await cls._get_task_with_session(task_id, p_uuid, session)

        async with db_module.AsyncSessionLocal() as local_session:
            return await cls._get_task_with_session(task_id, p_uuid, local_session)

    @classmethod
    async def _get_task_with_session(
        cls,
        task_id: int,
        p_uuid: Optional[uuid.UUID],
        session: AsyncSession,
    ) -> Optional[dict[str, Any]]:
        stmt = select(PreviewTask).where(PreviewTask.id == task_id)
        if p_uuid is not None:
            stmt = stmt.where(PreviewTask.project_id == p_uuid)

        res = await session.execute(stmt)
        task = res.scalar_one_or_none()
        return task.to_dict() if task else None

    @classmethod
    async def update_task(
        cls,
        task_id: int,
        data: dict[str, Any],
        project_id: Optional[Union[str, uuid.UUID]] = None,
        session: Optional[AsyncSession] = None,
    ) -> Optional[dict[str, Any]]:
        """Update fields on an existing task."""
        p_uuid = parse_project_uuid(project_id)

        if session is not None:
            return await cls._update_task_with_session(task_id, data, p_uuid, session)

        async with db_module.AsyncSessionLocal() as local_session:
            return await cls._update_task_with_session(task_id, data, p_uuid, local_session)

    @classmethod
    async def _update_task_with_session(
        cls,
        task_id: int,
        data: dict[str, Any],
        p_uuid: Optional[uuid.UUID],
        session: AsyncSession,
    ) -> Optional[dict[str, Any]]:
        stmt = select(PreviewTask).where(PreviewTask.id == task_id)
        if p_uuid is not None:
            stmt = stmt.where(PreviewTask.project_id == p_uuid)

        res = await session.execute(stmt)
        task = res.scalar_one_or_none()
        if not task:
            return None

        if "title" in data:
            task.title = str(data["title"]).strip()
        if "description" in data:
            task.description = str(data["description"]).strip()
        if "priority" in data:
            task.priority = str(data["priority"]).strip()
        if "status" in data:
            task.status = str(data["status"]).strip()
        if "due_date" in data:
            task.due_date = str(data["due_date"]).strip()

        await session.commit()
        await session.refresh(task)
        return task.to_dict()

    @classmethod
    async def delete_task(
        cls,
        task_id: int,
        project_id: Optional[Union[str, uuid.UUID]] = None,
        session: Optional[AsyncSession] = None,
    ) -> bool:
        """Delete task by ID."""
        p_uuid = parse_project_uuid(project_id)

        if session is not None:
            return await cls._delete_task_with_session(task_id, p_uuid, session)

        async with db_module.AsyncSessionLocal() as local_session:
            return await cls._delete_task_with_session(task_id, p_uuid, local_session)

    @classmethod
    async def _delete_task_with_session(
        cls,
        task_id: int,
        p_uuid: Optional[uuid.UUID],
        session: AsyncSession,
    ) -> bool:
        stmt = select(PreviewTask).where(PreviewTask.id == task_id)
        if p_uuid is not None:
            stmt = stmt.where(PreviewTask.project_id == p_uuid)

        res = await session.execute(stmt)
        task = res.scalar_one_or_none()
        if not task:
            return False

        await session.delete(task)
        await session.commit()
        return True

    @classmethod
    async def get_scores(
        cls,
        project_id: Optional[Union[str, uuid.UUID]] = None,
        session: Optional[AsyncSession] = None,
    ) -> list[dict[str, Any]]:
        """Retrieve leaderboard scores for Snake Game."""
        p_uuid = parse_project_uuid(project_id)

        if session is not None:
            return await cls._get_scores_with_session(p_uuid, session)

        async with db_module.AsyncSessionLocal() as local_session:
            return await cls._get_scores_with_session(p_uuid, local_session)

    @classmethod
    async def _get_scores_with_session(
        cls,
        p_uuid: Optional[uuid.UUID],
        session: AsyncSession,
    ) -> list[dict[str, Any]]:
        stmt = select(PreviewScore)
        if p_uuid is not None:
            stmt = stmt.where((PreviewScore.project_id == p_uuid) | (PreviewScore.project_id.is_(None)))
        stmt = stmt.order_by(PreviewScore.score.desc()).limit(10)

        res = await session.execute(stmt)
        scores = list(res.scalars().all())

        if not scores:
            initial = [
                PreviewScore(project_id=p_uuid, player_name="NeonViper", score=320),
                PreviewScore(project_id=p_uuid, player_name="CyberSnake", score=240),
                PreviewScore(project_id=p_uuid, player_name="RetroGamer", score=180),
                PreviewScore(project_id=p_uuid, player_name="PixelMaster", score=120),
            ]
            session.add_all(initial)
            await session.commit()
            for s in initial:
                await session.refresh(s)
            return [s.to_dict() for s in initial]

        return [s.to_dict() for s in scores]

    @classmethod
    async def add_score(
        cls,
        score: int,
        player_name: str = "Player 1",
        project_id: Optional[Union[str, uuid.UUID]] = None,
        session: Optional[AsyncSession] = None,
    ) -> dict[str, Any]:
        """Save a new score for Snake Game."""
        p_uuid = parse_project_uuid(project_id)
        clean_player = str(player_name or "Player 1").strip()[:64]

        if session is not None:
            return await cls._add_score_with_session(score, clean_player, p_uuid, session)

        async with db_module.AsyncSessionLocal() as local_session:
            return await cls._add_score_with_session(score, clean_player, p_uuid, local_session)

    @classmethod
    async def _add_score_with_session(
        cls,
        score: int,
        player_name: str,
        p_uuid: Optional[uuid.UUID],
        session: AsyncSession,
    ) -> dict[str, Any]:
        score_rec = PreviewScore(
            project_id=p_uuid,
            player_name=player_name,
            score=int(score),
        )
        session.add(score_rec)
        await session.commit()
        await session.refresh(score_rec)
        res = score_rec.to_dict()
        res["status"] = "SAVED"
        return res

    @classmethod
    def get_analytics_metrics(cls, project_id: Optional[Union[str, uuid.UUID]] = None) -> dict[str, Any]:
        """Provide rich data for Executive Analytics Dashboard."""
        return {
            "summary": {
                "arr": "$2,480,000",
                "mrr": "$206,667",
                "arr_growth": "+19.4% YoY",
                "active_users": 15420,
                "user_growth": "+8.2% MoM",
                "net_retention": "112.5%",
                "gross_margin": "78.4%",
                "cac_payback_months": 7.2,
                "churn_rate": "1.4%",
            },
            "kpis": [
                {"name": "Annual Recurring Revenue", "value": "$2.48M", "change": "+19.4%", "category": "Financial"},
                {"name": "Monthly Recurring Revenue", "value": "$206.7K", "change": "+3.1%", "category": "Financial"},
                {"name": "Net Revenue Retention", "value": "112.5%", "change": "+2.4%", "category": "Product"},
                {"name": "Monthly Active Users", "value": "15,420", "change": "+8.2%", "category": "Product"},
                {"name": "Customer Acquisition Cost", "value": "$640", "change": "-4.5%", "category": "Sales"},
                {"name": "Average Revenue Per User", "value": "$42.50", "change": "+5.2%", "category": "Sales"},
            ],
            "monthly_revenue": [
                {"month": "May", "revenue": 178000},
                {"month": "Jun", "revenue": 184000},
                {"month": "Jul", "revenue": 191000},
                {"month": "Aug", "revenue": 197000},
                {"month": "Sep", "revenue": 202000},
                {"month": "Oct", "revenue": 206667},
            ],
            "cohort_retention": [
                {"cohort": "May 2026", "m0": 100, "m1": 89, "m2": 82, "m3": 78, "m4": 75, "m5": 74},
                {"cohort": "Jun 2026", "m0": 100, "m1": 91, "m2": 84, "m3": 81, "m4": 79},
                {"cohort": "Jul 2026", "m0": 100, "m1": 92, "m2": 86, "m3": 83},
                {"cohort": "Aug 2026", "m0": 100, "m1": 94, "m2": 88},
                {"cohort": "Sep 2026", "m0": 100, "m1": 95},
                {"cohort": "Oct 2026", "m0": 100},
            ],
        }
