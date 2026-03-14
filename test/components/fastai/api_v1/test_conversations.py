import uuid

import pytest
from httpx import AsyncClient

pytestmark = pytest.mark.integration

BASE_URL = "/conversations"


def _make_conversation_payload(
    *,
    user_id: str,
    title: str | None = "Test conversation",
) -> dict:
    payload: dict = {"user_id": user_id}
    if title is not None:
        payload["title"] = title
    return payload


async def _create_conversation(
    client: AsyncClient,
    user_id: str,
    **overrides: object,
) -> dict:
    """Helper – create a conversation and return the response body."""
    payload = _make_conversation_payload(user_id=user_id, **overrides)  # type: ignore[arg-type]
    res = await client.post(BASE_URL, json=payload)
    assert res.status_code == 201
    return res.json()


def _messages_url(conversation_id: str) -> str:
    return f"{BASE_URL}/{conversation_id}/messages"


def _make_message_payload(
    *,
    conversation_id: str,
    role: str = "user",
    content_text: str = "Hello!",
) -> dict:
    return {
        "conversation_id": conversation_id,
        "role": role,
        "content_text": content_text,
    }


async def _create_message(
    client: AsyncClient,
    conversation_id: str,
    **overrides: object,
) -> dict:
    """Helper – create a message and return the response body."""
    payload = _make_message_payload(conversation_id=conversation_id, **overrides)  # type: ignore[arg-type]
    res = await client.post(_messages_url(conversation_id), json=payload)
    assert res.status_code == 201
    return res.json()


# ═══════════════════════════════════════════════════════════════════════
# Conversations
# ═══════════════════════════════════════════════════════════════════════


# ── CREATE ──


@pytest.mark.asyncio
async def test_create_conversation(
    authenticated_client: AsyncClient, sample_user_id: uuid.UUID
) -> None:
    user_id = str(sample_user_id)
    body = await _create_conversation(authenticated_client, user_id)

    assert body["title"] == "Test conversation"
    assert body["user_id"] == user_id
    assert "id" in body
    assert "created_at" in body
    assert "updated_at" in body


@pytest.mark.asyncio
async def test_create_conversation_no_title(
    authenticated_client: AsyncClient, sample_user_id: uuid.UUID
) -> None:
    """Title is optional – should default to null."""
    user_id = str(sample_user_id)
    body = await _create_conversation(authenticated_client, user_id, title=None)

    assert body["title"] is None
    assert body["user_id"] == user_id


# ── READ (single) ──


@pytest.mark.asyncio
async def test_get_conversation(
    authenticated_client: AsyncClient, sample_user_id: uuid.UUID
) -> None:
    user_id = str(sample_user_id)
    created = await _create_conversation(authenticated_client, user_id)
    conv_id = created["id"]

    res = await authenticated_client.get(f"{BASE_URL}/{conv_id}")

    assert res.status_code == 200
    assert res.json()["id"] == conv_id
    assert res.json()["title"] == "Test conversation"


@pytest.mark.asyncio
async def test_get_conversation_not_found(authenticated_client: AsyncClient) -> None:
    fake_id = str(uuid.uuid4())
    res = await authenticated_client.get(f"{BASE_URL}/{fake_id}")
    assert res.status_code == 404


# ── READ (list) ──


@pytest.mark.asyncio
async def test_list_conversations(
    authenticated_client: AsyncClient, sample_user_id: uuid.UUID
) -> None:
    user_id = str(sample_user_id)
    await _create_conversation(authenticated_client, user_id, title="Conv A")
    await _create_conversation(authenticated_client, user_id, title="Conv B")

    res = await authenticated_client.get(BASE_URL, params={"user_id": user_id})

    assert res.status_code == 200
    titles = {c["title"] for c in res.json()}
    assert "Conv A" in titles
    assert "Conv B" in titles


@pytest.mark.asyncio
async def test_list_conversations_requires_user_id(
    authenticated_client: AsyncClient,
) -> None:
    """user_id is a required query param — omitting it returns 422."""
    res = await authenticated_client.get(BASE_URL)
    assert res.status_code == 422


@pytest.mark.asyncio
async def test_list_conversations_pagination(
    authenticated_client: AsyncClient, sample_user_id: uuid.UUID
) -> None:
    user_id = str(sample_user_id)
    for i in range(5):
        await _create_conversation(authenticated_client, user_id, title=f"Page Conv {i}")

    res = await authenticated_client.get(
        BASE_URL, params={"user_id": user_id, "offset": 0, "limit": 2}
    )

    assert res.status_code == 200
    assert len(res.json()) == 2


# ── UPDATE ──


@pytest.mark.asyncio
async def test_update_conversation(
    authenticated_client: AsyncClient, sample_user_id: uuid.UUID
) -> None:
    user_id = str(sample_user_id)
    created = await _create_conversation(authenticated_client, user_id)
    conv_id = created["id"]

    res = await authenticated_client.patch(
        f"{BASE_URL}/{conv_id}",
        json={"title": "Renamed"},
    )

    assert res.status_code == 200
    body = res.json()
    assert body["title"] == "Renamed"
    assert body["user_id"] == user_id


@pytest.mark.asyncio
async def test_update_conversation_not_found(authenticated_client: AsyncClient) -> None:
    fake_id = str(uuid.uuid4())
    res = await authenticated_client.patch(
        f"{BASE_URL}/{fake_id}",
        json={"title": "Ghost"},
    )
    assert res.status_code == 404


# ── DELETE ──


@pytest.mark.asyncio
async def test_delete_conversation(
    authenticated_client: AsyncClient, sample_user_id: uuid.UUID
) -> None:
    user_id = str(sample_user_id)
    created = await _create_conversation(authenticated_client, user_id)
    conv_id = created["id"]

    res = await authenticated_client.delete(f"{BASE_URL}/{conv_id}")
    assert res.status_code == 204

    get_res = await authenticated_client.get(f"{BASE_URL}/{conv_id}")
    assert get_res.status_code == 404


@pytest.mark.asyncio
async def test_delete_conversation_not_found(authenticated_client: AsyncClient) -> None:
    fake_id = str(uuid.uuid4())
    res = await authenticated_client.delete(f"{BASE_URL}/{fake_id}")
    assert res.status_code == 404


@pytest.mark.asyncio
async def test_deleted_conversation_excluded_from_list(
    authenticated_client: AsyncClient, sample_user_id: uuid.UUID
) -> None:
    user_id = str(sample_user_id)
    created = await _create_conversation(authenticated_client, user_id, title="Delete Me")
    conv_id = created["id"]

    await authenticated_client.delete(f"{BASE_URL}/{conv_id}")

    list_res = await authenticated_client.get(BASE_URL, params={"user_id": user_id})
    ids = [c["id"] for c in list_res.json()]
    assert conv_id not in ids


# ═══════════════════════════════════════════════════════════════════════
# Messages
# ═══════════════════════════════════════════════════════════════════════


# ── CREATE ──


@pytest.mark.asyncio
async def test_create_message(
    authenticated_client: AsyncClient, sample_user_id: uuid.UUID
) -> None:
    conv = await _create_conversation(authenticated_client, str(sample_user_id))
    conv_id = conv["id"]

    body = await _create_message(authenticated_client, conv_id)

    assert body["role"] == "user"
    assert body["content_text"] == "Hello!"
    assert body["conversation_id"] == conv_id
    assert "id" in body
    assert "created_at" in body


@pytest.mark.asyncio
async def test_create_message_assistant_role(
    authenticated_client: AsyncClient, sample_user_id: uuid.UUID
) -> None:
    conv = await _create_conversation(authenticated_client, str(sample_user_id))
    conv_id = conv["id"]

    body = await _create_message(
        authenticated_client, conv_id, role="assistant", content_text="Hi there!"
    )

    assert body["role"] == "assistant"
    assert body["content_text"] == "Hi there!"


@pytest.mark.asyncio
async def test_create_message_conversation_not_found(
    authenticated_client: AsyncClient,
) -> None:
    fake_id = str(uuid.uuid4())
    payload = _make_message_payload(conversation_id=fake_id)
    res = await authenticated_client.post(_messages_url(fake_id), json=payload)
    assert res.status_code == 404


@pytest.mark.asyncio
async def test_create_message_conversation_id_mismatch(
    authenticated_client: AsyncClient, sample_user_id: uuid.UUID
) -> None:
    """Body conversation_id must match the URL path parameter."""
    conv = await _create_conversation(authenticated_client, str(sample_user_id))
    conv_id = conv["id"]

    other_id = str(uuid.uuid4())
    payload = _make_message_payload(conversation_id=other_id)
    res = await authenticated_client.post(_messages_url(conv_id), json=payload)
    assert res.status_code == 422
    assert "does not match" in res.json()["detail"]


# ── READ (single) ──


@pytest.mark.asyncio
async def test_get_message(
    authenticated_client: AsyncClient, sample_user_id: uuid.UUID
) -> None:
    conv = await _create_conversation(authenticated_client, str(sample_user_id))
    conv_id = conv["id"]
    msg = await _create_message(authenticated_client, conv_id)
    msg_id = msg["id"]

    res = await authenticated_client.get(f"{_messages_url(conv_id)}/{msg_id}")

    assert res.status_code == 200
    assert res.json()["id"] == msg_id
    assert res.json()["content_text"] == "Hello!"


@pytest.mark.asyncio
async def test_get_message_not_found(
    authenticated_client: AsyncClient, sample_user_id: uuid.UUID
) -> None:
    conv = await _create_conversation(authenticated_client, str(sample_user_id))
    conv_id = conv["id"]
    fake_id = str(uuid.uuid4())

    res = await authenticated_client.get(f"{_messages_url(conv_id)}/{fake_id}")
    assert res.status_code == 404


@pytest.mark.asyncio
async def test_get_message_wrong_conversation(
    authenticated_client: AsyncClient, sample_user_id: uuid.UUID
) -> None:
    """A message that belongs to a different conversation should 404."""
    user_id = str(sample_user_id)
    conv_a = await _create_conversation(authenticated_client, user_id, title="Conv A")
    conv_b = await _create_conversation(authenticated_client, user_id, title="Conv B")
    msg = await _create_message(authenticated_client, conv_a["id"])

    res = await authenticated_client.get(f"{_messages_url(conv_b['id'])}/{msg['id']}")
    assert res.status_code == 404


# ── READ (list) ──


@pytest.mark.asyncio
async def test_list_messages(
    authenticated_client: AsyncClient, sample_user_id: uuid.UUID
) -> None:
    conv = await _create_conversation(authenticated_client, str(sample_user_id))
    conv_id = conv["id"]
    await _create_message(authenticated_client, conv_id, content_text="First")
    await _create_message(
        authenticated_client, conv_id, role="assistant", content_text="Second"
    )

    res = await authenticated_client.get(_messages_url(conv_id))

    assert res.status_code == 200
    messages = res.json()
    assert len(messages) >= 2
    texts = [m["content_text"] for m in messages]
    assert "First" in texts
    assert "Second" in texts


@pytest.mark.asyncio
async def test_list_messages_conversation_not_found(
    authenticated_client: AsyncClient,
) -> None:
    fake_id = str(uuid.uuid4())
    res = await authenticated_client.get(_messages_url(fake_id))
    assert res.status_code == 404


@pytest.mark.asyncio
async def test_list_messages_pagination(
    authenticated_client: AsyncClient, sample_user_id: uuid.UUID
) -> None:
    conv = await _create_conversation(authenticated_client, str(sample_user_id))
    conv_id = conv["id"]
    for i in range(5):
        await _create_message(authenticated_client, conv_id, content_text=f"Msg {i}")

    res = await authenticated_client.get(
        _messages_url(conv_id), params={"offset": 0, "limit": 2}
    )

    assert res.status_code == 200
    assert len(res.json()) == 2


# ── DELETE ──


@pytest.mark.asyncio
async def test_delete_message(
    authenticated_client: AsyncClient, sample_user_id: uuid.UUID
) -> None:
    conv = await _create_conversation(authenticated_client, str(sample_user_id))
    conv_id = conv["id"]
    msg = await _create_message(authenticated_client, conv_id)
    msg_id = msg["id"]

    res = await authenticated_client.delete(f"{_messages_url(conv_id)}/{msg_id}")
    assert res.status_code == 204

    get_res = await authenticated_client.get(f"{_messages_url(conv_id)}/{msg_id}")
    assert get_res.status_code == 404


@pytest.mark.asyncio
async def test_delete_message_not_found(
    authenticated_client: AsyncClient, sample_user_id: uuid.UUID
) -> None:
    conv = await _create_conversation(authenticated_client, str(sample_user_id))
    conv_id = conv["id"]
    fake_id = str(uuid.uuid4())

    res = await authenticated_client.delete(f"{_messages_url(conv_id)}/{fake_id}")
    assert res.status_code == 404


@pytest.mark.asyncio
async def test_delete_message_wrong_conversation(
    authenticated_client: AsyncClient, sample_user_id: uuid.UUID
) -> None:
    """Cannot delete a message via a different conversation's URL."""
    user_id = str(sample_user_id)
    conv_a = await _create_conversation(authenticated_client, user_id, title="Conv A")
    conv_b = await _create_conversation(authenticated_client, user_id, title="Conv B")
    msg = await _create_message(authenticated_client, conv_a["id"])

    res = await authenticated_client.delete(f"{_messages_url(conv_b['id'])}/{msg['id']}")
    assert res.status_code == 404

    # Original message should still exist
    get_res = await authenticated_client.get(f"{_messages_url(conv_a['id'])}/{msg['id']}")
    assert get_res.status_code == 200


@pytest.mark.asyncio
async def test_deleted_message_excluded_from_list(
    authenticated_client: AsyncClient, sample_user_id: uuid.UUID
) -> None:
    conv = await _create_conversation(authenticated_client, str(sample_user_id))
    conv_id = conv["id"]
    msg = await _create_message(authenticated_client, conv_id)
    msg_id = msg["id"]

    await authenticated_client.delete(f"{_messages_url(conv_id)}/{msg_id}")

    list_res = await authenticated_client.get(_messages_url(conv_id))
    ids = [m["id"] for m in list_res.json()]
    assert msg_id not in ids
