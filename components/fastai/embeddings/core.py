import uuid
from decimal import Decimal

import structlog.stdlib
from pydantic_ai.embeddings import Embedder
from sqlmodel.ext.asyncio.session import AsyncSession

from fastai.embeddings.exceptions import EmbeddingNotFoundError
from fastai.embeddings.models import Embedding
from fastai.embeddings.schemas import EmbeddingCreate, SearchResult
from fastai.embeddings.settings import EmbeddingSettings

logger = structlog.stdlib.get_logger(__name__)


def _embedder_model_name(embedder: Embedder) -> str:
    """Derive a 'provider:model' identifier from an Embedder instance."""
    model = embedder.model
    if isinstance(model, str):
        return model
    return f"{model.system}:{model.model_name}"


class KnowledgeBase:
    """Encapsulates embedding storage and semantic search over documents."""

    def __init__(
        self,
        embedder: Embedder,
        settings: EmbeddingSettings | None = None,
    ) -> None:
        self.embedder = embedder
        self.settings = settings or EmbeddingSettings()

    async def embed_and_store(
        self,
        session: AsyncSession,
        source_type: str,
        source_id: uuid.UUID,
        content: str,
        metadata: dict | None = None,
    ) -> Embedding:
        """Embed content and store it. Skips the API call if content is unchanged.

        Args:
            session: The async database session.
            source_type: The type of source (e.g. "item").
            source_id: The UUID of the source record.
            content: The text content to embed.
            metadata: Optional metadata dict to store alongside the embedding.

        Returns:
            The created or existing Embedding record.
        """
        model_name = _embedder_model_name(self.embedder)

        if not await Embedding.needs_update(
            session, source_type, source_id, content, model_name
        ):
            logger.debug(
                "Content unchanged, skipping embedding",
                source_type=source_type,
                source_id=str(source_id),
            )
            existing = await Embedding.get_by_source(
                session, source_type, source_id, model_name
            )
            if existing is None:
                raise EmbeddingNotFoundError(
                    f"Embedding for {source_type}:{source_id} vanished between "
                    "needs_update check and get_by_source lookup"
                )
            return existing

        result = await self.embedder.embed_documents(content)
        vector = list(result.embeddings[0])

        embedding_in = EmbeddingCreate(
            source_type=source_type,
            source_id=source_id,
            chunk_text=content,
            extra_metadata=metadata or {},
        )
        record = await Embedding.upsert(session, embedding_in, vector, model_name)

        logger.info(
            "Embedding stored",
            source_type=source_type,
            source_id=str(source_id),
            model=model_name,
        )
        return record

    async def search(
        self,
        session: AsyncSession,
        query: str,
        source_type: str | None = None,
        limit: int = 5,
    ) -> list[SearchResult]:
        """Embed a query and search for semantically similar content.

        Args:
            session: The async database session.
            query: Natural language search query.
            source_type: Optional filter by source type (e.g. "item").
            limit: Maximum number of results.

        Returns:
            A list of SearchResult ordered by similarity.
        """
        result = await self.embedder.embed_query(query)
        query_vector = list(result.embeddings[0])

        results = await Embedding.search_similar(
            session,
            query_vector=query_vector,
            source_type=source_type,
            limit=limit,
        )

        logger.info(
            "Semantic search completed",
            query_length=len(query),
            source_type=source_type,
            results_count=len(results),
        )
        return results


def build_item_text(
    name: str,
    description: str | None = None,
    cost: Decimal | None = None,
    quantity: int = 0,
) -> str:
    """Build embeddable text from item fields, enriched with metadata labels.

    Field labels give the embedding model semantic anchors, improving
    retrieval quality for short content.

    Args:
        name: The item name.
        description: Optional item description.
        cost: Optional item cost (Decimal or similar).
        quantity: Item quantity.

    Returns:
        A metadata-enriched text string for embedding.
    """
    parts = [f"Item: {name}"]
    if description:
        parts.append(f"Description: {description}")
    if cost is not None:
        parts.append(f"Cost: ${cost}")
    parts.append(f"Quantity: {quantity}")
    return "\n".join(parts)
