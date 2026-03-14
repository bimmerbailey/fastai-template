import uuid

import pytest
from httpx import AsyncClient
from pydantic_ai import models

models.ALLOW_MODEL_REQUESTS = False

pytestmark = pytest.mark.integration

BASE_URL = "/chat"
CONVERSATIONS_URL = "/conversations"


def _chat_payload(**overrides: object) -> dict:
    """Build a minimal chat request payload."""
    payload: dict = {"message": "Hello!"}
    payload.update(overrides)
    return payload


# ═══════════════════════════════════════════════════════════════════════
# Authentication
# ═══════════════════════════════════════════════════════════════════════


@pytest.mark.asyncio
async def test_chat_unauthenticated_rejected(
    api_v1_client: AsyncClient,
) -> None:
    """POST /chat without credentials returns 401."""
    res = await api_v1_client.post(BASE_URL, json=_chat_payload())
    assert res.status_code == 401


# ═══════════════════════════════════════════════════════════════════════
# Basic response shape
# ═══════════════════════════════════════════════════════════════════════


@pytest.mark.asyncio
async def test_chat_returns_response(
    authenticated_client: AsyncClient,
) -> None:
    """POST /chat returns a valid ChatResponse with conversation_id."""
    res = await authenticated_client.post(BASE_URL, json=_chat_payload())

    assert res.status_code == 200
    body = res.json()
    assert "message" in body
    assert isinstance(body["message"], str)
    assert len(body["message"]) > 0
    assert "model" in body
    assert "usage" in body
    assert "conversation_id" in body
    # conversation_id should be a valid UUID
    uuid.UUID(body["conversation_id"])


@pytest.mark.asyncio
async def test_chat_returns_usage_stats(
    authenticated_client: AsyncClient,
) -> None:
    """POST /chat includes token usage statistics."""
    res = await authenticated_client.post(
        BASE_URL,
        json=_chat_payload(message="What time is it?"),
    )

    assert res.status_code == 200
    body = res.json()
    usage = body["usage"]
    assert usage is not None
    assert "input_tokens" in usage
    assert "output_tokens" in usage
    assert "requests" in usage
    assert usage["requests"] >= 1


@pytest.mark.asyncio
async def test_chat_response_model_field(
    authenticated_client: AsyncClient,
) -> None:
    """Response includes the model identifier."""
    res = await authenticated_client.post(BASE_URL, json=_chat_payload(message="Hi"))

    assert res.status_code == 200
    body = res.json()
    assert body["model"] == "test"


# ═══════════════════════════════════════════════════════════════════════
# Validation
# ═══════════════════════════════════════════════════════════════════════


@pytest.mark.asyncio
async def test_chat_empty_message_rejected(
    authenticated_client: AsyncClient,
) -> None:
    """POST /chat rejects empty messages with 422."""
    res = await authenticated_client.post(BASE_URL, json=_chat_payload(message=""))
    assert res.status_code == 422


@pytest.mark.asyncio
async def test_chat_missing_message_rejected(
    authenticated_client: AsyncClient,
) -> None:
    """POST /chat rejects requests without a message field."""
    res = await authenticated_client.post(BASE_URL, json={})
    assert res.status_code == 422


@pytest.mark.asyncio
async def test_chat_message_too_long_rejected(
    authenticated_client: AsyncClient,
) -> None:
    """POST /chat rejects messages exceeding max length."""
    long_message = "x" * 10001
    res = await authenticated_client.post(
        BASE_URL,
        json=_chat_payload(message=long_message),
    )
    assert res.status_code == 422


# ═══════════════════════════════════════════════════════════════════════
# Conversation creation
# ═══════════════════════════════════════════════════════════════════════


@pytest.mark.asyncio
async def test_chat_creates_new_conversation(
    authenticated_client: AsyncClient,
) -> None:
    """When conversation_id is omitted, a new conversation is created."""
    res = await authenticated_client.post(BASE_URL, json=_chat_payload())

    assert res.status_code == 200
    conversation_id = res.json()["conversation_id"]

    # Verify the conversation exists via the conversations endpoint
    conv_res = await authenticated_client.get(f"{CONVERSATIONS_URL}/{conversation_id}")
    assert conv_res.status_code == 200
    assert conv_res.json()["user_id"] is not None


@pytest.mark.asyncio
async def test_chat_continues_existing_conversation(
    authenticated_client: AsyncClient,
) -> None:
    """When conversation_id is provided, messages are added to it."""
    # First message – creates conversation
    res1 = await authenticated_client.post(
        BASE_URL, json=_chat_payload(message="First")
    )
    assert res1.status_code == 200
    conversation_id = res1.json()["conversation_id"]

    # Second message – continues conversation
    res2 = await authenticated_client.post(
        BASE_URL,
        json=_chat_payload(
            message="Second",
            conversation_id=conversation_id,
        ),
    )
    assert res2.status_code == 200
    assert res2.json()["conversation_id"] == conversation_id


@pytest.mark.asyncio
async def test_chat_invalid_conversation_id_returns_404(
    authenticated_client: AsyncClient,
) -> None:
    """Providing a non-existent conversation_id returns 404."""
    fake_id = str(uuid.uuid4())
    res = await authenticated_client.post(
        BASE_URL,
        json=_chat_payload(conversation_id=fake_id),
    )
    assert res.status_code == 404


# ═══════════════════════════════════════════════════════════════════════
# Message persistence
# ═══════════════════════════════════════════════════════════════════════


@pytest.mark.asyncio
async def test_chat_persists_user_and_assistant_messages(
    authenticated_client: AsyncClient,
) -> None:
    """Both the user message and assistant response are persisted."""
    res = await authenticated_client.post(
        BASE_URL,
        json=_chat_payload(message="What is 2+2?"),
    )
    assert res.status_code == 200
    conversation_id = res.json()["conversation_id"]

    # Fetch messages via the conversations endpoint
    msgs_res = await authenticated_client.get(
        f"{CONVERSATIONS_URL}/{conversation_id}/messages"
    )
    assert msgs_res.status_code == 200
    messages = msgs_res.json()

    assert len(messages) == 2
    assert messages[0]["role"] == "user"
    assert messages[0]["content_text"] == "What is 2+2?"
    assert messages[1]["role"] == "assistant"
    assert len(messages[1]["content_text"]) > 0


@pytest.mark.asyncio
async def test_chat_multi_turn_persists_all_messages(
    authenticated_client: AsyncClient,
) -> None:
    """Multiple turns accumulate messages in the conversation."""
    # Turn 1
    res1 = await authenticated_client.post(
        BASE_URL, json=_chat_payload(message="Turn 1")
    )
    conversation_id = res1.json()["conversation_id"]

    # Turn 2
    await authenticated_client.post(
        BASE_URL,
        json=_chat_payload(
            message="Turn 2",
            conversation_id=conversation_id,
        ),
    )

    msgs_res = await authenticated_client.get(
        f"{CONVERSATIONS_URL}/{conversation_id}/messages"
    )
    messages = msgs_res.json()

    # 2 turns × 2 messages (user + assistant) = 4 messages
    assert len(messages) == 4
    roles = [m["role"] for m in messages]
    assert roles == ["user", "assistant", "user", "assistant"]


# ═══════════════════════════════════════════════════════════════════════
# Auto-title
# ═══════════════════════════════════════════════════════════════════════


@pytest.mark.asyncio
async def test_chat_auto_titles_new_conversation(
    authenticated_client: AsyncClient,
) -> None:
    """A new conversation gets auto-titled from the first user message."""
    res = await authenticated_client.post(
        BASE_URL,
        json=_chat_payload(message="Tell me about Python"),
    )
    conversation_id = res.json()["conversation_id"]

    conv_res = await authenticated_client.get(f"{CONVERSATIONS_URL}/{conversation_id}")
    assert conv_res.json()["title"] == "Tell me about Python"


@pytest.mark.asyncio
async def test_chat_auto_title_truncates_long_messages(
    authenticated_client: AsyncClient,
) -> None:
    """Auto-title is truncated to ~100 chars with ellipsis for long messages."""
    long_msg = "A" * 200
    res = await authenticated_client.post(
        BASE_URL,
        json=_chat_payload(message=long_msg),
    )
    conversation_id = res.json()["conversation_id"]

    conv_res = await authenticated_client.get(f"{CONVERSATIONS_URL}/{conversation_id}")
    title = conv_res.json()["title"]
    # 100 chars + ellipsis character
    assert len(title) == 101
    assert title.endswith("…")


@pytest.mark.asyncio
async def test_chat_does_not_overwrite_existing_title(
    authenticated_client: AsyncClient,
) -> None:
    """Subsequent messages do not change the conversation title."""
    # First message sets the title
    res1 = await authenticated_client.post(
        BASE_URL,
        json=_chat_payload(message="Original title"),
    )
    conversation_id = res1.json()["conversation_id"]

    # Second message should not overwrite
    await authenticated_client.post(
        BASE_URL,
        json=_chat_payload(
            message="Different text",
            conversation_id=conversation_id,
        ),
    )

    conv_res = await authenticated_client.get(f"{CONVERSATIONS_URL}/{conversation_id}")
    assert conv_res.json()["title"] == "Original title"
