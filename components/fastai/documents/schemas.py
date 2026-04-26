import uuid
from typing import Optional

from pydantic import AwareDatetime
from sqlmodel import Field, SQLModel


class DocumentBase(SQLModel):
    """Shared document fields for API schemas. No database concerns."""

    filename: str
    content_type: str
    file_size: int = Field(ge=0)
    storage_path: str
    content_hash: str
    embedding_status: str = "pending"


class DocumentCreate(DocumentBase):
    """Schema for creating a new document. No id/timestamps."""

    pass


class DocumentRead(DocumentBase):
    """Schema for reading a document. Includes id and timestamps."""

    id: uuid.UUID
    created_at: AwareDatetime
    updated_at: AwareDatetime


class DocumentUpdate(SQLModel):
    """Schema for partially updating a document. All fields optional."""

    filename: Optional[str] = None
    content_type: Optional[str] = None
    file_size: Optional[int] = Field(default=None, ge=0)
    storage_path: Optional[str] = None
    content_hash: Optional[str] = None
    embedding_status: Optional[str] = None
