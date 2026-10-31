"""Create preview_tasks and preview_scores tables for Live Preview.

Revision ID: 0009_preview_tasks_and_scores
Revises: 0008_environments_and_deployments
Create Date: 2026-11-01 00:00:00.000000+00:00
"""

from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = "0009_preview_tasks_and_scores"
down_revision: Union[str, None] = "0008_environments_and_deployments"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    tables = inspector.get_table_names()

    # 1. preview_tasks table
    if "preview_tasks" not in tables:
        op.create_table(
            "preview_tasks",
            sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
            sa.Column("project_id", sa.UUID(), nullable=True),
            sa.Column("title", sa.String(length=255), nullable=False, server_default="Untitled Task"),
            sa.Column("description", sa.Text(), nullable=False, server_default=""),
            sa.Column("priority", sa.String(length=32), nullable=False, server_default="MEDIUM"),
            sa.Column("status", sa.String(length=32), nullable=False, server_default="PENDING"),
            sa.Column("due_date", sa.String(length=64), nullable=True, server_default="2026-12-31"),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
            sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index(
            "ix_preview_tasks_project_id",
            "preview_tasks",
            ["project_id"],
            unique=False,
        )
        op.create_index(
            "ix_preview_tasks_id",
            "preview_tasks",
            ["id"],
            unique=False,
        )

    # 2. preview_scores table
    if "preview_scores" not in tables:
        op.create_table(
            "preview_scores",
            sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
            sa.Column("project_id", sa.UUID(), nullable=True),
            sa.Column("player_name", sa.String(length=64), nullable=False, server_default="Player 1"),
            sa.Column("score", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
            sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index(
            "ix_preview_scores_project_id",
            "preview_scores",
            ["project_id"],
            unique=False,
        )
        op.create_index(
            "ix_preview_scores_score",
            "preview_scores",
            ["score"],
            unique=False,
        )


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    tables = inspector.get_table_names()

    if "preview_scores" in tables:
        indexes = [idx["name"] for idx in inspector.get_indexes("preview_scores")]
        if "ix_preview_scores_score" in indexes:
            op.drop_index("ix_preview_scores_score", table_name="preview_scores")
        if "ix_preview_scores_project_id" in indexes:
            op.drop_index("ix_preview_scores_project_id", table_name="preview_scores")
        op.drop_table("preview_scores")

    if "preview_tasks" in tables:
        indexes = [idx["name"] for idx in inspector.get_indexes("preview_tasks")]
        if "ix_preview_tasks_id" in indexes:
            op.drop_index("ix_preview_tasks_id", table_name="preview_tasks")
        if "ix_preview_tasks_project_id" in indexes:
            op.drop_index("ix_preview_tasks_project_id", table_name="preview_tasks")
        op.drop_table("preview_tasks")

