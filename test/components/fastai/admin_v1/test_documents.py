import uuid

import pytest
from httpx import AsyncClient

pytestmark = pytest.mark.integration

BASE_URL = "/documents"


def _make_document_payload(
    *,
    filename: str = "report.pdf",
    content_type: str = "application/pdf",
    file_size: int = 1024,
    storage_path: str = "uploads/2026/04/report.pdf",
    content_hash: str = "abc123def456",
) -> dict:
    return {
        "filename": filename,
        "content_type": content_type,
        "file_size": file_size,
        "storage_path": storage_path,
        "content_hash": content_hash,
    }


# ── CREATE ──


@pytest.mark.asyncio
async def test_create_document(admin_client: AsyncClient) -> None:
    payload = _make_document_payload()
    res = await admin_client.post(BASE_URL, json=payload)

    assert res.status_code == 201
    body = res.json()
    assert body["filename"] == "report.pdf"
    assert body["content_type"] == "application/pdf"
    assert body["file_size"] == 1024
    assert body["storage_path"] == "uploads/2026/04/report.pdf"
    assert body["content_hash"] == "abc123def456"
    assert "id" in body
    assert "created_at" in body
    assert "updated_at" in body


@pytest.mark.asyncio
async def test_create_document_duplicate_storage_path(
    admin_client: AsyncClient,
) -> None:
    payload = _make_document_payload(storage_path="uploads/dup.pdf")
    res1 = await admin_client.post(BASE_URL, json=payload)
    assert res1.status_code == 201

    res2 = await admin_client.post(BASE_URL, json=payload)
    assert res2.status_code == 409
    assert "already exists" in res2.json()["detail"]


# ── READ (single) ──


@pytest.mark.asyncio
async def test_get_document(admin_client: AsyncClient) -> None:
    create_res = await admin_client.post(BASE_URL, json=_make_document_payload())
    doc_id = create_res.json()["id"]

    res = await admin_client.get(f"{BASE_URL}/{doc_id}")

    assert res.status_code == 200
    assert res.json()["id"] == doc_id
    assert res.json()["filename"] == "report.pdf"


@pytest.mark.asyncio
async def test_get_document_not_found(admin_client: AsyncClient) -> None:
    fake_id = str(uuid.uuid4())
    res = await admin_client.get(f"{BASE_URL}/{fake_id}")
    assert res.status_code == 404


# ── READ (list) ──


@pytest.mark.asyncio
async def test_list_documents(admin_client: AsyncClient) -> None:
    await admin_client.post(
        BASE_URL, json=_make_document_payload(storage_path="uploads/a.pdf")
    )
    await admin_client.post(
        BASE_URL, json=_make_document_payload(storage_path="uploads/b.pdf")
    )

    res = await admin_client.get(BASE_URL)

    assert res.status_code == 200
    docs = res.json()
    assert len(docs) >= 2
    paths = {d["storage_path"] for d in docs}
    assert "uploads/a.pdf" in paths
    assert "uploads/b.pdf" in paths


@pytest.mark.asyncio
async def test_list_documents_pagination(admin_client: AsyncClient) -> None:
    for i in range(5):
        await admin_client.post(
            BASE_URL,
            json=_make_document_payload(storage_path=f"uploads/page{i}.pdf"),
        )

    res = await admin_client.get(BASE_URL, params={"offset": 0, "limit": 2})

    assert res.status_code == 200
    assert len(res.json()) == 2


# ── UPDATE ──


@pytest.mark.asyncio
async def test_update_document(admin_client: AsyncClient) -> None:
    create_res = await admin_client.post(BASE_URL, json=_make_document_payload())
    doc_id = create_res.json()["id"]

    res = await admin_client.patch(
        f"{BASE_URL}/{doc_id}",
        json={"filename": "updated.pdf", "file_size": 2048},
    )

    assert res.status_code == 200
    body = res.json()
    assert body["filename"] == "updated.pdf"
    assert body["file_size"] == 2048
    # Unchanged fields preserved
    assert body["content_type"] == "application/pdf"
    assert body["storage_path"] == "uploads/2026/04/report.pdf"


@pytest.mark.asyncio
async def test_update_document_storage_path_conflict(
    admin_client: AsyncClient,
) -> None:
    await admin_client.post(
        BASE_URL,
        json=_make_document_payload(storage_path="uploads/existing.pdf"),
    )
    create_res = await admin_client.post(
        BASE_URL,
        json=_make_document_payload(storage_path="uploads/other.pdf"),
    )
    doc_id = create_res.json()["id"]

    res = await admin_client.patch(
        f"{BASE_URL}/{doc_id}",
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
async def test_delete_document(admin_client: AsyncClient) -> None:
    create_res = await admin_client.post(BASE_URL, json=_make_document_payload())
    doc_id = create_res.json()["id"]

    res = await admin_client.delete(f"{BASE_URL}/{doc_id}")
    assert res.status_code == 204

    get_res = await admin_client.get(f"{BASE_URL}/{doc_id}")
    assert get_res.status_code == 404


@pytest.mark.asyncio
async def test_delete_document_not_found(admin_client: AsyncClient) -> None:
    fake_id = str(uuid.uuid4())
    res = await admin_client.delete(f"{BASE_URL}/{fake_id}")
    assert res.status_code == 404
