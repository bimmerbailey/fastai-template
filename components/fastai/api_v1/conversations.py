import uuid

from fastapi import APIRouter, HTTPException, Query, status
from sqlmodel.ext.asyncio.session import AsyncSession

from fastai.api_v1.dependencies import CurrentUserDep
from fastai.chats.models import Conversation, Message
from fastai.chats.schemas import (
    ConversationBase,
    ConversationCreate,
    ConversationRead,
    ConversationUpdate,
    MessageCreate,
    MessageRead,
)
from fastai.utils.dependencies import SessionDep

router = APIRouter(prefix="/conversations", tags=["Conversations"])


async def _get_user_conversation(
    session: AsyncSession, conv_id: uuid.UUID, user_id: uuid.UUID
) -> Conversation:
    """Fetch a conversation belonging to the given user, or raise 404."""
    conv = await Conversation.get(session, conv_id, user_id=user_id)  # pyright: ignore[reportCallIssue]
    if conv is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found",
        )
    return conv


# ── Conversations ──


@router.get("", response_model=list[ConversationRead])
async def list_conversations(
    session: SessionDep,
    current_user: CurrentUserDep,
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=200),
) -> list[Conversation]:
    """List conversations for a user, newest first."""
    return await Conversation.get_by_user(
        session, user_id=current_user.id, offset=offset, limit=limit
    )


@router.get("/{conversation_id}", response_model=ConversationRead)
async def get_conversation(
    session: SessionDep,
    current_user: CurrentUserDep,
    conversation_id: uuid.UUID,
) -> Conversation:
    """Get a single conversation by ID."""
    return await _get_user_conversation(session, conversation_id, current_user.id)


@router.post("", response_model=ConversationRead, status_code=status.HTTP_201_CREATED)
async def create_conversation(
    session: SessionDep,
    user: CurrentUserDep,
    conv_in: ConversationBase,
) -> Conversation:
    """Create a new conversation."""
    return await Conversation.create(
        session, ConversationCreate(user_id=user.id, **conv_in.model_dump())
    )


@router.patch("/{conversation_id}", response_model=ConversationRead)
async def update_conversation(
    session: SessionDep,
    current_user: CurrentUserDep,
    conversation_id: uuid.UUID,
    conv_in: ConversationUpdate,
) -> Conversation:
    """Partially update a conversation (e.g. rename title)."""
    conv = await _get_user_conversation(session, conversation_id, current_user.id)
    return await conv.update(session, conv_in)


@router.delete("/{conversation_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_conversation(
    session: SessionDep,
    current_user: CurrentUserDep,
    conversation_id: uuid.UUID,
) -> None:
    """Delete a conversation and all its messages (cascaded)."""
    conv = await _get_user_conversation(session, conversation_id, current_user.id)
    await conv.delete(session)


# ── Messages ──


@router.get(
    "/{conversation_id}/messages",
    response_model=list[MessageRead],
    tags=["Messages"],
)
async def list_messages(
    session: SessionDep,
    current_user: CurrentUserDep,
    conversation_id: uuid.UUID,
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=500),
) -> list[Message]:
    """List messages for a conversation, ordered by creation time."""
    await _get_user_conversation(session, conversation_id, current_user.id)
    return await Message.get_by_conversation(
        session,
        conversation_id=conversation_id,
        user_id=current_user.id,  # pyright: ignore[reportCallIssue]
        offset=offset,
        limit=limit,
    )


@router.get(
    "/{conversation_id}/messages/{message_id}",
    response_model=MessageRead,
    tags=["Messages"],
)
async def get_message(
    session: SessionDep,
    current_user: CurrentUserDep,
    conversation_id: uuid.UUID,
    message_id: uuid.UUID,
) -> Message:
    """Get a single message by ID."""
    msg = await Message.get(session, message_id, user_id=current_user.id)  # pyright: ignore[reportCallIssue]
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
    current_user: CurrentUserDep,
    conversation_id: uuid.UUID,
    msg_in: MessageCreate,
) -> Message:
    """Create a new message in a conversation."""
    await _get_user_conversation(session, conversation_id, current_user.id)
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
    current_user: CurrentUserDep,
    conversation_id: uuid.UUID,
    message_id: uuid.UUID,
) -> None:
    """Delete a single message."""
    msg = await Message.get(session, message_id, user_id=current_user.id)  # pyright: ignore[reportCallIssue]
    if msg is None or msg.conversation_id != conversation_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Message not found",
        )
    await msg.delete(session)
