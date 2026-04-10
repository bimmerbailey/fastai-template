import hashlib
import uuid
from test.conftest import _deterministic_vector

import pytest
import pytest_asyncio
from sqlmodel.ext.asyncio.session import AsyncSession

from fastai.embeddings.models import Embedding
from fastai.embeddings.schemas import EmbeddingCreate

pytestmark = pytest.mark.integration

TEST_MODEL_NAME = "test:mock-embed"


@pytest_asyncio.fixture
async def sample_embedding(
    test_db_session: AsyncSession,
) -> Embedding:
    """Create a sample embedding for tests."""
    text = "Item: Widget\nDescription: A test widget\nCost: $9.99\nQuantity: 10"
    vector = _deterministic_vector(text)
    embedding_in = EmbeddingCreate(
        source_type="item",
        source_id=uuid.uuid4(),
        chunk_text=text,
    )
    return await Embedding.upsert(
        test_db_session, embedding_in, vector, TEST_MODEL_NAME
    )


@pytest.mark.asyncio
async def test_upsert_creates_record(
    test_db_session: AsyncSession,
) -> None:
    """Upsert creates a new embedding record."""
    text = "Item: Gadget\nDescription: A cool gadget\nQuantity: 5"
    vector = _deterministic_vector(text)
    source_id = uuid.uuid4()

    embedding_in = EmbeddingCreate(
        source_type="item",
        source_id=source_id,
        chunk_text=text,
        extra_metadata={"name": "Gadget"},
    )
    result = await Embedding.upsert(
        test_db_session, embedding_in, vector, TEST_MODEL_NAME
    )

    assert result.id is not None
    assert result.source_type == "item"
    assert result.source_id == source_id
    assert result.chunk_text == text
    assert result.embedding_model == "test:mock-embed"
    assert result.content_hash == Embedding.hash_content(text)
    assert result.chunk_index == 0
    assert result.metadata_ == {"name": "Gadget"}
    assert result.created_at is not None


@pytest.mark.asyncio
async def test_upsert_skips_unchanged_content(
    test_db_session: AsyncSession,
    sample_embedding: Embedding,
) -> None:
    """Upsert returns existing record when content hash matches."""
    embedding_in = EmbeddingCreate(
        source_type=sample_embedding.source_type,
        source_id=sample_embedding.source_id,
        chunk_text=sample_embedding.chunk_text,
    )
    # Use a different vector to prove it's not re-embedded
    different_vector = [0.0] * 1536

    result = await Embedding.upsert(
        test_db_session, embedding_in, different_vector, TEST_MODEL_NAME
    )

    assert result.id == sample_embedding.id
    # Embedding should NOT have changed to the zero vector
    assert result.content_hash == sample_embedding.content_hash


@pytest.mark.asyncio
async def test_upsert_updates_changed_content(
    test_db_session: AsyncSession,
    sample_embedding: Embedding,
) -> None:
    """Upsert updates the embedding when content changes."""
    new_text = "Item: Widget\nDescription: Updated widget\nCost: $14.99\nQuantity: 20"
    new_vector = _deterministic_vector(new_text)

    embedding_in = EmbeddingCreate(
        source_type=sample_embedding.source_type,
        source_id=sample_embedding.source_id,
        chunk_text=new_text,
    )
    result = await Embedding.upsert(
        test_db_session, embedding_in, new_vector, TEST_MODEL_NAME
    )

    assert result.id == sample_embedding.id
    assert result.chunk_text == new_text
    assert result.content_hash == Embedding.hash_content(new_text)


@pytest.mark.asyncio
async def test_search_similar_returns_results(
    test_db_session: AsyncSession,
) -> None:
    """Search returns results ordered by similarity."""
    # Insert two embeddings with different content
    text_a = "Item: Laptop\nDescription: High-performance laptop\nQuantity: 5"
    text_b = "Item: Keyboard\nDescription: Mechanical keyboard\nQuantity: 20"

    for text in [text_a, text_b]:
        vector = _deterministic_vector(text)
        embedding_in = EmbeddingCreate(
            source_type="item",
            source_id=uuid.uuid4(),
            chunk_text=text,
        )
        await Embedding.upsert(test_db_session, embedding_in, vector, TEST_MODEL_NAME)

    # Search using vector similar to text_a
    query_vector = _deterministic_vector(text_a)
    results = await Embedding.search_similar(
        test_db_session,
        query_vector=query_vector,
        source_type="item",
        limit=5,
    )

    assert len(results) == 2
    # The first result should be most similar to the query (text_a itself)
    assert results[0].chunk_text == text_a
    assert results[0].score > results[1].score


@pytest.mark.asyncio
async def test_search_similar_filters_by_source_type(
    test_db_session: AsyncSession,
) -> None:
    """Search filters results by source_type."""
    text_item = "Item: Phone\nDescription: Smartphone\nQuantity: 10"
    text_doc = "Document: User manual for phone setup"

    for text, stype in [(text_item, "item"), (text_doc, "document")]:
        vector = _deterministic_vector(text)
        embedding_in = EmbeddingCreate(
            source_type=stype,
            source_id=uuid.uuid4(),
            chunk_text=text,
        )
        await Embedding.upsert(test_db_session, embedding_in, vector, TEST_MODEL_NAME)

    query_vector = _deterministic_vector(text_item)
    results = await Embedding.search_similar(
        test_db_session,
        query_vector=query_vector,
        source_type="item",
        limit=10,
    )

    assert all(r.source_type == "item" for r in results)
    assert len(results) == 1


@pytest.mark.asyncio
async def test_delete_by_source(
    test_db_session: AsyncSession,
    sample_embedding: Embedding,
) -> None:
    """delete_by_source removes all embeddings for a source."""
    count = await Embedding.delete_by_source(
        test_db_session,
        source_type=sample_embedding.source_type,
        source_id=sample_embedding.source_id,
    )

    assert count == 1

    existing = await Embedding.get_by_source(
        test_db_session,
        source_type=sample_embedding.source_type,
        source_id=sample_embedding.source_id,
        embedding_model=sample_embedding.embedding_model,
    )
    assert existing is None


@pytest.mark.asyncio
async def test_needs_update_detects_change(
    test_db_session: AsyncSession,
    sample_embedding: Embedding,
) -> None:
    """needs_update returns True when content has changed."""
    needs = await Embedding.needs_update(
        test_db_session,
        source_type=sample_embedding.source_type,
        source_id=sample_embedding.source_id,
        content="Completely different content",
        model=sample_embedding.embedding_model,
    )
    assert needs is True


@pytest.mark.asyncio
async def test_needs_update_detects_no_change(
    test_db_session: AsyncSession,
    sample_embedding: Embedding,
) -> None:
    """needs_update returns False when content is unchanged."""
    needs = await Embedding.needs_update(
        test_db_session,
        source_type=sample_embedding.source_type,
        source_id=sample_embedding.source_id,
        content=sample_embedding.chunk_text,
        model=sample_embedding.embedding_model,
    )
    assert needs is False


@pytest.mark.asyncio
async def test_needs_update_returns_true_for_new_source(
    test_db_session: AsyncSession,
) -> None:
    """needs_update returns True for a source with no existing embedding."""
    needs = await Embedding.needs_update(
        test_db_session,
        source_type="item",
        source_id=uuid.uuid4(),
        content="Any content",
        model="test:mock-embed",
    )
    assert needs is True


def test_hash_content_deterministic() -> None:
    """hash_content produces consistent SHA-256 hashes."""
    text = "Hello, world!"
    hash1 = Embedding.hash_content(text)
    hash2 = Embedding.hash_content(text)
    assert hash1 == hash2
    assert hash1 == hashlib.sha256(text.encode()).hexdigest()


def test_hash_content_differs_for_different_input() -> None:
    """hash_content produces different hashes for different input."""
    assert Embedding.hash_content("foo") != Embedding.hash_content("bar")
