from __future__ import annotations

from decimal import Decimal
from typing import Optional

from sqlmodel import Column, Field, Integer, Numeric, String, select
from sqlmodel.ext.asyncio.session import AsyncSession

from fastai.items.schemas import ItemBase, ItemCreate, ItemUpdate
from fastai.utils.models import TimestampMixin


class Item(ItemBase, TimestampMixin, table=True):
    """Database table model for items."""

    __tablename__ = "items"

    id: int | None = Field(default=None, sa_column=Column(Integer, primary_key=True))
    name: str = Field(sa_column=Column(String, nullable=False))
    cost: Optional[Decimal] = Field(
        default=None,
        decimal_places=2,
        sa_column=Column(Numeric(precision=10, scale=2), nullable=True),
    )
    description: Optional[str] = Field(
        default=None, sa_column=Column(String, nullable=True)
    )
    quantity: int = Field(default=0, sa_column=Column(Integer, nullable=False))

    @classmethod
    async def create(cls, session: AsyncSession, item_in: ItemCreate) -> Item:
        """Create a new item and persist it to the database."""
        item = cls.model_validate(item_in)
        session.add(item)
        await session.commit()
        await session.refresh(item)
        return item

    @classmethod
    async def get(cls, session: AsyncSession, item_id: int) -> Item | None:
        """Get a single item by ID. Returns None if not found."""
        return await session.get(cls, item_id)

    @classmethod
    async def get_all(
        cls, session: AsyncSession, offset: int = 0, limit: int = 100
    ) -> list[Item]:
        """Get a paginated list of items."""
        statement = select(cls).offset(offset).limit(limit)
        results = await session.exec(statement)
        return list(results.all())

    async def update(self, session: AsyncSession, item_in: ItemUpdate) -> Item:
        """Update this item with partial data."""
        update_data = item_in.model_dump(exclude_unset=True)
        self.sqlmodel_update(update_data)
        session.add(self)
        await session.commit()
        await session.refresh(self)
        return self

    async def delete(self, session: AsyncSession) -> None:
        """Delete this item from the database."""
        await session.delete(self)
        await session.commit()
