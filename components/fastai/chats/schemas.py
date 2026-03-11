from __future__ import annotations

import uuid
from enum import StrEnum

from pydantic import AwareDatetime
from sqlmodel import SQLModel


class MessageRole(StrEnum):
    """Semantic role for chat messages."""

    USER = "user"
    ASSISTANT = "assistant"


# ── Conversation schemas ──


class ConversationBase(SQLModel):
    """Shared conversation fields. No database concerns."""

    title: str | None = None


class ConversationCreate(ConversationBase):
    """Schema for creating a new conversation."""

    user_id: uuid.UUID


class ConversationRead(ConversationBase):
    """Schema for reading a conversation."""

    id: uuid.UUID
    user_id: uuid.UUID
    created_at: AwareDatetime
    updated_at: AwareDatetime


class ConversationUpdate(SQLModel):
    """Schema for partially updating a conversation. All fields optional."""

    title: str | None = None


# ── Message schemas ──


class MessageBase(SQLModel):
    """Shared message fields. No database concerns."""

    role: MessageRole
    content_text: str | None = None


class MessageCreate(MessageBase):
    """Schema for creating a new message."""

    conversation_id: uuid.UUID


class MessageRead(MessageBase):
    """Schema for reading a message.

    Messages are append-only so there is no updated_at field.
    """

    id: uuid.UUID
    conversation_id: uuid.UUID
    created_at: AwareDatetime
