"""Create development_versions and development_changes tables for Phase 11H.

Revision ID: 0006_development_versions
Revises: 0005_workflow_executions
Create Date: 2026-10-02 10:55:00.000000+00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = "0006_development_versions"
down_revision: Union[str, None] = "0005_workflow_executions"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. development_versions
    op.create_table(
        "development_versions",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("project_id", sa.UUID(), nullable=False),
        sa.Column("version_number", sa.Integer(), nullable=False),
        sa.Column("parent_version_id", sa.UUID(), nullable=True),
        sa.Column("workflow_execution_id", sa.UUID(), nullable=True),
        sa.Column("artifact_key", sa.String(length=100), nullable=False, server_default="code-generation"),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="GENERATED"),
        sa.Column("content_hash", sa.String(length=64), nullable=False),
        sa.Column("manifest_hash", sa.String(length=64), nullable=False),
        sa.Column("file_count", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("total_size_bytes", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("source_reason", sa.String(length=200), nullable=False, server_default="INITIAL_GENERATION"),
        sa.Column("created_by", sa.String(length=100), nullable=False, server_default="system"),
        sa.Column(
            "requirement_ids",
            sa.JSON().with_variant(postgresql.JSONB(astext_type=sa.Text()), "postgresql"),
            server_default=sa.text("'[]'"),
            nullable=False,
        ),
        sa.Column(
            "files_manifest",
            sa.JSON().with_variant(postgresql.JSONB(astext_type=sa.Text()), "postgresql"),
            server_default=sa.text("'[]'"),
            nullable=False,
        ),
        sa.Column(
            "verification_summary",
            sa.JSON().with_variant(postgresql.JSONB(astext_type=sa.Text()), "postgresql"),
            nullable=True,
        ),
        sa.Column("diagnosis_reference", sa.String(length=100), nullable=True),
        sa.Column("remediation_reference", sa.String(length=100), nullable=True),
        sa.Column(
            "metadata",
            sa.JSON().with_variant(postgresql.JSONB(astext_type=sa.Text()), "postgresql"),
            server_default=sa.text("'{}'"),
            nullable=False,
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["parent_version_id"], ["development_versions.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_development_versions_id", "development_versions", ["id"], unique=False)
    op.create_index("ix_development_versions_project_id", "development_versions", ["project_id"], unique=False)
    op.create_index("ix_development_versions_parent_version_id", "development_versions", ["parent_version_id"], unique=False)
    op.create_index("ix_development_versions_workflow_execution_id", "development_versions", ["workflow_execution_id"], unique=False)
    op.create_index("ix_development_versions_status", "development_versions", ["status"], unique=False)
    op.create_index("ix_development_versions_project_number", "development_versions", ["project_id", "version_number"], unique=True)
    op.create_index("ix_development_versions_project_status", "development_versions", ["project_id", "status"], unique=False)

    # 2. development_changes
    op.create_table(
        "development_changes",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("project_id", sa.UUID(), nullable=False),
        sa.Column("parent_version_id", sa.UUID(), nullable=True),
        sa.Column("resulting_version_id", sa.UUID(), nullable=False),
        sa.Column("change_category", sa.String(length=32), nullable=False),
        sa.Column("change_type", sa.String(length=32), nullable=False),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("diagnosis_id", sa.String(length=100), nullable=True),
        sa.Column("remediation_proposal_id", sa.String(length=100), nullable=True),
        sa.Column("approved_by", sa.String(length=100), nullable=True),
        sa.Column("approved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "metadata",
            sa.JSON().with_variant(postgresql.JSONB(astext_type=sa.Text()), "postgresql"),
            server_default=sa.text("'{}'"),
            nullable=False,
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["parent_version_id"], ["development_versions.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["resulting_version_id"], ["development_versions.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_development_changes_id", "development_changes", ["id"], unique=False)
    op.create_index("ix_development_changes_project_id", "development_changes", ["project_id"], unique=False)
    op.create_index("ix_development_changes_resulting_version_id", "development_changes", ["resulting_version_id"], unique=False)
    op.create_index("ix_development_changes_project_created", "development_changes", ["project_id", "created_at"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_development_changes_project_created", table_name="development_changes")
    op.drop_index("ix_development_changes_resulting_version_id", table_name="development_changes")
    op.drop_index("ix_development_changes_project_id", table_name="development_changes")
    op.drop_index("ix_development_changes_id", table_name="development_changes")
    op.drop_table("development_changes")

    op.drop_index("ix_development_versions_project_status", table_name="development_versions")
    op.drop_index("ix_development_versions_project_number", table_name="development_versions")
    op.drop_index("ix_development_versions_status", table_name="development_versions")
    op.drop_index("ix_development_versions_workflow_execution_id", table_name="development_versions")
    op.drop_index("ix_development_versions_parent_version_id", table_name="development_versions")
    op.drop_index("ix_development_versions_project_id", table_name="development_versions")
    op.drop_index("ix_development_versions_id", table_name="development_versions")
    op.drop_table("development_versions")
