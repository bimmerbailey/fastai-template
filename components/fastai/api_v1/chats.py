import uuid

import structlog.stdlib
from fastapi import APIRouter, HTTPException, status

from fastai.agents.core import get_usage_limits, messages_to_history
from fastai.agents.dependencies import AgentDeps
from fastai.agents.schemas import ChatRequest, ChatResponse, ChatUsage
from fastai.api_v1.dependencies import AgentDep, AgentSettingsDep, CurrentUserDep
from fastai.chats.models import Conversation, Message
from fastai.chats.schemas import (
    ConversationCreate,
    ConversationUpdate,
    MessageCreate,
    MessageRole,
)
from fastai.utils.dependencies import EngineDep, SessionDep

logger = structlog.stdlib.get_logger(__name__)

router = APIRouter(prefix="/chat", tags=["Chat"])

MAX_TITLE_LENGTH = 100


def _auto_title(text: str) -> str:
    """Derive a short conversation title from the first user message."""
    title = text.strip().replace("\n", " ")
    if len(title) > MAX_TITLE_LENGTH:
        title = title[:MAX_TITLE_LENGTH].rstrip() + "…"
    return title


@router.post("", response_model=ChatResponse)
async def chat(
    user: CurrentUserDep,
    chat_request: ChatRequest,
    agent: AgentDep,
    settings: AgentSettingsDep,
    engine: EngineDep,
    session: SessionDep,
) -> ChatResponse:
    """Send a message to the AI chat agent and receive a response.

    If ``conversation_id`` is provided the message is appended to that
    conversation and the full history is sent to the model.  Otherwise, a
    new conversation is created automatically.
    """
    logger.info(
        "Chat request received",
        message_length=len(chat_request.message),
        conversation_id=str(chat_request.conversation_id),
    )

    # ── Load or create conversation ──
    conversation: Conversation
    needs_title: bool
    if chat_request.conversation_id is not None:
        conv = await Conversation.get(session, chat_request.conversation_id)
        if conv is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conversation not found",
            )
        conversation = conv
        needs_title = conv.title is None
    else:
        conversation = await Conversation.create(
            session,
            ConversationCreate(user_id=user.id),
        )
        # Newly created conversations always need a title
        needs_title = True

    assert conversation.id is not None
    conversation_id: uuid.UUID = conversation.id

    # ── Build message history from persisted messages ──
    existing_messages = await Message.get_by_conversation(
        session, conversation_id=conversation_id
    )
    message_history = messages_to_history(existing_messages)

    # ── Persist the user message ──
    await Message.create(
        session,
        MessageCreate(
            conversation_id=conversation_id,
            role=MessageRole.USER,
            content_text=chat_request.message,
        ),
    )

    # ── Run the agent ──
    deps = AgentDeps(engine=engine, settings=settings)
    usage_limits = get_usage_limits(settings)

    result = await agent.run(
        chat_request.message,
        deps=deps,
        usage_limits=usage_limits,
        message_history=message_history,
    )

    assistant_text: str = result.output

    # ── Persist the assistant response ──
    await Message.create(
        session,
        MessageCreate(
            conversation_id=conversation_id,
            role=MessageRole.ASSISTANT,
            content_text=assistant_text,
        ),
    )

    # ── Auto-title on first message ──
    if needs_title:
        # Re-fetch the conversation since prior commits expired the object
        conversation = await Conversation.get(session, conversation_id)  # pyright: ignore[reportAssignmentType]
        await conversation.update(
            session,
            ConversationUpdate(title=_auto_title(chat_request.message)),
        )

    # ── Build response ──
    run_usage = result.usage()
    usage = ChatUsage(
        input_tokens=run_usage.input_tokens,
        output_tokens=run_usage.output_tokens,
        requests=run_usage.requests,
    )

    logger.info(
        "Chat response generated",
        conversation_id=str(conversation_id),
        input_tokens=usage.input_tokens,
        output_tokens=usage.output_tokens,
        requests=usage.requests,
    )

    return ChatResponse(
        message=assistant_text,
        model=settings.model,
        conversation_id=conversation_id,
        usage=usage,
    )
