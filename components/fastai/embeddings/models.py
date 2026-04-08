import hashlib
import uuid as _uuid
from typing import Any, Optional

from pgvector.sqlalchemy import HALFVEC
from pydantic import AwareDatetime
from sqlalchemy import Index, SmallInteger, String, Text, UniqueConstraint
from sqlalchemy.dialects import postgresql
from sqlmodel import Column, DateTime, Field, SQLModel, func, select, text
from sqlmodel.ext.asyncio.session import AsyncSession

from fastai.embeddings.schemas import EmbeddingCreate, SearchResult
from fastai.embeddings.settings import EmbeddingSettings
from fastai.utils.fields import date_now


def get_embedding_dimensions() -> int:
    return EmbeddingSettings().dimensions


class Embedding(SQLModel, table=True):
    """Polymorphic embeddings table with pgvector halfvec storage.

    Stores vector embeddings for any source type (items, documents, etc.)
    using a single table with HNSW indexing for fast cosine similarity search.

    .. todo:: Add a "reset and re-embed" admin endpoint or CLI command so
       users can clear all embeddings and trigger re-indexing when switching
       embedding models (similar to Open WebUI's "Reset Vector Storage").
    """

    __tablename__ = "embeddings"  # pyright: ignore[reportAssignmentType]
    __table_args__ = (
        UniqueConstraint(
            "source_type",
            "source_id",
            "chunk_index",
            "embedding_model",
            name="uq_embeddings_source_chunk_model",
        ),
        Index(
            "ix_embeddings_halfvec_hnsw",
            "embedding",
            postgresql_using="hnsw",
            postgresql_with={"m": 16, "ef_construction": 128},
            postgresql_ops={"embedding": "halfvec_cosine_ops"},
        ),
        Index(
            "ix_embeddings_source",
            "source_type",
            "source_id",
        ),
    )

    id: _uuid.UUID = Field(default_factory=_uuid.uuid4, primary_key=True)
    source_type: str = Field(sa_column=Column(String, nullable=False))
    source_id: _uuid.UUID = Field(nullable=False)
    embedding: Any = Field(
        sa_column=Column(HALFVEC(get_embedding_dimensions()), nullable=False)  # pyright: ignore[reportArgumentType]
    )
    content_hash: str = Field(sa_column=Column(String, nullable=False))
    chunk_index: int = Field(
        default=0,
        sa_column=Column(SmallInteger, nullable=False, server_default=text("0")),
    )
    chunk_text: str = Field(sa_column=Column(Text, nullable=False))
    embedding_model: str = Field(sa_column=Column(String, nullable=False))
    token_count: Optional[int] = Field(
        default=None,
        sa_column=Column(SmallInteger, nullable=True),
    )
    metadata_: dict = Field(
        default_factory=dict,
        sa_column=Column(
            "metadata",
            postgresql.JSONB,
            server_default=text("'{}'::jsonb"),
            nullable=False,
        ),
    )

    # No updated_at — embeddings are replaced, not updated in place.
    created_at: AwareDatetime = Field(
        default_factory=date_now,
        sa_type=DateTime(timezone=True),  # pyright: ignore[reportArgumentType]
        sa_column_kwargs={"server_default": func.now(), "nullable": False},
    )

    @staticmethod
    def hash_content(content: str) -> str:
        """SHA-256 hash of content for change detection.

        Args:
            content: The text to hash.

        Returns:
            Hex-encoded SHA-256 digest.
        """
        return hashlib.sha256(content.encode()).hexdigest()

    @classmethod
    async def get_by_source(
        cls,
        session: AsyncSession,
        source_type: str,
        source_id: _uuid.UUID,
        embedding_model: str,
        chunk_index: int = 0,
    ) -> "Embedding | None":
        """Get an embedding record by its source reference.

        Args:
            session: The async database session.
            source_type: The type of source (e.g. "item").
            source_id: The UUID of the source record.
            embedding_model: The model used to generate the embedding.
            chunk_index: The chunk index (default 0 for single-chunk sources).

        Returns:
            The matching Embedding record, or None.
        """
        statement = select(cls).where(
            cls.source_type == source_type,
            cls.source_id == source_id,
            cls.chunk_index == chunk_index,
            cls.embedding_model == embedding_model,
        )
        result = await session.exec(statement)
        return result.first()

    @classmethod
    async def upsert(
        cls,
        session: AsyncSession,
        embedding_in: EmbeddingCreate,
        vector: list[float],
        model_name: str,
    ) -> "Embedding":
        """Insert or update an embedding, skipping if content_hash is unchanged.

        Args:
            session: The async database session.
            embedding_in: The embedding creation data.
            vector: The embedding vector from the provider.
            model_name: The embedding model identifier (e.g. "openai:text-embedding-3-small").

        Returns:
            The created or updated Embedding record.
        """
        content_hash = cls.hash_content(embedding_in.chunk_text)

        existing = await cls.get_by_source(
            session,
            source_type=embedding_in.source_type,
            source_id=embedding_in.source_id,
            embedding_model=model_name,
            chunk_index=embedding_in.chunk_index,
        )

        if existing and existing.content_hash == content_hash:
            return existing

        if existing:
            existing.embedding = vector
            existing.content_hash = content_hash
            existing.chunk_text = embedding_in.chunk_text
            existing.metadata_ = embedding_in.extra_metadata  # pyright: ignore[reportAttributeAccessIssue]
            session.add(existing)
            await session.commit()
            await session.refresh(existing)
            return existing

        record = cls(
            source_type=embedding_in.source_type,
            source_id=embedding_in.source_id,
            embedding=vector,
            content_hash=content_hash,
            chunk_index=embedding_in.chunk_index,
            chunk_text=embedding_in.chunk_text,
            embedding_model=model_name,
            metadata_=embedding_in.extra_metadata,  # pyright: ignore[reportArgumentType]
        )
        session.add(record)
        await session.commit()
        await session.refresh(record)
        return record

    @classmethod
    async def search_similar(
        cls,
        session: AsyncSession,
        query_vector: list[float],
        source_type: str | None = None,
        limit: int = 5,
    ) -> list[SearchResult]:
        """Cosine similarity search using pgvector HNSW index.

        Args:
            session: The async database session.
            query_vector: The query embedding vector.
            source_type: Optional filter by source type.
            limit: Maximum number of results.

        Returns:
            A list of SearchResult ordered by similarity (highest first).
        """
        distance_col = cls.embedding.cosine_distance(query_vector).label(  # pyright: ignore[reportAttributeAccessIssue]
            "distance"
        )

        statement = (
            select(  # pyright: ignore[reportCallIssue]
                cls.source_type,
                cls.source_id,
                cls.chunk_text,
                (1 - distance_col).label("score"),
                cls.metadata_.label("metadata"),  # pyright: ignore[reportAttributeAccessIssue]
            )
            .order_by(distance_col)
            .limit(limit)
        )

        if source_type is not None:
            statement = statement.where(cls.source_type == source_type)

        result = await session.exec(statement)
        rows = result.all()

        return [
            SearchResult(
                source_type=row.source_type,
                source_id=row.source_id,
                chunk_text=row.chunk_text,
                score=float(row.score),
                metadata=row.metadata,
            )
            for row in rows
        ]

    @classmethod
    async def delete_by_source(
        cls,
        session: AsyncSession,
        source_type: str,
        source_id: _uuid.UUID,
    ) -> int:
        """Delete all embeddings for a given source.

        Args:
            session: The async database session.
            source_type: The type of source (e.g. "item").
            source_id: The UUID of the source record.

        Returns:
            The number of records deleted.
        """
        statement = select(cls).where(
            cls.source_type == source_type,
            cls.source_id == source_id,
        )
        result = await session.exec(statement)
        records = list(result.all())
        for record in records:
            await session.delete(record)
        if records:
            await session.commit()
        return len(records)

    @classmethod
    async def needs_update(
        cls,
        session: AsyncSession,
        source_type: str,
        source_id: _uuid.UUID,
        content: str,
        model: str,
    ) -> bool:
        """Check if content has changed since last embedding.

        Args:
            session: The async database session.
            source_type: The type of source.
            source_id: The UUID of the source record.
            content: The current content to compare.
            model: The embedding model name.

        Returns:
            True if the content needs re-embedding.
        """
        content_hash = cls.hash_content(content)
        statement = select(cls.content_hash).where(
            cls.source_type == source_type,
            cls.source_id == source_id,
            cls.chunk_index == 0,
            cls.embedding_model == model,
        )
        result = await session.exec(statement)
        existing_hash = result.first()
        return existing_hash != content_hash
