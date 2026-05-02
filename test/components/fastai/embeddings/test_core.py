import uuid

import pytest
from sqlmodel.ext.asyncio.session import AsyncSession

from fastai.embeddings.core import KnowledgeBase

integration = pytest.mark.integration


@integration
@pytest.mark.asyncio
async def test_embed_and_store_creates_embedding(
    test_db_session: AsyncSession,
    knowledge_base: KnowledgeBase,
) -> None:
    """embed_and_store creates a new embedding record."""
    source_id = uuid.uuid4()
    content = "Item: Test Widget\nDescription: A test item\nQuantity: 5"

    result = await knowledge_base.embed_and_store(
        test_db_session,
        source_type="item",
        source_id=source_id,
        content=content,
        metadata={"name": "Test Widget"},
    )

    assert result.source_type == "item"
    assert result.source_id == source_id
    assert result.chunk_text == content
    assert result.metadata_ == {"name": "Test Widget"}


@integration
@pytest.mark.asyncio
async def test_embed_and_store_skips_unchanged(
    test_db_session: AsyncSession,
    knowledge_base: KnowledgeBase,
) -> None:
    """embed_and_store skips the API call when content is unchanged."""
    source_id = uuid.uuid4()
    content = "Item: Stable Item\nQuantity: 10"

    # First call creates the embedding
    first = await knowledge_base.embed_and_store(
        test_db_session,
        source_type="item",
        source_id=source_id,
        content=content,
    )

    # Second call with same content should return existing record
    result = await knowledge_base.embed_and_store(
        test_db_session,
        source_type="item",
        source_id=source_id,
        content=content,
    )
    assert result.id == first.id
    assert result.chunk_text == content


@integration
@pytest.mark.asyncio
async def test_search_returns_results(
    test_db_session: AsyncSession,
    knowledge_base: KnowledgeBase,
) -> None:
    """search embeds the query and returns matching results."""
    # Store some embeddings
    items = [
        ("item1", "Item: Laptop\nDescription: High-performance laptop"),
        ("item2", "Item: Keyboard\nDescription: Mechanical keyboard"),
        ("item3", "Item: Monitor\nDescription: 4K display monitor"),
    ]
    for name, content in items:
        await knowledge_base.embed_and_store(
            test_db_session,
            source_type="item",
            source_id=uuid.uuid4(),
            content=content,
            metadata={"name": name},
        )

    # Search
    results = await knowledge_base.search(
        test_db_session,
        query="Item: Laptop\nDescription: High-performance laptop",
        source_type="item",
        limit=3,
    )

    assert len(results) == 3
    # First result should be most similar (exact match for our deterministic vectors)
    assert "Laptop" in results[0].chunk_text
    assert results[0].score >= results[1].score


@integration
@pytest.mark.asyncio
async def test_search_no_results(
    test_db_session: AsyncSession,
    knowledge_base: KnowledgeBase,
) -> None:
    """search returns empty list when no embeddings exist."""
    results = await knowledge_base.search(
        test_db_session,
        query="Find something",
        limit=5,
    )
    assert results == []
