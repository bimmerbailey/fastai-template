from __future__ import annotations

import uuid as _uuid
from decimal import Decimal
from typing import Optional

from sqlmodel import Column, Field, Numeric, String, func, select
from sqlmodel.ext.asyncio.session import AsyncSession

from fastai.items.schemas import ItemBase, ItemCreate, ItemUpdate
from fastai.utils.models import TimestampMixin


class Item(ItemBase, TimestampMixin, table=True):
    """Database table model for items."""

    __tablename__ = "items"

    id: _uuid.UUID | None = Field(default_factory=_uuid.uuid4, primary_key=True)
    name: str = Field(sa_column=Column(String, nullable=False))
    cost: Optional[Decimal] = Field(
        default=None,
        decimal_places=2,
        sa_column=Column(Numeric(precision=10, scale=2), nullable=True),
    )
    description: Optional[str] = Field(
        default=None, sa_column=Column(String, nullable=True)
    )
    quantity: int = Field(default=0)

    @classmethod
    async def create(cls, session: AsyncSession, item_in: ItemCreate) -> Item:
        """Create a new item and persist it to the database."""
        item = cls.model_validate(item_in)
        session.add(item)
        await session.commit()
        await session.refresh(item)
        return item

    @classmethod
    async def get(cls, session: AsyncSession, item_id: _uuid.UUID) -> Item | None:
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

    @classmethod
    async def search_by_name(
        cls, session: AsyncSession, query: str, limit: int = 10
    ) -> list[Item]:
        """Search for items whose name matches a query (case-insensitive).

        Args:
            session: The async database session.
            query: A search term to match against item names.
            limit: Maximum number of results to return.

        Returns:
            A list of matching items.
        """
        statement = (
            select(cls)
            .where(cls.name.ilike(f"%{query}%"))  # type: ignore[union-attr]
            .limit(limit)
        )
        results = await session.exec(statement)
        return list(results.all())

    @classmethod
    async def count(cls, session: AsyncSession) -> int:
        """Get the total number of items in the database.

        Args:
            session: The async database session.

        Returns:
            The total item count.
        """
        statement = select(func.count()).select_from(cls)
        result = await session.exec(statement)
        return result.one()
