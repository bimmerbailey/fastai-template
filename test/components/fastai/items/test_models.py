from decimal import Decimal

import pytest
import pytest_asyncio
from sqlmodel.ext.asyncio.session import AsyncSession

from fastai.items.models import Item
from fastai.items.schemas import ItemCreate, ItemUpdate

pytestmark = pytest.mark.integration


@pytest_asyncio.fixture
async def sample_item(test_db_session: AsyncSession) -> Item:
    """Create a sample item for tests that need an existing record."""
    item_in = ItemCreate(
        name="Widget",
        cost=Decimal("9.99"),
        description="A test widget",
        quantity=10,
    )
    return await Item.create(test_db_session, item_in)


@pytest.mark.asyncio
async def test_create_item(test_db_session: AsyncSession) -> None:
    item_in = ItemCreate(
        name="Gadget",
        cost=Decimal("19.99"),
        description="A test gadget",
        quantity=5,
    )

    item = await Item.create(test_db_session, item_in)

    assert item.id is not None
    assert item.name == "Gadget"
    assert item.cost == Decimal("19.99")
    assert item.description == "A test gadget"
    assert item.quantity == 5
    assert item.created_at is not None
    assert item.updated_at is not None


@pytest.mark.asyncio
async def test_create_item_defaults(test_db_session: AsyncSession) -> None:
    item_in = ItemCreate(name="Minimal")

    item = await Item.create(test_db_session, item_in)

    assert item.id is not None
    assert item.name == "Minimal"
    assert item.cost is None
    assert item.description is None
    assert item.quantity == 0


@pytest.mark.asyncio
async def test_get_item(test_db_session: AsyncSession, sample_item: Item) -> None:
    assert sample_item.id is not None
    fetched = await Item.get(test_db_session, sample_item.id)

    assert fetched is not None
    assert fetched.id == sample_item.id
    assert fetched.name == sample_item.name


@pytest.mark.asyncio
async def test_get_item_not_found(test_db_session: AsyncSession) -> None:
    fetched = await Item.get(test_db_session, 99999)

    assert fetched is None


@pytest.mark.asyncio
async def test_get_all_items(test_db_session: AsyncSession, sample_item: Item) -> None:
    second = await Item.create(
        test_db_session,
        ItemCreate(name="Second Item", quantity=3),
    )

    items = await Item.get_all(test_db_session)

    assert len(items) >= 2
    item_ids = [i.id for i in items]
    assert sample_item.id in item_ids
    assert second.id in item_ids


@pytest.mark.asyncio
async def test_get_all_items_pagination(
    test_db_session: AsyncSession,
) -> None:
    for i in range(5):
        await Item.create(
            test_db_session,
            ItemCreate(name=f"Item {i}"),
        )

    page = await Item.get_all(test_db_session, offset=2, limit=2)

    assert len(page) == 2


@pytest.mark.asyncio
async def test_update_item(test_db_session: AsyncSession, sample_item: Item) -> None:
    update_in = ItemUpdate(name="Updated Widget", quantity=99)

    updated = await sample_item.update(test_db_session, update_in)

    assert updated.id == sample_item.id
    assert updated.name == "Updated Widget"
    assert updated.quantity == 99
    # Unset fields should remain unchanged
    assert updated.cost == Decimal("9.99")
    assert updated.description == "A test widget"


@pytest.mark.asyncio
async def test_update_item_partial(
    test_db_session: AsyncSession, sample_item: Item
) -> None:
    update_in = ItemUpdate(description="New description")

    updated = await sample_item.update(test_db_session, update_in)

    assert updated.name == "Widget"
    assert updated.cost == Decimal("9.99")
    assert updated.description == "New description"
    assert updated.quantity == 10


@pytest.mark.asyncio
async def test_delete_item(test_db_session: AsyncSession, sample_item: Item) -> None:
    assert sample_item.id is not None
    item_id = sample_item.id

    await sample_item.delete(test_db_session)

    fetched = await Item.get(test_db_session, item_id)
    assert fetched is None
