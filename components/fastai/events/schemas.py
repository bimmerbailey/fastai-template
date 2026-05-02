import uuid

from pydantic import BaseModel


class DocumentUploaded(BaseModel):
    """Event published when a document is uploaded and ready for processing."""

    document_id: uuid.UUID
    storage_path: str
    content_type: str
    filename: str


class DocumentDeleted(BaseModel):
    """Event published when a document is deleted."""

    document_id: uuid.UUID
    storage_path: str
