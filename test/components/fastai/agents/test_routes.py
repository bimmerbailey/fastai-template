import pytest
from httpx import AsyncClient
from pydantic_ai import models

models.ALLOW_MODEL_REQUESTS = False

pytestmark = pytest.mark.integration

BASE_URL = "/chat"


@pytest.mark.asyncio
async def test_chat_returns_response(chat_client: AsyncClient) -> None:
    """POST /chat returns a valid ChatResponse."""
    res = await chat_client.post(BASE_URL, json={"message": "Hello!"})

    assert res.status_code == 200
    body = res.json()
    assert "message" in body
    assert isinstance(body["message"], str)
    assert len(body["message"]) > 0
    assert "model" in body
    assert "usage" in body


@pytest.mark.asyncio
async def test_chat_returns_usage_stats(chat_client: AsyncClient) -> None:
    """POST /chat includes token usage statistics."""
    res = await chat_client.post(BASE_URL, json={"message": "What time is it?"})

    assert res.status_code == 200
    body = res.json()
    usage = body["usage"]
    assert usage is not None
    assert "input_tokens" in usage
    assert "output_tokens" in usage
    assert "requests" in usage
    assert usage["requests"] >= 1


@pytest.mark.asyncio
async def test_chat_empty_message_rejected(chat_client: AsyncClient) -> None:
    """POST /chat rejects empty messages with 422."""
    res = await chat_client.post(BASE_URL, json={"message": ""})
    assert res.status_code == 422


@pytest.mark.asyncio
async def test_chat_missing_message_rejected(chat_client: AsyncClient) -> None:
    """POST /chat rejects requests without a message field."""
    res = await chat_client.post(BASE_URL, json={})
    assert res.status_code == 422


@pytest.mark.asyncio
async def test_chat_message_too_long_rejected(chat_client: AsyncClient) -> None:
    """POST /chat rejects messages exceeding max length."""
    long_message = "x" * 10001
    res = await chat_client.post(BASE_URL, json={"message": long_message})
    assert res.status_code == 422


@pytest.mark.asyncio
async def test_chat_response_model_field(chat_client: AsyncClient) -> None:
    """Response includes the model identifier."""
    res = await chat_client.post(BASE_URL, json={"message": "Hi"})

    assert res.status_code == 200
    body = res.json()
    assert body["model"] == "test"
