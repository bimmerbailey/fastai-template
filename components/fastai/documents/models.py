import uuid as _uuid
from typing import Optional

from sqlalchemy import CheckConstraint, Index, UniqueConstraint
from sqlmodel import Column, Field, String, func, select
from sqlmodel.ext.asyncio.session import AsyncSession

from fastai.documents.schemas import DocumentBase, DocumentCreate, DocumentUpdate
from fastai.utils.models import TimestampMixin

EXTRACTABLE_CONTENT_TYPES: set[str] = {
    "application/pdf",
    "text/html",
    "text/markdown",
    "text/plain",
}


class Document(DocumentBase, TimestampMixin, table=True):
    """Database table model for documents stored in S3/Minio."""

    __tablename__ = "documents"  # pyright: ignore[reportAssignmentType]
    __table_args__ = (
        CheckConstraint("file_size >= 0", name="ck_documents_file_size_nonneg"),
        UniqueConstraint("storage_path", name="uq_documents_storage_path"),
        Index("ix_documents_content_hash", "content_hash"),
        Index("ix_documents_embedding_status", "embedding_status"),
    )

    id: _uuid.UUID = Field(default_factory=_uuid.uuid4, primary_key=True)
    filename: str = Field(sa_column=Column(String, nullable=False))
    content_type: str = Field(sa_column=Column(String, nullable=False))
    file_size: int = Field(default=0)
    storage_path: str = Field(sa_column=Column(String, nullable=False, unique=True))
    content_hash: str = Field(sa_column=Column(String, nullable=False))
    embedding_status: str = Field(
        default="pending",
        sa_column=Column(String, nullable=False, server_default="pending"),
    )

    @staticmethod
    def is_extractable(content_type: str) -> bool:
        """Check if a content type is supported for text extraction."""
        return content_type in EXTRACTABLE_CONTENT_TYPES

    @classmethod
    async def create(cls, session: AsyncSession, doc_in: DocumentCreate) -> "Document":
        """Create a new document and persist it to the database."""
        doc = cls.model_validate(doc_in)
        session.add(doc)
        await session.commit()
        await session.refresh(doc)
        return doc

    @classmethod
    async def get(
        cls, session: AsyncSession, doc_id: _uuid.UUID
    ) -> "Optional[Document]":
        """Get a single document by ID. Returns None if not found."""
        return await session.get(cls, doc_id)

    @classmethod
    async def get_all(
        cls, session: AsyncSession, offset: int = 0, limit: int = 100
    ) -> "list[Document]":
        """Get a paginated list of documents."""
        statement = (
            select(cls)
            .order_by(cls.created_at.desc())  # pyright: ignore[reportAttributeAccessIssue]
            .offset(offset)
            .limit(limit)
        )
        results = await session.exec(statement)
        return list(results.all())

    async def update(self, session: AsyncSession, doc_in: DocumentUpdate) -> "Document":
        """Update this document with partial data."""
        update_data = doc_in.model_dump(exclude_unset=True)
        self.sqlmodel_update(update_data)
        session.add(self)
        await session.commit()
        await session.refresh(self)
        return self

    async def delete(self, session: AsyncSession) -> None:
        """Delete this document from the database."""
        await session.delete(self)
        await session.commit()

    async def update_embedding_status(
        self, session: AsyncSession, status: str
    ) -> "Document":
        """Update only the embedding_status field."""
        self.embedding_status = status
        session.add(self)
        await session.commit()
        await session.refresh(self)
        return self

    @classmethod
    async def get_all_by_embedding_status(
        cls,
        session: AsyncSession,
        embedding_status: str,
        offset: int = 0,
        limit: int = 100,
    ) -> "list[Document]":
        """Get documents filtered by embedding_status."""
        statement = (
            select(cls)
            .where(
                cls.embedding_status == embedding_status  # pyright: ignore[reportAttributeAccessIssue]
            )
            .order_by(cls.created_at.desc())  # pyright: ignore[reportAttributeAccessIssue]
            .offset(offset)
            .limit(limit)
        )
        results = await session.exec(statement)
        return list(results.all())

    @classmethod
    async def get_by_storage_path(
        cls, session: AsyncSession, storage_path: str
    ) -> "Optional[Document]":
        """Find a document by its S3 storage path."""
        statement = select(cls).where(
            cls.storage_path == storage_path  # pyright: ignore[reportAttributeAccessIssue]
        )
        results = await session.exec(statement)
        return results.first()

    @classmethod
    async def get_by_content_hash(
        cls, session: AsyncSession, content_hash: str
    ) -> "list[Document]":
        """Find all documents with a given content hash."""
        statement = select(cls).where(
            cls.content_hash == content_hash  # pyright: ignore[reportAttributeAccessIssue]
        )
        results = await session.exec(statement)
        return list(results.all())

    @classmethod
    async def count(cls, session: AsyncSession) -> int:
        """Get the total number of documents in the database."""
        statement = select(func.count()).select_from(cls)
        result = await session.exec(statement)
        return result.one()
