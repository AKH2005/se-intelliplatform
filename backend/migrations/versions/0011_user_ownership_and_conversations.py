"""Add user_id to assistant_conversations and owner_id to projects.

Revision ID: 0011_user_ownership
Revises: 0010_users_table
Create Date: 2026-11-18 23:45:00.000000+00:00
"""

from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "0011_user_ownership"
down_revision: Union[str, None] = "0010_users_table"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    tables = inspector.get_table_names()

    # 1. Add owner_id to projects if not present
    if "projects" in tables:
        cols = [c["name"] for c in inspector.get_columns("projects")]
        if "owner_id" not in cols:
            op.add_column("projects", sa.Column("owner_id", sa.UUID(), nullable=True))
            if "users" in tables:
                try:
                    op.create_foreign_key(
                        "fk_projects_owner_id_users",
                        "projects",
                        "users",
                        ["owner_id"],
                        ["id"],
                        ondelete="SET NULL",
                    )
                except Exception:
                    pass
            try:
                op.create_index("ix_projects_owner_id", "projects", ["owner_id"], unique=False)
            except Exception:
                pass

    # 2. Add user_id to assistant_conversations if not present
    if "assistant_conversations" in tables:
        cols = [c["name"] for c in inspector.get_columns("assistant_conversations")]
        if "user_id" not in cols:
            op.add_column("assistant_conversations", sa.Column("user_id", sa.UUID(), nullable=True))
            if "users" in tables:
                try:
                    op.create_foreign_key(
                        "fk_assistant_conversations_user_id_users",
                        "assistant_conversations",
                        "users",
                        ["user_id"],
                        ["id"],
                        ondelete="CASCADE",
                    )
                except Exception:
                    pass
            try:
                op.create_index(
                    "ix_assistant_conversations_user_project",
                    "assistant_conversations",
                    ["user_id", "project_id"],
                    unique=False,
                )
            except Exception:
                pass


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    tables = inspector.get_table_names()

    if "assistant_conversations" in tables:
        cols = [c["name"] for c in inspector.get_columns("assistant_conversations")]
        if "user_id" in cols:
            try:
                op.drop_index("ix_assistant_conversations_user_project", table_name="assistant_conversations")
            except Exception:
                pass
            try:
                op.drop_constraint("fk_assistant_conversations_user_id_users", "assistant_conversations", type_="foreignkey")
            except Exception:
                pass
            op.drop_column("assistant_conversations", "user_id")

    if "projects" in tables:
        cols = [c["name"] for c in inspector.get_columns("projects")]
        if "owner_id" in cols:
            try:
                op.drop_index("ix_projects_owner_id", table_name="projects")
            except Exception:
                pass
            try:
                op.drop_constraint("fk_projects_owner_id_users", "projects", type_="foreignkey")
            except Exception:
                pass
            op.drop_column("projects", "owner_id")
