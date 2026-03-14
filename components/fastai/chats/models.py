import uuid as _uuid
from typing import Optional

from pydantic import AwareDatetime
from sqlalchemy import Enum as SAEnum
from sqlalchemy import Index
from sqlmodel import Column, DateTime, Field, Relationship, String, Text, func, select
from sqlmodel.ext.asyncio.session import AsyncSession

from fastai.chats.schemas import (
    ConversationBase,
    ConversationCreate,
    ConversationUpdate,
    MessageBase,
    MessageCreate,
    MessageRole,
)
from fastai.utils.fields import date_now
from fastai.utils.models import TimestampMixin

# ── Conversation ──


class Conversation(ConversationBase, TimestampMixin, table=True):
    """A conversation thread grouping multiple messages.

    Links to a user via user_id. Deleting a conversation cascades to
    all its messages at the database level (passive_deletes).
    """

    __tablename__ = "conversations"
    __table_args__ = (
        # Composite index: satisfies WHERE user_id = ? ORDER BY created_at DESC
        # with INCLUDE columns for index-only scans on listing queries.
        Index(
            "ix_conversations_user_id_created_at",
            "user_id",
            "created_at",
            postgresql_using="btree",
            postgresql_ops={"created_at": "DESC"},
            postgresql_include=["id", "title"],
        ),
    )

    id: _uuid.UUID | None = Field(default_factory=_uuid.uuid4, primary_key=True)
    user_id: _uuid.UUID = Field(foreign_key="users.id")
    title: str | None = Field(
        default=None, sa_column=Column(String(500), nullable=True)
    )

    # ── Relationships ──
    user: "User" = Relationship(  # noqa: F821
        back_populates="conversations",
        sa_relationship_kwargs={"lazy": "raise"},
    )
    messages: list["Message"] = Relationship(
        back_populates="conversation",
        sa_relationship_kwargs={
            "lazy": "raise",
            "passive_deletes": True,
        },
    )

    # ── CRUD ──

    @classmethod
    async def create(
        cls, session: AsyncSession, conv_in: ConversationCreate
    ) -> "Conversation":
        """Create a new conversation and persist it."""
        conv = cls.model_validate(conv_in)
        session.add(conv)
        await session.commit()
        await session.refresh(conv)
        return conv

    @classmethod
    async def get(
        cls, session: AsyncSession, conv_id: _uuid.UUID
    ) -> Optional["Conversation"]:
        """Get a single conversation by ID (without messages)."""
        return await session.get(cls, conv_id)

    @classmethod
    async def get_by_user(
        cls,
        session: AsyncSession,
        user_id: _uuid.UUID,
        offset: int = 0,
        limit: int = 50,
    ) -> list["Conversation"]:
        """Get paginated conversations for a user, newest first.

        Does NOT load messages — use Message.get_by_conversation() separately.
        """
        statement = (
            select(cls)
            .where(cls.user_id == user_id)
            .order_by(cls.created_at.desc())  # type: ignore[union-attr]
            .offset(offset)
            .limit(limit)
        )
        results = await session.exec(statement)
        return list(results.all())

    async def update(
        self, session: AsyncSession, conv_in: ConversationUpdate
    ) -> "Conversation":
        """Update this conversation with partial data."""
        update_data = conv_in.model_dump(exclude_unset=True)
        self.sqlmodel_update(update_data)
        session.add(self)
        await session.commit()
        await session.refresh(self)
        return self

    async def delete(self, session: AsyncSession) -> None:
        """Delete this conversation; PostgreSQL cascades to messages."""
        await session.delete(self)
        await session.commit()


# ── Message ──


class Message(MessageBase, table=True):
    """A single message in a conversation.

    Messages are append-only — they are never updated after creation,
    so only created_at is stored (no updated_at).
    """

    __tablename__ = "messages"
    __table_args__ = (
        # Composite index: satisfies WHERE conversation_id = ? ORDER BY created_at
        Index(
            "ix_messages_conversation_id_created_at",
            "conversation_id",
            "created_at",
        ),
    )

    id: _uuid.UUID | None = Field(default_factory=_uuid.uuid4, primary_key=True)
    conversation_id: _uuid.UUID = Field(
        foreign_key="conversations.id", ondelete="CASCADE"
    )
    role: MessageRole = Field(  # type: ignore[assignment]
        sa_column=Column(
            SAEnum(MessageRole, name="message_role", create_type=True),
            nullable=False,
        )
    )
    content_text: str | None = Field(
        default=None, sa_column=Column(Text, nullable=True)
    )

    # ── Timestamp (no updated_at — messages are immutable) ──
    created_at: AwareDatetime = Field(
        default_factory=date_now,
        sa_type=DateTime(timezone=True),
        sa_column_kwargs={"server_default": func.now(), "nullable": False},
    )

    # ── Relationships ──
    conversation: Conversation = Relationship(back_populates="messages")

    # ── CRUD ──

    @classmethod
    async def create(cls, session: AsyncSession, msg_in: MessageCreate) -> "Message":
        """Create a new message and persist it."""
        msg = cls.model_validate(msg_in)
        session.add(msg)
        await session.commit()
        await session.refresh(msg)
        return msg

    @classmethod
    async def get(
        cls, session: AsyncSession, msg_id: _uuid.UUID
    ) -> Optional["Message"]:
        """Get a single message by ID."""
        return await session.get(cls, msg_id)

    @classmethod
    async def get_by_conversation(
        cls,
        session: AsyncSession,
        conversation_id: _uuid.UUID,
        offset: int = 0,
        limit: int = 100,
    ) -> list["Message"]:
        """Get messages for a conversation, ordered by creation time."""
        statement = (
            select(cls)
            .where(cls.conversation_id == conversation_id)
            .order_by(cls.created_at)  # type: ignore[arg-type]
            .offset(offset)
            .limit(limit)
        )
        results = await session.exec(statement)
        return list(results.all())

    async def delete(self, session: AsyncSession) -> None:
        """Delete this message from the database."""
        await session.delete(self)
        await session.commit()
