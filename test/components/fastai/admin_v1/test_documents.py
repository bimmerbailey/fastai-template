import uuid

import pytest
from httpx import AsyncClient

from fastai.storage.core import StorageService

pytestmark = pytest.mark.integration

BASE_URL = "/documents"


def _make_upload_file(
    content: bytes = b"sample file content",
    filename: str = "report.pdf",
    content_type: str = "application/pdf",
) -> dict:
    return {"file": (filename, content, content_type)}


# ── CREATE ──


@pytest.mark.asyncio
async def test_create_document(
    admin_client: AsyncClient, storage: StorageService
) -> None:
    res = await admin_client.post(BASE_URL, files=_make_upload_file())

    assert res.status_code == 201
    body = res.json()
    assert body["filename"] == "report.pdf"
    assert body["content_type"] == "application/pdf"
    assert body["file_size"] == len(b"sample file content")
    assert body["storage_path"].startswith("documents/")
    assert body["content_hash"]  # ETag from S3
    assert "id" in body
    assert "created_at" in body
    assert "updated_at" in body


@pytest.mark.asyncio
async def test_create_document_with_filename_override(
    admin_client: AsyncClient, storage: StorageService
) -> None:
    res = await admin_client.post(
        BASE_URL,
        files=_make_upload_file(),
        data={"filename": "custom-name.pdf"},
    )

    assert res.status_code == 201
    assert res.json()["filename"] == "custom-name.pdf"


@pytest.mark.asyncio
async def test_create_document_s3_object_exists(
    admin_client: AsyncClient, storage: StorageService
) -> None:
    res = await admin_client.post(BASE_URL, files=_make_upload_file())
    assert res.status_code == 201

    storage_path = res.json()["storage_path"]
    assert await storage.object_exists(storage_path) is True


@pytest.mark.asyncio
async def test_create_two_identical_files_different_paths(
    admin_client: AsyncClient, storage: StorageService
) -> None:
    """Uploading the same file twice produces two documents with different storage paths but same content_hash."""
    res1 = await admin_client.post(BASE_URL, files=_make_upload_file())
    res2 = await admin_client.post(BASE_URL, files=_make_upload_file())

    assert res1.status_code == 201
    assert res2.status_code == 201
    assert res1.json()["storage_path"] != res2.json()["storage_path"]
    assert res1.json()["content_hash"] == res2.json()["content_hash"]


# ── READ (single) ──


@pytest.mark.asyncio
async def test_get_document(admin_client: AsyncClient, create_document_in_db) -> None:
    doc = await create_document_in_db()

    res = await admin_client.get(f"{BASE_URL}/{doc.id}")

    assert res.status_code == 200
    assert res.json()["id"] == str(doc.id)
    assert res.json()["filename"] == "report.pdf"


@pytest.mark.asyncio
async def test_get_document_not_found(admin_client: AsyncClient) -> None:
    fake_id = str(uuid.uuid4())
    res = await admin_client.get(f"{BASE_URL}/{fake_id}")
    assert res.status_code == 404


# ── READ (list) ──


@pytest.mark.asyncio
async def test_list_documents(admin_client: AsyncClient, create_document_in_db) -> None:
    await create_document_in_db(storage_path="uploads/a.pdf")
    await create_document_in_db(storage_path="uploads/b.pdf")

    res = await admin_client.get(BASE_URL)

    assert res.status_code == 200
    docs = res.json()
    assert len(docs) >= 2
    paths = {d["storage_path"] for d in docs}
    assert "uploads/a.pdf" in paths
    assert "uploads/b.pdf" in paths


@pytest.mark.asyncio
async def test_list_documents_pagination(
    admin_client: AsyncClient, create_document_in_db
) -> None:
    for i in range(5):
        await create_document_in_db(storage_path=f"uploads/page{i}.pdf")

    res = await admin_client.get(BASE_URL, params={"offset": 0, "limit": 2})

    assert res.status_code == 200
    assert len(res.json()) == 2


# ── UPDATE ──


@pytest.mark.asyncio
async def test_update_document(
    admin_client: AsyncClient, create_document_in_db
) -> None:
    doc = await create_document_in_db()

    res = await admin_client.patch(
        f"{BASE_URL}/{doc.id}",
        json={"filename": "updated.pdf", "file_size": 2048},
    )

    assert res.status_code == 200
    body = res.json()
    assert body["filename"] == "updated.pdf"
    assert body["file_size"] == 2048
    # Unchanged fields preserved
    assert body["content_type"] == "application/pdf"


@pytest.mark.asyncio
async def test_update_document_storage_path_conflict(
    admin_client: AsyncClient, create_document_in_db
) -> None:
    await create_document_in_db(storage_path="uploads/existing.pdf")
    doc = await create_document_in_db(storage_path="uploads/other.pdf")

    res = await admin_client.patch(
        f"{BASE_URL}/{doc.id}",
        json={"storage_path": "uploads/existing.pdf"},
    )

    assert res.status_code == 409


@pytest.mark.asyncio
async def test_update_document_not_found(admin_client: AsyncClient) -> None:
    fake_id = str(uuid.uuid4())
    res = await admin_client.patch(
        f"{BASE_URL}/{fake_id}",
        json={"filename": "ghost.pdf"},
    )
    assert res.status_code == 404


# ── DELETE ──


@pytest.mark.asyncio
async def test_delete_document(
    admin_client: AsyncClient, storage: StorageService
) -> None:
    create_res = await admin_client.post(BASE_URL, files=_make_upload_file())
    assert create_res.status_code == 201
    doc_id = create_res.json()["id"]
    storage_path = create_res.json()["storage_path"]

    res = await admin_client.delete(f"{BASE_URL}/{doc_id}")
    assert res.status_code == 204

    get_res = await admin_client.get(f"{BASE_URL}/{doc_id}")
    assert get_res.status_code == 404

    # S3 object should also be gone
    assert await storage.object_exists(storage_path) is False


@pytest.mark.asyncio
async def test_delete_document_not_found(admin_client: AsyncClient) -> None:
    fake_id = str(uuid.uuid4())
    res = await admin_client.delete(f"{BASE_URL}/{fake_id}")
    assert res.status_code == 404
