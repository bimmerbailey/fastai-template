from __future__ import annotations

import uuid

from pydantic import BaseModel, Field
from sqlmodel import SQLModel


class EmbeddingCreate(SQLModel):
    """Input for creating an embedding record."""

    source_type: str
    source_id: uuid.UUID
    chunk_text: str
    chunk_index: int = 0
    extra_metadata: dict = Field(default_factory=dict)


class SearchResult(BaseModel):
    """A single result from semantic search."""

    source_type: str
    source_id: uuid.UUID
    chunk_text: str
    score: float
    metadata: dict
