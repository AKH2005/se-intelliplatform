"""Create agent_execution_audits table.

Revision ID: 0003_agent_execution_audits
Revises: 0002_requirements_and_context_snapshots
Create Date: 2026-09-22 01:50:00.000000+00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "0003_agent_execution_audits"
down_revision: Union[str, None] = "0002_requirements_and_context_snapshots"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "agent_execution_audits",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("execution_id", sa.UUID(), nullable=False),
        sa.Column("project_id", sa.UUID(), nullable=False),
        sa.Column("agent_id", sa.String(length=100), nullable=False),
        sa.Column("agent_version", sa.String(length=32), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("context_version", sa.Integer(), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("output_summary", sa.Text(), nullable=True),
        sa.Column("error_code", sa.String(length=64), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column(
            "metadata",
            sa.JSON().with_variant(postgresql.JSONB(astext_type=sa.Text()), "postgresql"),
            server_default=sa.text("'{}'"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_agent_execution_audits_id", "agent_execution_audits", ["id"], unique=False)
    op.create_index("ix_agent_execution_audits_execution_id", "agent_execution_audits", ["execution_id"], unique=True)
    op.create_index("ix_agent_execution_audits_project_id", "agent_execution_audits", ["project_id"], unique=False)
    op.create_index("ix_agent_execution_audits_agent_id", "agent_execution_audits", ["agent_id"], unique=False)
    op.create_index("ix_agent_execution_audits_status", "agent_execution_audits", ["status"], unique=False)
    op.create_index("ix_agent_execution_audits_context_version", "agent_execution_audits", ["context_version"], unique=False)
    op.create_index("ix_agent_audits_project_agent", "agent_execution_audits", ["project_id", "agent_id"], unique=False)
    op.create_index("ix_agent_audits_project_status", "agent_execution_audits", ["project_id", "status"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_agent_audits_project_status", table_name="agent_execution_audits")
    op.drop_index("ix_agent_audits_project_agent", table_name="agent_execution_audits")
    op.drop_index("ix_agent_execution_audits_context_version", table_name="agent_execution_audits")
    op.drop_index("ix_agent_execution_audits_status", table_name="agent_execution_audits")
    op.drop_index("ix_agent_execution_audits_agent_id", table_name="agent_execution_audits")
    op.drop_index("ix_agent_execution_audits_project_id", table_name="agent_execution_audits")
    op.drop_index("ix_agent_execution_audits_execution_id", table_name="agent_execution_audits")
    op.drop_index("ix_agent_execution_audits_id", table_name="agent_execution_audits")
    op.drop_table("agent_execution_audits")
