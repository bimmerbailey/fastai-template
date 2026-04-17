import uuid

from fastapi import APIRouter, HTTPException, Query, status

from fastai.documents.models import Document
from fastai.documents.schemas import DocumentCreate, DocumentRead, DocumentUpdate
from fastai.utils.dependencies import SessionDep

router = APIRouter(prefix="/documents", tags=["Documents"])


@router.get("", response_model=list[DocumentRead])
async def list_documents(
    session: SessionDep,
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=1000),
) -> list[Document]:
    """List all documents with pagination."""
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


@router.post("", response_model=DocumentRead, status_code=status.HTTP_201_CREATED)
async def create_document(session: SessionDep, doc_in: DocumentCreate) -> Document:
    """Create a new document."""
    existing = await Document.get_by_storage_path(session, doc_in.storage_path)
    if existing is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A document with this storage path already exists",
        )
    return await Document.create(session, doc_in)


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
async def delete_document(session: SessionDep, document_id: uuid.UUID) -> None:
    """Delete a document."""
    doc = await Document.get(session, document_id)
    if doc is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found",
        )
    await doc.delete(session)
