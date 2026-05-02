import uuid

import pytest
import pytest_asyncio
from faststream.nats import NatsBroker, TestNatsBroker
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from fastai.documents.models import Document
from fastai.documents.schemas import DocumentCreate
from fastai.embeddings.models import Embedding
from fastai.events import SUBJECT_DOCUMENT_UPLOADED
from fastai.events.schemas import DocumentUploaded
from fastai.storage.core import StorageService

pytestmark = pytest.mark.integration


@pytest_asyncio.fixture
async def uploaded_document(
    test_db_session: AsyncSession,
    storage: StorageService,
) -> Document:
    """Create a document in DB and upload a markdown file to S3."""
    storage_path = f"documents/{uuid.uuid4()}/test.md"
    content = (
        b"# Test Document\n\nThis is a test document with some text for embedding."
    )
    await storage.upload_bytes(content, storage_path, content_type="text/markdown")

    doc_in = DocumentCreate(
        filename="test.md",
        content_type="text/markdown",
        file_size=len(content),
        storage_path=storage_path,
        content_hash="testhash",
        embedding_status="pending",
    )
    return await Document.create(test_db_session, doc_in)


@pytest_asyncio.fixture
async def unsupported_document(
    test_db_session: AsyncSession,
    storage: StorageService,
) -> Document:
    """Create a document with unsupported content type."""
    storage_path = f"documents/{uuid.uuid4()}/test.zip"
    content = b"PK\x03\x04fake-zip-content"
    await storage.upload_bytes(content, storage_path, content_type="application/zip")

    doc_in = DocumentCreate(
        filename="test.zip",
        content_type="application/zip",
        file_size=len(content),
        storage_path=storage_path,
        content_hash="ziphash",
        embedding_status="pending",
    )
    return await Document.create(test_db_session, doc_in)


def _set_broker_context(
    broker: NatsBroker,
    test_db_engine,
    storage_settings,
    knowledge_base,
    extraction_service,
) -> None:
    """Populate the broker's ContextRepo with test dependencies."""
    broker.context.set_global("db_engine", test_db_engine)
    broker.context.set_global("storage_settings", storage_settings)
    broker.context.set_global("knowledge_base", knowledge_base)
    broker.context.set_global("extraction_service", extraction_service)


@pytest.mark.asyncio
async def test_process_document_creates_embeddings(
    test_db_engine,
    uploaded_document: Document,
    knowledge_base,
    storage_settings,
    extraction_service,
    storage: StorageService,
) -> None:
    """The subscriber processes a document and creates embeddings."""
    from fastai.subscribers_v1.documents import router

    # Capture IDs eagerly before the subscriber modifies the DB
    doc_id = uploaded_document.id
    doc_storage_path = uploaded_document.storage_path

    broker = NatsBroker()
    broker.include_router(router)
    _set_broker_context(
        broker, test_db_engine, storage_settings, knowledge_base, extraction_service
    )

    event = DocumentUploaded(
        document_id=doc_id,
        storage_path=doc_storage_path,
        content_type="text/markdown",
        filename="test.md",
    )

    async with TestNatsBroker(broker) as br:
        await br.publish(event, subject=SUBJECT_DOCUMENT_UPLOADED)

    # Verify using a fresh session (subscriber committed via its own sessions)
    async with AsyncSession(test_db_engine) as session:
        doc = await Document.get(session, doc_id)
        assert doc is not None
        assert doc.embedding_status == "completed"

        # Verify embeddings were created
        stmt = select(Embedding).where(
            Embedding.source_type == "document",
            Embedding.source_id == doc_id,
        )
        result = await session.exec(stmt)
        embeddings = list(result.all())
        assert len(embeddings) >= 1


@pytest.mark.asyncio
async def test_process_unsupported_content_type_skips(
    test_db_engine,
    unsupported_document: Document,
    knowledge_base,
    storage_settings,
    extraction_service,
    storage: StorageService,
) -> None:
    """Unsupported content types result in 'skipped' status."""
    from fastai.subscribers_v1.documents import router

    # Capture IDs eagerly
    doc_id = unsupported_document.id
    doc_storage_path = unsupported_document.storage_path

    broker = NatsBroker()
    broker.include_router(router)
    _set_broker_context(
        broker, test_db_engine, storage_settings, knowledge_base, extraction_service
    )

    event = DocumentUploaded(
        document_id=doc_id,
        storage_path=doc_storage_path,
        content_type="application/zip",
        filename="test.zip",
    )

    async with TestNatsBroker(broker) as br:
        await br.publish(event, subject=SUBJECT_DOCUMENT_UPLOADED)

    # Verify using a fresh session
    async with AsyncSession(test_db_engine) as session:
        doc = await Document.get(session, doc_id)
        assert doc is not None
        assert doc.embedding_status == "skipped"


@pytest.mark.asyncio
async def test_process_missing_document_does_not_error(
    test_db_engine,
    knowledge_base,
    storage_settings,
    extraction_service,
    storage: StorageService,
) -> None:
    """Processing a non-existent document ID does not raise."""
    from fastai.subscribers_v1.documents import router

    broker = NatsBroker()
    broker.include_router(router)
    _set_broker_context(
        broker, test_db_engine, storage_settings, knowledge_base, extraction_service
    )

    event = DocumentUploaded(
        document_id=uuid.uuid4(),
        storage_path="documents/nonexistent/file.txt",
        content_type="text/plain",
        filename="file.txt",
    )

    # Should not raise
    async with TestNatsBroker(broker) as br:
        await br.publish(event, subject=SUBJECT_DOCUMENT_UPLOADED)
