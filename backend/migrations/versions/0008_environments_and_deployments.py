"""Create environments and deployment_records tables for Phase 13.

Revision ID: 0008_environments_and_deployments
Revises: 0007_assistant_conversations
Create Date: 2026-10-04 18:00:00.000000+00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = "0008_environments_and_deployments"
down_revision: Union[str, None] = "0007_assistant_conversations"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. environments table
    op.create_table(
        "environments",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("project_id", sa.UUID(), nullable=False),
        sa.Column("environment_type", sa.String(length=50), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("status", sa.String(length=50), nullable=False, server_default="HEALTHY"),
        sa.Column("current_version_id", sa.UUID(), nullable=True),
        sa.Column("is_production", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column(
            "configuration",
            sa.JSON().with_variant(postgresql.JSONB(astext_type=sa.Text()), "postgresql"),
            nullable=False,
            server_default="{}",
        ),
        sa.Column("last_deployed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["current_version_id"], ["development_versions.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_environments_project_id",
        "environments",
        ["project_id"],
        unique=False,
    )
    op.create_index(
        "ix_environments_current_version_id",
        "environments",
        ["current_version_id"],
        unique=False,
    )
    op.create_index(
        "ix_environments_project_type",
        "environments",
        ["project_id", "environment_type"],
        unique=True,
    )

    # 2. deployment_records table
    op.create_table(
        "deployment_records",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("project_id", sa.UUID(), nullable=False),
        sa.Column("environment_id", sa.UUID(), nullable=False),
        sa.Column("version_id", sa.UUID(), nullable=False),
        sa.Column("previous_version_id", sa.UUID(), nullable=True),
        sa.Column("operation", sa.String(length=50), nullable=False, server_default="DEPLOYMENT"),
        sa.Column("source_environment_id", sa.UUID(), nullable=True),
        sa.Column("status", sa.String(length=50), nullable=False, server_default="REQUESTED"),
        sa.Column("requested_by", sa.String(length=100), nullable=False, server_default="system"),
        sa.Column("started_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "verification_summary",
            sa.JSON().with_variant(postgresql.JSONB(astext_type=sa.Text()), "postgresql"),
            nullable=True,
        ),
        sa.Column("failure_reason", sa.Text(), nullable=True),
        sa.Column("rollback_target_deployment_id", sa.UUID(), nullable=True),
        sa.Column(
            "metadata",
            sa.JSON().with_variant(postgresql.JSONB(astext_type=sa.Text()), "postgresql"),
            nullable=False,
            server_default="{}",
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["environment_id"], ["environments.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["version_id"], ["development_versions.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["previous_version_id"], ["development_versions.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["source_environment_id"], ["environments.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["rollback_target_deployment_id"], ["deployment_records.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_deployment_records_project_id",
        "deployment_records",
        ["project_id"],
        unique=False,
    )
    op.create_index(
        "ix_deployment_records_environment_id",
        "deployment_records",
        ["environment_id"],
        unique=False,
    )
    op.create_index(
        "ix_deployment_records_version_id",
        "deployment_records",
        ["version_id"],
        unique=False,
    )
    op.create_index(
        "ix_deployment_records_project_env_created",
        "deployment_records",
        ["project_id", "environment_id", "created_at"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_table("deployment_records")
    op.drop_table("environments")
