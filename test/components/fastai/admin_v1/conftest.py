import uuid
from typing import AsyncGenerator

import pytest
import pytest_asyncio
from fastapi import FastAPI
from fastapi.testclient import TestClient
from httpx import ASGITransport, AsyncClient

from fastai.admin_v1.core import init_admin_v1_app
from fastai.database.core import PostgresSettings
from fastai.documents.models import Document
from fastai.documents.schemas import DocumentCreate
from fastai.storage.core import StorageSettings


@pytest_asyncio.fixture
async def app(
    test_db_settings: PostgresSettings,
    test_db_engine,
    storage_settings: StorageSettings,
) -> AsyncGenerator[FastAPI, None]:
    """Create FastAPI test application with storage configured."""
    application = init_admin_v1_app(test_db_engine, storage_settings=storage_settings)
    yield application


@pytest.fixture
def client(app: FastAPI) -> TestClient:
    """Create synchronous test client."""
    return TestClient(app)


@pytest_asyncio.fixture
async def admin_client(app: FastAPI) -> AsyncGenerator[AsyncClient, None]:
    """Create asynchronous test client."""
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://testserver"
    ) as ac:
        yield ac


@pytest_asyncio.fixture
async def create_document_in_db(test_db_session):
    """Insert a document directly into the DB (no S3 interaction)."""

    async def _create(
        *,
        filename: str = "report.pdf",
        content_type: str = "application/pdf",
        file_size: int = 1024,
        storage_path: str | None = None,
        content_hash: str = "abc123def456",
    ) -> Document:
        storage_path = storage_path or f"documents/{uuid.uuid4()}/report.pdf"
        doc_in = DocumentCreate(
            filename=filename,
            content_type=content_type,
            file_size=file_size,
            storage_path=storage_path,
            content_hash=content_hash,
        )
        return await Document.create(test_db_session, doc_in)

    return _create
