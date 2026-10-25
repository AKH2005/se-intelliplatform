"""Persistent Entity Models for Phase 11I Intelli Assistant & Engineering Action Layer."""

import uuid
from datetime import datetime, timezone
from typing import Any
from sqlalchemy import DateTime, ForeignKey, Index, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import JSON

from app.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class AssistantConversation(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Persistent conversation thread for the Intelli Assistant."""

    __tablename__ = "assistant_conversations"

    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        doc="Project UUID owning this conversation",
    )

    title: Mapped[str] = mapped_column(
        String(256),
        nullable=False,
        default="New Conversation",
        doc="Conversational thread title",
    )

    messages = relationship(
        "AssistantMessage",
        back_populates="conversation",
        cascade="all, delete-orphan",
        order_by="AssistantMessage.created_at.asc()",
    )
    tokens = relationship(
        "ActionConfirmationToken",
        back_populates="conversation",
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        Index("ix_assistant_conversations_project_created", "project_id", "created_at"),
    )


class AssistantMessage(Base, UUIDPrimaryKeyMixin):
    """User-visible message and action candidate record in an Assistant conversation."""

    __tablename__ = "assistant_messages"

    conversation_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("assistant_conversations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        doc="Parent conversation UUID",
    )

    role: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        doc="Role: user, assistant, system",
    )

    content: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        doc="User-visible message text",
    )

    action_id: Mapped[str | None] = mapped_column(
        String(64),
        nullable=True,
        doc="Candidate or executed action ID (from 26-action registry)",
    )

    action_status: Mapped[str | None] = mapped_column(
        String(32),
        nullable=True,
        doc="Outcome status: SUCCESS, FAILED, PENDING_CONFIRMATION, etc.",
    )

    target_id: Mapped[str | None] = mapped_column(
        String(128),
        nullable=True,
        doc="Optional target resource ID",
    )

    structured_payload: Mapped[dict[str, Any] | None] = mapped_column(
        JSON().with_variant(JSONB, "postgresql"),
        nullable=True,
        doc="Structured action result data for rich UI rendering",
    )

    referenced_entity_type: Mapped[str | None] = mapped_column(
        String(64),
        nullable=True,
        doc="Type of entity discussed: version, diagnosis, proposal, workflow, requirement",
    )

    referenced_entity_id: Mapped[str | None] = mapped_column(
        String(128),
        nullable=True,
        doc="UUID or ID of referenced entity",
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    conversation = relationship("AssistantConversation", back_populates="messages")
    action_audits = relationship("AssistantActionAudit", back_populates="message")

    __table_args__ = (
        Index("ix_assistant_messages_conversation_created", "conversation_id", "created_at"),
    )


class AssistantActionAudit(Base, UUIDPrimaryKeyMixin):
    """Audit record capturing every engineering action dispatched or confirmed."""

    __tablename__ = "assistant_action_audits"

    message_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("assistant_messages.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        doc="Triggering AssistantMessage UUID",
    )

    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        doc="Project UUID owning this action",
    )

    action_id: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        index=True,
        doc="Action ID from 26-action registry",
    )

    category: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        doc="Operational category: READ_ONLY, ANALYSIS, GENERATION, EXECUTION, MUTATING",
    )

    parameters: Mapped[dict[str, Any]] = mapped_column(
        JSON().with_variant(JSONB, "postgresql"),
        default=dict,
        server_default="{}",
        nullable=False,
        doc="Sanitized parameters supplied to the action",
    )

    result_status: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        doc="Outcome: SUCCESS, FAILED, PENDING_CONFIRMATION, REJECTED",
    )

    confirmed_by: Mapped[str | None] = mapped_column(
        String(128),
        nullable=True,
        doc="User or identity that confirmed the mutating action",
    )

    confirmed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        doc="Timestamp of human confirmation",
    )

    execution_duration_ms: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        doc="Action dispatch execution duration in milliseconds",
    )

    metadata_payload: Mapped[dict[str, Any]] = mapped_column(
        "metadata",
        JSON().with_variant(JSONB, "postgresql"),
        default=dict,
        server_default="{}",
        nullable=False,
        doc="Additional execution metadata (warnings, errors, audit refs)",
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    message = relationship("AssistantMessage", back_populates="action_audits")

    __table_args__ = (
        Index("ix_assistant_action_audits_project_created", "project_id", "created_at"),
    )


class ActionConfirmationToken(Base):
    """Anti-replay cryptographic token binding a pending mutating action."""

    __tablename__ = "assistant_confirmation_tokens"

    token_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    token_hash: Mapped[str] = mapped_column(
        String(128),
        unique=True,
        nullable=False,
        index=True,
        doc="Cryptographic token string provided to client",
    )

    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        doc="Target project UUID",
    )

    conversation_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("assistant_conversations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        doc="Conversation UUID context",
    )

    action_id: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        doc="Action ID from 26-action registry",
    )

    target_id: Mapped[str | None] = mapped_column(
        String(128),
        nullable=True,
        doc="Authorized target resource ID",
    )

    parameters_hash: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        doc="SHA-256 hash of bound canonical parameters",
    )

    parameters_payload: Mapped[dict[str, Any]] = mapped_column(
        JSON().with_variant(JSONB, "postgresql"),
        default=dict,
        server_default="{}",
        nullable=False,
        doc="Exact parameters payload to be executed upon confirmation",
    )

    issued_to_user_id: Mapped[str] = mapped_column(
        String(128),
        default="assistant_user",
        nullable=False,
        doc="User identity the token was issued to",
    )

    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        doc="Timestamp after which token cannot be redeemed (default 10m TTL)",
    )

    consumed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        default=None,
        doc="Timestamp when redeemed. Single-use: if not null, replay rejected",
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    conversation = relationship("AssistantConversation", back_populates="tokens")

    __table_args__ = (
        Index("ix_assistant_tokens_project_action", "project_id", "action_id"),
    )
