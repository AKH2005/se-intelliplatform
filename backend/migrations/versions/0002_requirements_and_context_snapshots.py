"""Create requirements and project_context_snapshots tables.

Revision ID: 0002_requirements_and_context_snapshots
Revises: 0001_initial
Create Date: 2026-09-22 01:30:00.000000+00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "0002_requirements_and_context_snapshots"
down_revision: Union[str, None] = "0001_initial"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Create requirements table
    op.create_table(
        "requirements",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("project_id", sa.UUID(), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("type", sa.String(length=32), nullable=False),
        sa.Column("priority", sa.String(length=32), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("is_archived", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_requirements_id", "requirements", ["id"], unique=False)
    op.create_index("ix_requirements_project_id", "requirements", ["project_id"], unique=False)
    op.create_index("ix_requirements_title", "requirements", ["title"], unique=False)
    op.create_index("ix_requirements_status", "requirements", ["status"], unique=False)
    op.create_index("ix_requirements_is_archived", "requirements", ["is_archived"], unique=False)
    op.create_index("ix_requirements_project_status", "requirements", ["project_id", "status"], unique=False)
    op.create_index("ix_requirements_project_type", "requirements", ["project_id", "type"], unique=False)
    op.create_index("ix_requirements_project_priority", "requirements", ["project_id", "priority"], unique=False)
    op.create_index("ix_requirements_project_archived", "requirements", ["project_id", "is_archived"], unique=False)

    # 2. Create project_context_snapshots table
    op.create_table(
        "project_context_snapshots",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("project_id", sa.UUID(), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column(
            "context_data",
            sa.JSON().with_variant(postgresql.JSONB(astext_type=sa.Text()), "postgresql"),
            nullable=False,
        ),
        sa.Column("summary", sa.String(length=500), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("project_id", "version", name="uq_project_context_snapshot_version"),
    )
    op.create_index("ix_project_context_snapshots_id", "project_context_snapshots", ["id"], unique=False)
    op.create_index("ix_project_context_snapshots_project_id", "project_context_snapshots", ["project_id"], unique=False)
    op.create_index("ix_project_context_snapshots_project_version", "project_context_snapshots", ["project_id", "version"], unique=False)


def downgrade() -> None:
    # 1. Drop project_context_snapshots table & indexes
    op.drop_index("ix_project_context_snapshots_project_version", table_name="project_context_snapshots")
    op.drop_index("ix_project_context_snapshots_project_id", table_name="project_context_snapshots")
    op.drop_index("ix_project_context_snapshots_id", table_name="project_context_snapshots")
    op.drop_table("project_context_snapshots")

    # 2. Drop requirements table & indexes
    op.drop_index("ix_requirements_project_archived", table_name="requirements")
    op.drop_index("ix_requirements_project_priority", table_name="requirements")
    op.drop_index("ix_requirements_project_type", table_name="requirements")
    op.drop_index("ix_requirements_project_status", table_name="requirements")
    op.drop_index("ix_requirements_is_archived", table_name="requirements")
    op.drop_index("ix_requirements_status", table_name="requirements")
    op.drop_index("ix_requirements_title", table_name="requirements")
    op.drop_index("ix_requirements_project_id", table_name="requirements")
    op.drop_index("ix_requirements_id", table_name="requirements")
    op.drop_table("requirements")
