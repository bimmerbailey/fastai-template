import uuid

import pytest
from httpx import AsyncClient

pytestmark = pytest.mark.integration

BASE_URL = "/users"


def _make_user_payload(
    *,
    email: str = "john@example.com",
    password: str = "securepassword123",
    first_name: str | None = "John",
    last_name: str | None = "Smith",
) -> dict:
    payload: dict = {"email": email, "password": password}
    if first_name is not None:
        payload["first_name"] = first_name
    if last_name is not None:
        payload["last_name"] = last_name
    return payload


# ── CREATE ──


@pytest.mark.asyncio
async def test_create_user(admin_client: AsyncClient) -> None:
    payload = _make_user_payload()
    res = await admin_client.post(BASE_URL, json=payload)

    assert res.status_code == 201
    body = res.json()
    assert body["email"] == "john@example.com"
    assert body["first_name"] == "John"
    assert body["last_name"] == "Smith"
    assert body["is_admin"] is False
    assert body["status"] == "pending_verification"
    assert body["is_active"] is True
    assert body["is_email_verified"] is False
    assert "id" in body
    # Password should never be in the response
    assert "password" not in body
    assert "password_hash" not in body


@pytest.mark.asyncio
async def test_create_user_duplicate_email(admin_client: AsyncClient) -> None:
    payload = _make_user_payload(email="dup@example.com")
    res1 = await admin_client.post(BASE_URL, json=payload)
    assert res1.status_code == 201

    res2 = await admin_client.post(BASE_URL, json=payload)
    assert res2.status_code == 409
    assert "already exists" in res2.json()["detail"]


@pytest.mark.asyncio
async def test_create_user_invalid_password(admin_client: AsyncClient) -> None:
    payload = _make_user_payload(password="short")
    res = await admin_client.post(BASE_URL, json=payload)
    assert res.status_code == 422


@pytest.mark.asyncio
async def test_create_user_minimal(admin_client: AsyncClient) -> None:
    """Only email and password are required."""
    payload = {"email": "minimal@example.com", "password": "securepassword123"}
    res = await admin_client.post(BASE_URL, json=payload)

    assert res.status_code == 201
    body = res.json()
    assert body["first_name"] is None
    assert body["last_name"] is None


# ── READ (single) ──


@pytest.mark.asyncio
async def test_get_user(admin_client: AsyncClient) -> None:
    create_res = await admin_client.post(BASE_URL, json=_make_user_payload())
    user_id = create_res.json()["id"]

    res = await admin_client.get(f"{BASE_URL}/{user_id}")

    assert res.status_code == 200
    assert res.json()["id"] == user_id
    assert res.json()["email"] == "john@example.com"


@pytest.mark.asyncio
async def test_get_user_not_found(admin_client: AsyncClient) -> None:
    fake_id = str(uuid.uuid4())
    res = await admin_client.get(f"{BASE_URL}/{fake_id}")
    assert res.status_code == 404


# ── READ (list) ──


@pytest.mark.asyncio
async def test_list_users(admin_client: AsyncClient) -> None:
    await admin_client.post(BASE_URL, json=_make_user_payload(email="a@example.com"))
    await admin_client.post(BASE_URL, json=_make_user_payload(email="b@example.com"))

    res = await admin_client.get(BASE_URL)

    assert res.status_code == 200
    users = res.json()
    assert len(users) >= 2
    emails = {u["email"] for u in users}
    assert "a@example.com" in emails
    assert "b@example.com" in emails


@pytest.mark.asyncio
async def test_list_users_pagination(admin_client: AsyncClient) -> None:
    for i in range(5):
        await admin_client.post(
            BASE_URL,
            json=_make_user_payload(email=f"page{i}@example.com"),
        )

    res = await admin_client.get(BASE_URL, params={"offset": 0, "limit": 2})

    assert res.status_code == 200
    assert len(res.json()) == 2


# ── UPDATE ──


@pytest.mark.asyncio
async def test_update_user(admin_client: AsyncClient) -> None:
    create_res = await admin_client.post(BASE_URL, json=_make_user_payload())
    user_id = create_res.json()["id"]

    res = await admin_client.patch(
        f"{BASE_URL}/{user_id}",
        json={"first_name": "Jane", "is_admin": True},
    )

    assert res.status_code == 200
    body = res.json()
    assert body["first_name"] == "Jane"
    assert body["is_admin"] is True
    # Unchanged fields preserved
    assert body["last_name"] == "Smith"
    assert body["email"] == "john@example.com"


@pytest.mark.asyncio
async def test_update_user_email_conflict(admin_client: AsyncClient) -> None:
    await admin_client.post(
        BASE_URL, json=_make_user_payload(email="existing@example.com")
    )
    create_res = await admin_client.post(
        BASE_URL, json=_make_user_payload(email="other@example.com")
    )
    user_id = create_res.json()["id"]

    res = await admin_client.patch(
        f"{BASE_URL}/{user_id}",
        json={"email": "existing@example.com"},
    )

    assert res.status_code == 409


@pytest.mark.asyncio
async def test_update_user_not_found(admin_client: AsyncClient) -> None:
    fake_id = str(uuid.uuid4())
    res = await admin_client.patch(
        f"{BASE_URL}/{fake_id}",
        json={"first_name": "Ghost"},
    )
    assert res.status_code == 404


# ── DELETE (soft) ──


@pytest.mark.asyncio
async def test_delete_user(admin_client: AsyncClient) -> None:
    create_res = await admin_client.post(BASE_URL, json=_make_user_payload())
    user_id = create_res.json()["id"]

    res = await admin_client.delete(f"{BASE_URL}/{user_id}")
    assert res.status_code == 204

    # User should no longer be visible
    get_res = await admin_client.get(f"{BASE_URL}/{user_id}")
    assert get_res.status_code == 404


@pytest.mark.asyncio
async def test_delete_user_not_found(admin_client: AsyncClient) -> None:
    fake_id = str(uuid.uuid4())
    res = await admin_client.delete(f"{BASE_URL}/{fake_id}")
    assert res.status_code == 404


@pytest.mark.asyncio
async def test_deleted_user_excluded_from_list(
    admin_client: AsyncClient,
) -> None:
    create_res = await admin_client.post(
        BASE_URL,
        json=_make_user_payload(email="deleteme@example.com"),
    )
    user_id = create_res.json()["id"]

    await admin_client.delete(f"{BASE_URL}/{user_id}")

    list_res = await admin_client.get(BASE_URL)
    ids = [u["id"] for u in list_res.json()]
    assert user_id not in ids
