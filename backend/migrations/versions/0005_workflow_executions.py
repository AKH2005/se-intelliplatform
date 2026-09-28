"""Create workflow_executions table.

Revision ID: 0005_workflow_executions
Revises: 0004_audit_snapshot_provenance
Create Date: 2026-09-28 20:50:00.000000+00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = "0005_workflow_executions"
down_revision: Union[str, None] = "0004_audit_snapshot_provenance"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "workflow_executions",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("workflow_execution_id", sa.UUID(), nullable=False),
        sa.Column("project_id", sa.UUID(), nullable=False),
        sa.Column("workflow_id", sa.String(length=100), nullable=False),
        sa.Column("workflow_version", sa.String(length=32), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("context_snapshot_id", sa.UUID(), nullable=True),
        sa.Column("context_version", sa.Integer(), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("step_count", sa.Integer(), server_default=sa.text("0"), nullable=False),
        sa.Column("completed_steps", sa.Integer(), server_default=sa.text("0"), nullable=False),
        sa.Column("failed_steps", sa.Integer(), server_default=sa.text("0"), nullable=False),
        sa.Column("skipped_steps", sa.Integer(), server_default=sa.text("0"), nullable=False),
        sa.Column(
            "artifacts",
            sa.JSON().with_variant(postgresql.JSONB(astext_type=sa.Text()), "postgresql"),
            server_default=sa.text("'{}'"),
            nullable=False,
        ),
        sa.Column(
            "errors",
            sa.JSON().with_variant(postgresql.JSONB(astext_type=sa.Text()), "postgresql"),
            server_default=sa.text("'[]'"),
            nullable=False,
        ),
        sa.Column(
            "warnings",
            sa.JSON().with_variant(postgresql.JSONB(astext_type=sa.Text()), "postgresql"),
            server_default=sa.text("'[]'"),
            nullable=False,
        ),
        sa.Column(
            "metadata",
            sa.JSON().with_variant(postgresql.JSONB(astext_type=sa.Text()), "postgresql"),
            server_default=sa.text("'{}'"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["context_snapshot_id"], ["project_context_snapshots.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_workflow_executions_id", "workflow_executions", ["id"], unique=False)
    op.create_index("ix_workflow_executions_workflow_execution_id", "workflow_executions", ["workflow_execution_id"], unique=True)
    op.create_index("ix_workflow_executions_project_id", "workflow_executions", ["project_id"], unique=False)
    op.create_index("ix_workflow_executions_workflow_id", "workflow_executions", ["workflow_id"], unique=False)
    op.create_index("ix_workflow_executions_status", "workflow_executions", ["status"], unique=False)
    op.create_index("ix_workflow_executions_context_snapshot_id", "workflow_executions", ["context_snapshot_id"], unique=False)
    op.create_index("ix_workflow_executions_context_version", "workflow_executions", ["context_version"], unique=False)
    op.create_index("ix_workflow_executions_started_at", "workflow_executions", ["started_at"], unique=False)
    op.create_index("ix_workflow_executions_project_status", "workflow_executions", ["project_id", "status"], unique=False)
    op.create_index("ix_workflow_executions_project_started", "workflow_executions", ["project_id", "started_at"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_workflow_executions_project_started", table_name="workflow_executions")
    op.drop_index("ix_workflow_executions_project_status", table_name="workflow_executions")
    op.drop_index("ix_workflow_executions_started_at", table_name="workflow_executions")
    op.drop_index("ix_workflow_executions_context_version", table_name="workflow_executions")
    op.drop_index("ix_workflow_executions_context_snapshot_id", table_name="workflow_executions")
    op.drop_index("ix_workflow_executions_status", table_name="workflow_executions")
    op.drop_index("ix_workflow_executions_workflow_id", table_name="workflow_executions")
    op.drop_index("ix_workflow_executions_project_id", table_name="workflow_executions")
    op.drop_index("ix_workflow_executions_workflow_execution_id", table_name="workflow_executions")
    op.drop_index("ix_workflow_executions_id", table_name="workflow_executions")
    op.drop_table("workflow_executions")
