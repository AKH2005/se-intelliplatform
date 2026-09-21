"""Add context_snapshot_id and make context_version nullable in agent_execution_audits.

Revision ID: 0004_audit_snapshot_provenance
Revises: 0003_agent_execution_audits
Create Date: 2026-09-22 02:05:00.000000+00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "0004_audit_snapshot_provenance"
down_revision: Union[str, None] = "0003_agent_execution_audits"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("agent_execution_audits") as batch_op:
        batch_op.add_column(
            sa.Column("context_snapshot_id", sa.UUID(), nullable=True)
        )
        batch_op.alter_column(
            "context_version",
            existing_type=sa.Integer(),
            nullable=True,
        )
        batch_op.create_foreign_key(
            "fk_agent_audits_snapshot_id",
            "project_context_snapshots",
            ["context_snapshot_id"],
            ["id"],
            ondelete="SET NULL",
        )
        batch_op.create_index(
            "ix_agent_execution_audits_context_snapshot_id",
            ["context_snapshot_id"],
            unique=False,
        )


def downgrade() -> None:
    with op.batch_alter_table("agent_execution_audits") as batch_op:
        batch_op.drop_index("ix_agent_execution_audits_context_snapshot_id")
        batch_op.drop_constraint("fk_agent_audits_snapshot_id", type_="foreignkey")
        batch_op.alter_column(
            "context_version",
            existing_type=sa.Integer(),
            nullable=False,
        )
        batch_op.drop_column("context_snapshot_id")
