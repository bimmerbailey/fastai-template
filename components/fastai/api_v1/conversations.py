from __future__ import annotations

import uuid

from fastapi import APIRouter, HTTPException, Query, status

from fastai.api_v1.dependencies import CurrentUserDep
from fastai.chats.models import Conversation, Message
from fastai.chats.schemas import (
    ConversationCreate,
    ConversationRead,
    ConversationUpdate,
    MessageCreate,
    MessageRead,
)
from fastai.utils.dependencies import SessionDep

router = APIRouter(prefix="/conversations", tags=["Conversations"])


# ── Conversations ──


@router.get("", response_model=list[ConversationRead])
async def list_conversations(
    session: SessionDep,
    _: CurrentUserDep,
    user_id: uuid.UUID = Query(..., description="Filter conversations by user ID"),
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=200),
) -> list[Conversation]:
    """List conversations for a user, newest first."""
    return await Conversation.get_by_user(
        session, user_id=user_id, offset=offset, limit=limit
    )


@router.get("/{conversation_id}", response_model=ConversationRead)
async def get_conversation(
    session: SessionDep,
    _: CurrentUserDep,
    conversation_id: uuid.UUID,
) -> Conversation:
    """Get a single conversation by ID."""
    conv = await Conversation.get(session, conversation_id)
    if conv is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found",
        )
    return conv


@router.post("", response_model=ConversationRead, status_code=status.HTTP_201_CREATED)
async def create_conversation(
    session: SessionDep,
    _: CurrentUserDep,
    conv_in: ConversationCreate,
) -> Conversation:
    """Create a new conversation."""
    return await Conversation.create(session, conv_in)


@router.patch("/{conversation_id}", response_model=ConversationRead)
async def update_conversation(
    session: SessionDep,
    _: CurrentUserDep,
    conversation_id: uuid.UUID,
    conv_in: ConversationUpdate,
) -> Conversation:
    """Partially update a conversation (e.g. rename title)."""
    conv = await Conversation.get(session, conversation_id)
    if conv is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found",
        )
    return await conv.update(session, conv_in)


@router.delete("/{conversation_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_conversation(
    session: SessionDep,
    _: CurrentUserDep,
    conversation_id: uuid.UUID,
) -> None:
    """Delete a conversation and all its messages (cascaded)."""
    conv = await Conversation.get(session, conversation_id)
    if conv is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found",
        )
    await conv.delete(session)


# ── Messages ──


@router.get(
    "/{conversation_id}/messages",
    response_model=list[MessageRead],
    tags=["Messages"],
)
async def list_messages(
    session: SessionDep,
    _: CurrentUserDep,
    conversation_id: uuid.UUID,
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=500),
) -> list[Message]:
    """List messages for a conversation, ordered by creation time."""
    conv = await Conversation.get(session, conversation_id)
    if conv is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found",
        )
    return await Message.get_by_conversation(
        session, conversation_id=conversation_id, offset=offset, limit=limit
    )


@router.get(
    "/{conversation_id}/messages/{message_id}",
    response_model=MessageRead,
    tags=["Messages"],
)
async def get_message(
    session: SessionDep,
    _: CurrentUserDep,
    conversation_id: uuid.UUID,
    message_id: uuid.UUID,
) -> Message:
    """Get a single message by ID."""
    msg = await Message.get(session, message_id)
    if msg is None or msg.conversation_id != conversation_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Message not found",
        )
    return msg


@router.post(
    "/{conversation_id}/messages",
    response_model=MessageRead,
    status_code=status.HTTP_201_CREATED,
    tags=["Messages"],
)
async def create_message(
    session: SessionDep,
    _: CurrentUserDep,
    conversation_id: uuid.UUID,
    msg_in: MessageCreate,
) -> Message:
    """Create a new message in a conversation."""
    conv = await Conversation.get(session, conversation_id)
    if conv is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found",
        )
    if msg_in.conversation_id != conversation_id:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="conversation_id in body does not match URL",
        )
    return await Message.create(session, msg_in)


@router.delete(
    "/{conversation_id}/messages/{message_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    tags=["Messages"],
)
async def delete_message(
    session: SessionDep,
    _: CurrentUserDep,
    conversation_id: uuid.UUID,
    message_id: uuid.UUID,
) -> None:
    """Delete a single message."""
    msg = await Message.get(session, message_id)
    if msg is None or msg.conversation_id != conversation_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Message not found",
        )
    await msg.delete(session)
