from __future__ import annotations

import uuid

from pydantic import BaseModel, Field


class ChatUsage(BaseModel):
    """Token usage statistics for a chat response."""

    input_tokens: int = Field(description="Number of input tokens consumed.")
    output_tokens: int = Field(description="Number of output tokens generated.")
    requests: int = Field(description="Number of LLM requests made.")


class ChatRequest(BaseModel):
    """Request body for the chat endpoint."""

    message: str = Field(
        ...,
        min_length=1,
        max_length=10000,
        description="The user message to send to the agent.",
    )
    conversation_id: uuid.UUID | None = Field(
        default=None,
        description=(
            "Continue an existing conversation. Omit to start a new conversation."
        ),
    )


class ChatResponse(BaseModel):
    """Response body from the chat endpoint."""

    message: str = Field(description="The agent's response message.")
    model: str = Field(description="The model used for this response.")
    conversation_id: uuid.UUID = Field(
        description="The conversation this message belongs to.",
    )
    usage: ChatUsage | None = Field(default=None, description="Token usage statistics.")
