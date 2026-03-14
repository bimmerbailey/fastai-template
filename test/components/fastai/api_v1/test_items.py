import uuid

import pytest
from httpx import AsyncClient

pytestmark = pytest.mark.integration

BASE_URL = "/items"


def _make_item_payload(
    *,
    name: str = "Widget",
    cost: str = "9.99",
    description: str = "A test widget",
    quantity: int = 10,
) -> dict:
    return {
        "name": name,
        "cost": cost,
        "description": description,
        "quantity": quantity,
    }


# ── AUTH ──


@pytest.mark.asyncio
async def test_unauthenticated_request_returns_401(
    api_v1_client: AsyncClient,
) -> None:
    """All item endpoints require authentication."""
    res = await api_v1_client.get(BASE_URL)
    assert res.status_code == 401


# ── CREATE (admin only) ──


@pytest.mark.asyncio
async def test_create_item(admin_client: AsyncClient) -> None:
    payload = _make_item_payload()
    res = await admin_client.post(BASE_URL, json=payload)

    assert res.status_code == 201
    body = res.json()
    assert body["name"] == "Widget"
    assert body["cost"] == "9.99"
    assert body["description"] == "A test widget"
    assert body["quantity"] == 10
    assert "id" in body
    assert "created_at" in body
    assert "updated_at" in body


@pytest.mark.asyncio
async def test_create_item_minimal(admin_client: AsyncClient) -> None:
    """Only name is required."""
    payload = {"name": "Minimal"}
    res = await admin_client.post(BASE_URL, json=payload)

    assert res.status_code == 201
    body = res.json()
    assert body["name"] == "Minimal"
    assert body["cost"] is None
    assert body["description"] is None
    assert body["quantity"] == 0


@pytest.mark.asyncio
async def test_create_item_missing_name(admin_client: AsyncClient) -> None:
    """Name is required — omitting it should return 422."""
    res = await admin_client.post(BASE_URL, json={"quantity": 5})
    assert res.status_code == 422


@pytest.mark.asyncio
async def test_create_item_forbidden_for_regular_user(
    authenticated_client: AsyncClient,
) -> None:
    """Non-admin users cannot create items."""
    res = await authenticated_client.post(BASE_URL, json=_make_item_payload())
    assert res.status_code == 403


# ── READ (single) ──


@pytest.mark.asyncio
async def test_get_item(admin_client: AsyncClient) -> None:
    create_res = await admin_client.post(BASE_URL, json=_make_item_payload())
    item_id = create_res.json()["id"]

    res = await admin_client.get(f"{BASE_URL}/{item_id}")

    assert res.status_code == 200
    body = res.json()
    assert body["id"] == item_id
    assert body["name"] == "Widget"


@pytest.mark.asyncio
async def test_get_item_not_found(authenticated_client: AsyncClient) -> None:
    fake_id = str(uuid.uuid4())
    res = await authenticated_client.get(f"{BASE_URL}/{fake_id}")
    assert res.status_code == 404


# ── READ (list) ──


@pytest.mark.asyncio
async def test_list_items(admin_client: AsyncClient) -> None:
    await admin_client.post(BASE_URL, json=_make_item_payload(name="Item A"))
    await admin_client.post(BASE_URL, json=_make_item_payload(name="Item B"))

    res = await admin_client.get(BASE_URL)

    assert res.status_code == 200
    items = res.json()
    assert len(items) >= 2
    names = {i["name"] for i in items}
    assert "Item A" in names
    assert "Item B" in names


@pytest.mark.asyncio
async def test_list_items_pagination(admin_client: AsyncClient) -> None:
    for i in range(5):
        await admin_client.post(
            BASE_URL, json=_make_item_payload(name=f"Page Item {i}")
        )

    res = await admin_client.get(BASE_URL, params={"offset": 0, "limit": 2})

    assert res.status_code == 200
    assert len(res.json()) == 2


# ── UPDATE ──


@pytest.mark.asyncio
async def test_update_item(admin_client: AsyncClient) -> None:
    create_res = await admin_client.post(BASE_URL, json=_make_item_payload())
    item_id = create_res.json()["id"]

    res = await admin_client.patch(
        f"{BASE_URL}/{item_id}",
        json={"name": "Updated Widget", "quantity": 99},
    )

    assert res.status_code == 200
    body = res.json()
    assert body["name"] == "Updated Widget"
    assert body["quantity"] == 99
    # Unchanged fields preserved
    assert body["cost"] == "9.99"
    assert body["description"] == "A test widget"


@pytest.mark.asyncio
async def test_update_item_partial(admin_client: AsyncClient) -> None:
    create_res = await admin_client.post(BASE_URL, json=_make_item_payload())
    item_id = create_res.json()["id"]

    res = await admin_client.patch(
        f"{BASE_URL}/{item_id}",
        json={"description": "New description"},
    )

    assert res.status_code == 200
    body = res.json()
    assert body["name"] == "Widget"
    assert body["cost"] == "9.99"
    assert body["description"] == "New description"
    assert body["quantity"] == 10


@pytest.mark.asyncio
async def test_update_item_not_found(authenticated_client: AsyncClient) -> None:
    fake_id = str(uuid.uuid4())
    res = await authenticated_client.patch(
        f"{BASE_URL}/{fake_id}",
        json={"name": "Ghost"},
    )
    assert res.status_code == 404


# ── DELETE (admin only) ──


@pytest.mark.asyncio
async def test_delete_item(admin_client: AsyncClient) -> None:
    create_res = await admin_client.post(BASE_URL, json=_make_item_payload())
    item_id = create_res.json()["id"]

    res = await admin_client.delete(f"{BASE_URL}/{item_id}")
    assert res.status_code == 204

    # Item should no longer be accessible
    get_res = await admin_client.get(f"{BASE_URL}/{item_id}")
    assert get_res.status_code == 404


@pytest.mark.asyncio
async def test_delete_item_not_found(admin_client: AsyncClient) -> None:
    fake_id = str(uuid.uuid4())
    res = await admin_client.delete(f"{BASE_URL}/{fake_id}")
    assert res.status_code == 404


@pytest.mark.asyncio
async def test_delete_item_forbidden_for_regular_user(
    authenticated_client: AsyncClient,
) -> None:
    """Non-admin users cannot delete items."""
    fake_id = str(uuid.uuid4())
    res = await authenticated_client.delete(f"{BASE_URL}/{fake_id}")
    assert res.status_code == 403


@pytest.mark.asyncio
async def test_deleted_item_excluded_from_list(
    admin_client: AsyncClient,
) -> None:
    create_res = await admin_client.post(
        BASE_URL, json=_make_item_payload(name="Delete Me")
    )
    item_id = create_res.json()["id"]

    await admin_client.delete(f"{BASE_URL}/{item_id}")

    list_res = await admin_client.get(BASE_URL)
    ids = [i["id"] for i in list_res.json()]
    assert item_id not in ids
