"""Create users table for Authentication and Authorization.

Revision ID: 0010_users_table
Revises: 0009_preview_tasks_and_scores
Create Date: 2026-11-18 00:00:00.000000+00:00
"""

from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "0010_users_table"
down_revision: Union[str, None] = "0009_preview_tasks_and_scores"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    tables = inspector.get_table_names()

    # 1. users table
    if "users" not in tables:
        op.create_table(
            "users",
            sa.Column("id", sa.UUID(), nullable=False),
            sa.Column("email", sa.String(length=255), nullable=False),
            sa.Column("name", sa.String(length=255), nullable=False),
            sa.Column("hashed_password", sa.String(length=255), nullable=False),
            sa.Column("role", sa.String(length=32), nullable=False, server_default="user"),
            sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("1")),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.PrimaryKeyConstraint("id"),
        )
        op.create_index(
            "ix_users_id",
            "users",
            ["id"],
            unique=False,
        )
        op.create_index(
            "ix_users_email",
            "users",
            ["email"],
            unique=True,
        )


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    tables = inspector.get_table_names()

    if "users" in tables:
        indexes = [idx["name"] for idx in inspector.get_indexes("users")]
        if "ix_users_email" in indexes:
            op.drop_index("ix_users_email", table_name="users")
        if "ix_users_id" in indexes:
            op.drop_index("ix_users_id", table_name="users")
        op.drop_table("users")
