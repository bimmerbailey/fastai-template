import uuid

import pytest
import pytest_asyncio
from sqlmodel.ext.asyncio.session import AsyncSession

from fastai.documents.models import Document
from fastai.documents.schemas import DocumentCreate, DocumentUpdate

pytestmark = pytest.mark.integration


@pytest_asyncio.fixture
async def sample_document(test_db_session: AsyncSession) -> Document:
    """Create a sample document for tests that need an existing record."""
    doc_in = DocumentCreate(
        filename="report.pdf",
        content_type="application/pdf",
        file_size=1024,
        storage_path="documents/2026/04/report.pdf",
        content_hash="abc123def456",
    )
    return await Document.create(test_db_session, doc_in)


@pytest.mark.asyncio
async def test_create_document(test_db_session: AsyncSession) -> None:
    doc_in = DocumentCreate(
        filename="notes.txt",
        content_type="text/plain",
        file_size=256,
        storage_path="documents/notes.txt",
        content_hash="sha256hexdigest",
    )

    doc = await Document.create(test_db_session, doc_in)

    assert doc.id is not None
    assert doc.filename == "notes.txt"
    assert doc.content_type == "text/plain"
    assert doc.file_size == 256
    assert doc.storage_path == "documents/notes.txt"
    assert doc.content_hash == "sha256hexdigest"
    assert doc.created_at is not None
    assert doc.updated_at is not None


@pytest.mark.asyncio
async def test_get_document(
    test_db_session: AsyncSession, sample_document: Document
) -> None:
    assert sample_document.id is not None
    fetched = await Document.get(test_db_session, sample_document.id)

    assert fetched is not None
    assert fetched.id == sample_document.id
    assert fetched.filename == sample_document.filename


@pytest.mark.asyncio
async def test_get_document_not_found(test_db_session: AsyncSession) -> None:
    fetched = await Document.get(test_db_session, uuid.uuid4())

    assert fetched is None


@pytest.mark.asyncio
async def test_get_all_documents(
    test_db_session: AsyncSession, sample_document: Document
) -> None:
    second = await Document.create(
        test_db_session,
        DocumentCreate(
            filename="second.pdf",
            content_type="application/pdf",
            file_size=2048,
            storage_path="documents/second.pdf",
            content_hash="hash2",
        ),
    )

    docs = await Document.get_all(test_db_session)

    assert len(docs) >= 2
    doc_ids = [d.id for d in docs]
    assert sample_document.id in doc_ids
    assert second.id in doc_ids


@pytest.mark.asyncio
async def test_get_all_documents_pagination(
    test_db_session: AsyncSession,
) -> None:
    for i in range(5):
        await Document.create(
            test_db_session,
            DocumentCreate(
                filename=f"file_{i}.txt",
                content_type="text/plain",
                file_size=100 + i,
                storage_path=f"documents/file_{i}.txt",
                content_hash=f"hash_{i}",
            ),
        )

    page = await Document.get_all(test_db_session, offset=2, limit=2)

    assert len(page) == 2


@pytest.mark.asyncio
async def test_update_document(
    test_db_session: AsyncSession, sample_document: Document
) -> None:
    update_in = DocumentUpdate(
        filename="updated_report.pdf",
        content_hash="newhash789",
    )

    updated = await sample_document.update(test_db_session, update_in)

    assert updated.id == sample_document.id
    assert updated.filename == "updated_report.pdf"
    assert updated.content_hash == "newhash789"
    # Unset fields should remain unchanged
    assert updated.content_type == sample_document.content_type
    assert updated.file_size == sample_document.file_size
    assert updated.storage_path == sample_document.storage_path


@pytest.mark.asyncio
async def test_delete_document(
    test_db_session: AsyncSession, sample_document: Document
) -> None:
    assert sample_document.id is not None
    doc_id = sample_document.id

    await sample_document.delete(test_db_session)

    fetched = await Document.get(test_db_session, doc_id)
    assert fetched is None


@pytest.mark.asyncio
async def test_get_by_storage_path(
    test_db_session: AsyncSession, sample_document: Document
) -> None:
    fetched = await Document.get_by_storage_path(
        test_db_session, "documents/2026/04/report.pdf"
    )

    assert fetched is not None
    assert fetched.id == sample_document.id


@pytest.mark.asyncio
async def test_get_by_storage_path_not_found(
    test_db_session: AsyncSession,
) -> None:
    fetched = await Document.get_by_storage_path(
        test_db_session, "nonexistent/path.pdf"
    )

    assert fetched is None


@pytest.mark.asyncio
async def test_get_by_content_hash(
    test_db_session: AsyncSession, sample_document: Document
) -> None:
    docs = await Document.get_by_content_hash(test_db_session, "abc123def456")

    assert len(docs) == 1
    assert docs[0].id == sample_document.id


@pytest.mark.asyncio
async def test_count(test_db_session: AsyncSession, sample_document: Document) -> None:
    count = await Document.count(test_db_session)

    assert count >= 1
