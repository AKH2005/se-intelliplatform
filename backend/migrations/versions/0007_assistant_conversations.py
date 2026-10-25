"""Create assistant tables and confirmation tokens for Phase 11I.

Revision ID: 0007_assistant_conversations
Revises: 0006_development_versions
Create Date: 2026-10-02 11:35:00.000000+00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = "0007_assistant_conversations"
down_revision: Union[str, None] = "0006_development_versions"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. assistant_conversations
    op.create_table(
        "assistant_conversations",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("project_id", sa.UUID(), nullable=False),
        sa.Column("title", sa.String(length=256), nullable=False, server_default="New Conversation"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_assistant_conversations_project_created",
        "assistant_conversations",
        ["project_id", "created_at"],
        unique=False,
    )

    # 2. assistant_messages
    op.create_table(
        "assistant_messages",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("conversation_id", sa.UUID(), nullable=False),
        sa.Column("role", sa.String(length=32), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("action_id", sa.String(length=64), nullable=True),
        sa.Column("action_status", sa.String(length=32), nullable=True),
        sa.Column("target_id", sa.String(length=128), nullable=True),
        sa.Column(
            "structured_payload",
            sa.JSON().with_variant(postgresql.JSONB(astext_type=sa.Text()), "postgresql"),
            nullable=True,
        ),
        sa.Column("referenced_entity_type", sa.String(length=64), nullable=True),
        sa.Column("referenced_entity_id", sa.String(length=128), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["conversation_id"], ["assistant_conversations.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_assistant_messages_conversation_created",
        "assistant_messages",
        ["conversation_id", "created_at"],
        unique=False,
    )

    # 3. assistant_action_audits
    op.create_table(
        "assistant_action_audits",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("message_id", sa.UUID(), nullable=True),
        sa.Column("project_id", sa.UUID(), nullable=False),
        sa.Column("action_id", sa.String(length=64), nullable=False),
        sa.Column("category", sa.String(length=32), nullable=False),
        sa.Column(
            "parameters",
            sa.JSON().with_variant(postgresql.JSONB(astext_type=sa.Text()), "postgresql"),
            server_default=sa.text("'{}'"),
            nullable=False,
        ),
        sa.Column("result_status", sa.String(length=32), nullable=False),
        sa.Column("confirmed_by", sa.String(length=128), nullable=True),
        sa.Column("confirmed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("execution_duration_ms", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column(
            "metadata",
            sa.JSON().with_variant(postgresql.JSONB(astext_type=sa.Text()), "postgresql"),
            server_default=sa.text("'{}'"),
            nullable=False,
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["message_id"], ["assistant_messages.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_assistant_action_audits_project_created",
        "assistant_action_audits",
        ["project_id", "created_at"],
        unique=False,
    )
    op.create_index(
        "ix_assistant_action_audits_action_id",
        "assistant_action_audits",
        ["action_id"],
        unique=False,
    )

    # 4. assistant_confirmation_tokens
    op.create_table(
        "assistant_confirmation_tokens",
        sa.Column("token_id", sa.UUID(), nullable=False),
        sa.Column("token_hash", sa.String(length=128), nullable=False),
        sa.Column("project_id", sa.UUID(), nullable=False),
        sa.Column("conversation_id", sa.UUID(), nullable=False),
        sa.Column("action_id", sa.String(length=64), nullable=False),
        sa.Column("target_id", sa.String(length=128), nullable=True),
        sa.Column("parameters_hash", sa.String(length=64), nullable=False),
        sa.Column(
            "parameters_payload",
            sa.JSON().with_variant(postgresql.JSONB(astext_type=sa.Text()), "postgresql"),
            server_default=sa.text("'{}'"),
            nullable=False,
        ),
        sa.Column("issued_to_user_id", sa.String(length=128), nullable=False, server_default="assistant_user"),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("consumed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["conversation_id"], ["assistant_conversations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("token_id"),
    )
    op.create_index(
        "ix_assistant_confirmation_tokens_token_hash",
        "assistant_confirmation_tokens",
        ["token_hash"],
        unique=True,
    )
    op.create_index(
        "ix_assistant_tokens_project_action",
        "assistant_confirmation_tokens",
        ["project_id", "action_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_table("assistant_confirmation_tokens")
    op.drop_table("assistant_action_audits")
    op.drop_table("assistant_messages")
    op.drop_table("assistant_conversations")
