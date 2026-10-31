"""Unified Preview Application API Service.

Provides persistent, project-isolated API data for Live Preview applications
(TaskFlow/Kanban, Snake Game, Executive Analytics, EventHub, E-Commerce).
Ensures database schema migrations (project_id scoping, scores table) and WAL-safe operations.
"""

import json
import logging
import os
import sqlite3
from pathlib import Path
from typing import Any, Optional

logger = logging.getLogger(__name__)

# Resolve absolute path to se_intelliplatform.db
DB_FILE = Path(__file__).resolve().parent.parent.parent / "se_intelliplatform.db"


def get_sqlite_conn() -> sqlite3.Connection:
    """Create a SQLite connection with timeout and WAL journal mode."""
    conn = sqlite3.connect(str(DB_FILE), timeout=30.0)
    conn.row_factory = sqlite3.Row
    try:
        conn.execute("PRAGMA busy_timeout = 30000")
        conn.execute("PRAGMA journal_mode = WAL")
    except Exception:
        pass
    return conn


class PreviewApiService:
    """Service for handling preview application APIs across FastAPI and preview runtime."""

    @staticmethod
    def ensure_schema() -> None:
        """Ensure all required preview tables and columns exist with backward compatibility."""
        try:
            conn = get_sqlite_conn()
            cur = conn.cursor()

            # 1. Ensure preview_tasks table exists
            cur.execute("""
                CREATE TABLE IF NOT EXISTS preview_tasks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    description TEXT DEFAULT '',
                    priority TEXT DEFAULT 'MEDIUM',
                    status TEXT DEFAULT 'PENDING',
                    due_date TEXT DEFAULT '2026-12-31',
                    project_id TEXT DEFAULT ''
                )
            """)

            # Verify if project_id column exists on preview_tasks
            cur.execute("PRAGMA table_info(preview_tasks)")
            columns = [c["name"] for c in cur.fetchall()]
            if "project_id" not in columns:
                try:
                    cur.execute("ALTER TABLE preview_tasks ADD COLUMN project_id TEXT DEFAULT ''")
                    logger.info("Migrated preview_tasks: added project_id column.")
                except Exception as exc:
                    logger.debug("ALTER TABLE preview_tasks project_id already applied or skipped: %s", exc)

            # 2. Ensure preview_scores table exists for Arcade / Snake Game
            cur.execute("""
                CREATE TABLE IF NOT EXISTS preview_scores (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    project_id TEXT DEFAULT '',
                    player_name TEXT DEFAULT 'Player 1',
                    score INTEGER NOT NULL,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Seed initial scores if empty
            cur.execute("SELECT COUNT(*) as count FROM preview_scores")
            count = cur.fetchone()["count"]
            if count == 0:
                cur.executemany(
                    "INSERT INTO preview_scores (project_id, player_name, score) VALUES (?, ?, ?)",
                    [
                        ("", "NeonViper", 320),
                        ("", "CyberSnake", 240),
                        ("", "RetroGamer", 180),
                        ("", "PixelMaster", 120),
                    ]
                )

            conn.commit()
            conn.close()
        except Exception as exc:
            logger.warning("Could not auto-ensure preview database schema: %s", exc)

    @classmethod
    def get_tasks(cls, project_id: Optional[str] = None) -> list[dict[str, Any]]:
        """Retrieve tasks, isolating by project_id while seeding defaults if empty."""
        cls.ensure_schema()
        clean_pid = str(project_id or "").strip()
        conn = get_sqlite_conn()
        cur = conn.cursor()

        if clean_pid:
            cur.execute(
                "SELECT id, title, description, priority, status, due_date, project_id FROM preview_tasks WHERE project_id = ? ORDER BY id ASC",
                (clean_pid,)
            )
            rows = cur.fetchall()
            if not rows:
                # Seed initial starter tasks for this project
                initial = [
                    (clean_pid, "Review Architecture Blueprint", "Inspect domain models, services, and endpoints.", "HIGH", "COMPLETED", "2026-11-15"),
                    (clean_pid, "Implement Core Feature Set", "Build and integrate primary application logic.", "HIGH", "IN_PROGRESS", "2026-11-20"),
                    (clean_pid, "Verify Live Preview Integration", "Ensure end-to-end API communication and real-time UI updates.", "MEDIUM", "PENDING", "2026-11-25"),
                ]
                cur.executemany(
                    "INSERT INTO preview_tasks (project_id, title, description, priority, status, due_date) VALUES (?, ?, ?, ?, ?, ?)",
                    initial
                )
                conn.commit()
                cur.execute(
                    "SELECT id, title, description, priority, status, due_date, project_id FROM preview_tasks WHERE project_id = ? ORDER BY id ASC",
                    (clean_pid,)
                )
                rows = cur.fetchall()
        else:
            cur.execute("SELECT id, title, description, priority, status, due_date, project_id FROM preview_tasks ORDER BY id ASC")
            rows = cur.fetchall()
            if not rows:
                initial = [
                    ("", "Setup Project Scaffolding", "Initialize database models and API routes.", "HIGH", "COMPLETED", "2026-10-15"),
                    ("", "Design Task Management UI", "Create responsive task dashboard and action cards.", "MEDIUM", "PENDING", "2026-10-20"),
                ]
                cur.executemany(
                    "INSERT INTO preview_tasks (project_id, title, description, priority, status, due_date) VALUES (?, ?, ?, ?, ?, ?)",
                    initial
                )
                conn.commit()
                cur.execute("SELECT id, title, description, priority, status, due_date, project_id FROM preview_tasks ORDER BY id ASC")
                rows = cur.fetchall()

        tasks = []
        for r in rows:
            tasks.append({
                "id": r["id"],
                "title": r["title"],
                "description": r["description"] or "",
                "priority": r["priority"] or "MEDIUM",
                "status": r["status"] or "PENDING",
                "due_date": r["due_date"] or "2026-12-31",
                "project_id": r["project_id"] or "",
            })
        conn.close()
        return tasks

    @classmethod
    def create_task(cls, data: dict[str, Any], project_id: Optional[str] = None) -> dict[str, Any]:
        """Create a new task scoped to project_id."""
        cls.ensure_schema()
        clean_pid = str(project_id or data.get("project_id") or "").strip()
        title = (data.get("title") or "Untitled Task").strip()
        desc = (data.get("description") or "").strip()
        priority = (data.get("priority") or "MEDIUM").strip()
        status = (data.get("status") or "PENDING").strip()
        due_date = (data.get("due_date") or "2026-12-31").strip()

        conn = get_sqlite_conn()
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO preview_tasks (project_id, title, description, priority, status, due_date) VALUES (?, ?, ?, ?, ?, ?)",
            (clean_pid, title, desc, priority, status, due_date)
        )
        task_id = cur.lastrowid
        conn.commit()
        conn.close()

        return {
            "id": task_id,
            "title": title,
            "description": desc,
            "priority": priority,
            "status": status,
            "due_date": due_date,
            "project_id": clean_pid,
        }

    @classmethod
    def get_task(cls, task_id: int, project_id: Optional[str] = None) -> Optional[dict[str, Any]]:
        """Retrieve single task by ID."""
        cls.ensure_schema()
        clean_pid = str(project_id or "").strip()
        conn = get_sqlite_conn()
        cur = conn.cursor()
        if clean_pid:
            cur.execute(
                "SELECT id, title, description, priority, status, due_date, project_id FROM preview_tasks WHERE id = ? AND (project_id = ? OR project_id = '')",
                (task_id, clean_pid)
            )
        else:
            cur.execute(
                "SELECT id, title, description, priority, status, due_date, project_id FROM preview_tasks WHERE id = ?",
                (task_id,)
            )
        row = cur.fetchone()
        conn.close()
        if not row:
            return None
        return {
            "id": row["id"],
            "title": row["title"],
            "description": row["description"] or "",
            "priority": row["priority"] or "MEDIUM",
            "status": row["status"] or "PENDING",
            "due_date": row["due_date"] or "2026-12-31",
            "project_id": row["project_id"] or "",
        }

    @classmethod
    def update_task(cls, task_id: int, data: dict[str, Any], project_id: Optional[str] = None) -> Optional[dict[str, Any]]:
        """Update fields on an existing task."""
        existing = cls.get_task(task_id, project_id)
        if not existing:
            return None

        updated_title = data.get("title", existing["title"])
        updated_desc = data.get("description", existing["description"])
        updated_priority = data.get("priority", existing["priority"])
        updated_status = data.get("status", existing["status"])
        updated_due = data.get("due_date", existing["due_date"])

        conn = get_sqlite_conn()
        cur = conn.cursor()
        cur.execute(
            "UPDATE preview_tasks SET title = ?, description = ?, priority = ?, status = ?, due_date = ? WHERE id = ?",
            (updated_title, updated_desc, updated_priority, updated_status, updated_due, task_id)
        )
        conn.commit()
        conn.close()

        return {
            "id": task_id,
            "title": updated_title,
            "description": updated_desc,
            "priority": updated_priority,
            "status": updated_status,
            "due_date": updated_due,
            "project_id": existing.get("project_id", ""),
        }

    @classmethod
    def delete_task(cls, task_id: int, project_id: Optional[str] = None) -> bool:
        """Delete task by ID."""
        existing = cls.get_task(task_id, project_id)
        if not existing:
            return False

        conn = get_sqlite_conn()
        cur = conn.cursor()
        cur.execute("DELETE FROM preview_tasks WHERE id = ?", (task_id,))
        conn.commit()
        conn.close()
        return True

    @classmethod
    def get_scores(cls, project_id: Optional[str] = None) -> list[dict[str, Any]]:
        """Retrieve leaderboard scores for Snake Game."""
        cls.ensure_schema()
        clean_pid = str(project_id or "").strip()
        conn = get_sqlite_conn()
        cur = conn.cursor()
        if clean_pid:
            cur.execute(
                "SELECT id, player_name, score, created_at FROM preview_scores WHERE project_id = ? OR project_id = '' ORDER BY score DESC LIMIT 10",
                (clean_pid,)
            )
        else:
            cur.execute("SELECT id, player_name, score, created_at FROM preview_scores ORDER BY score DESC LIMIT 10")
        rows = cur.fetchall()
        conn.close()
        return [
            {
                "id": r["id"],
                "player_name": r["player_name"],
                "score": r["score"],
                "created_at": r["created_at"],
            }
            for r in rows
        ]

    @classmethod
    def add_score(cls, score: int, player_name: str = "Player", project_id: Optional[str] = None) -> dict[str, Any]:
        """Save a new score for Snake Game."""
        cls.ensure_schema()
        clean_pid = str(project_id or "").strip()
        clean_player = str(player_name or "Player").strip()[:32]

        conn = get_sqlite_conn()
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO preview_scores (project_id, player_name, score) VALUES (?, ?, ?)",
            (clean_pid, clean_player, int(score))
        )
        new_id = cur.lastrowid
        conn.commit()
        conn.close()

        return {
            "id": new_id,
            "player_name": clean_player,
            "score": int(score),
            "project_id": clean_pid,
            "status": "SAVED",
        }

    @classmethod
    def get_analytics_metrics(cls, project_id: Optional[str] = None) -> dict[str, Any]:
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
            ]
        }

