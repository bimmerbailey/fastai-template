import uuid

import structlog.stdlib
from fastapi import APIRouter, Form, HTTPException, Query, UploadFile, status

from fastai.admin_v1.dependencies import EventPublisherDep, StorageServiceDep
from fastai.documents.models import Document
from fastai.documents.schemas import DocumentCreate, DocumentRead, DocumentUpdate
from fastai.embeddings.models import Embedding
from fastai.embeddings.schemas import EmbeddingRead
from fastai.events.schemas import DocumentUploaded
from fastai.utils.dependencies import SessionDep

logger = structlog.stdlib.get_logger(__name__)

router = APIRouter(prefix="/documents", tags=["Documents"])


# TODO: Look into model for all query params
@router.get("", response_model=list[DocumentRead])
async def list_documents(
    session: SessionDep,
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=1000),
    embedding_status: str | None = Query(default=None),
) -> list[Document]:
    """List all documents with pagination, optionally filtered by embedding status."""
    if embedding_status:
        return await Document.get_all_by_embedding_status(
            session, embedding_status, offset=offset, limit=limit
        )
    return await Document.get_all(session, offset=offset, limit=limit)


@router.get("/{document_id}", response_model=DocumentRead)
async def get_document(session: SessionDep, document_id: uuid.UUID) -> Document:
    """Get a single document by ID."""
    doc = await Document.get(session, document_id)
    if doc is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found",
        )
    return doc


@router.get("/{document_id}/chunks", response_model=list[EmbeddingRead])
async def list_document_chunks(
    session: SessionDep,
    document_id: uuid.UUID,
) -> list[Embedding]:
    """List all embedding chunks for a document, ordered by chunk_index."""
    doc = await Document.get(session, document_id)
    if doc is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found",
        )
    return await Embedding.get_chunks_by_source(session, "document", document_id)


@router.post("", response_model=DocumentRead, status_code=status.HTTP_201_CREATED)
async def create_document(
    session: SessionDep,
    storage: StorageServiceDep,
    publisher: EventPublisherDep,
    file: UploadFile,
    filename: str | None = Form(None),
) -> Document:
    """Upload a file to storage and create a document record."""
    resolved_filename = filename or file.filename or "unnamed"
    content_type = file.content_type or "application/octet-stream"
    data = await file.read()
    file_size = len(data)
    storage_path = f"documents/{uuid.uuid4()}/{resolved_filename}"

    etag = await storage.upload_bytes(data, storage_path, content_type=content_type)

    doc_in = DocumentCreate(
        filename=resolved_filename,
        content_type=content_type,
        file_size=file_size,
        storage_path=storage_path,
        content_hash=etag,
        embedding_status="pending",
    )
    try:
        doc = await Document.create(session, doc_in)
    except Exception:
        try:
            await storage.delete_object(storage_path)
        except Exception:
            logger.warning(
                "Failed to clean up S3 object after DB error",
                storage_path=storage_path,
            )
        raise

    # Publish event for async processing (best-effort)
    try:
        await publisher.publish_document_uploaded(
            DocumentUploaded(
                document_id=doc.id,
                storage_path=doc.storage_path,
                content_type=doc.content_type,
                filename=doc.filename,
            )
        )
    except Exception:
        logger.warning(
            "Failed to publish document.uploaded event",
            document_id=str(doc.id),
            exc_info=True,
        )

    return doc


@router.patch("/{document_id}", response_model=DocumentRead)
async def update_document(
    session: SessionDep,
    document_id: uuid.UUID,
    doc_in: DocumentUpdate,
) -> Document:
    """Partially update a document."""
    doc = await Document.get(session, document_id)
    if doc is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found",
        )

    if doc_in.storage_path is not None and doc_in.storage_path != doc.storage_path:
        existing = await Document.get_by_storage_path(session, doc_in.storage_path)
        if existing is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="A document with this storage path already exists",
            )

    return await doc.update(session, doc_in)


@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document(
    session: SessionDep,
    storage: StorageServiceDep,
    publisher: EventPublisherDep,
    document_id: uuid.UUID,
) -> None:
    """Delete a document, its stored file, and its embeddings."""
    doc = await Document.get(session, document_id)
    if doc is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found",
        )
    storage_path = doc.storage_path

    # Delete embeddings first
    deleted_count = await Embedding.delete_by_source(session, "document", doc.id)
    if deleted_count > 0:
        logger.info(
            "Deleted document embeddings",
            document_id=str(doc.id),
            count=deleted_count,
        )

    await doc.delete(session)
    try:
        await storage.delete_object(storage_path)
    except Exception:
        logger.warning(
            "Failed to delete S3 object after DB deletion",
            storage_path=storage_path,
        )


@router.post(
    "/{document_id}/reprocess",
    response_model=DocumentRead,
)
async def reprocess_document(
    session: SessionDep,
    publisher: EventPublisherDep,
    document_id: uuid.UUID,
) -> Document:
    """Re-process a document: delete existing embeddings and re-extract.

    Resets the embedding status to "pending" and publishes a new
    DocumentUploaded event so the worker re-extracts the document.
    """
    doc = await Document.get(session, document_id)
    if doc is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found",
        )

    # Clear existing embeddings
    deleted_count = await Embedding.delete_by_source(session, "document", doc.id)
    if deleted_count > 0:
        logger.info(
            "Deleted existing embeddings for reprocessing",
            document_id=str(doc.id),
            count=deleted_count,
        )

    await doc.update_embedding_status(session, "pending")

    try:
        await publisher.publish_document_uploaded(
            DocumentUploaded(
                document_id=doc.id,
                storage_path=doc.storage_path,
                content_type=doc.content_type,
                filename=doc.filename,
            )
        )
    except Exception:
        logger.warning(
            "Failed to publish document.uploaded event for reprocessing",
            document_id=str(doc.id),
            exc_info=True,
        )

    return doc
