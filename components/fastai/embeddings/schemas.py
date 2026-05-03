from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, Field
from sqlmodel import SQLModel


class EmbeddingCreate(SQLModel):
    """Input for creating an embedding record."""

    source_type: str
    source_id: uuid.UUID
    chunk_text: str
    chunk_index: int = 0
    extra_metadata: dict = Field(default_factory=dict)


class EmbeddingRead(BaseModel):
    """Read-only representation of an embedding chunk."""

    id: uuid.UUID
    source_type: str
    source_id: uuid.UUID
    chunk_text: str
    chunk_index: int
    embedding_model: str
    metadata_: dict
    created_at: datetime


class SearchResult(BaseModel):
    """A single result from semantic search."""

    source_type: str
    source_id: uuid.UUID
    chunk_text: str
    score: float
    metadata: dict
