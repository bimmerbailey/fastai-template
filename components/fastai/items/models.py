from __future__ import annotations

import re
import uuid as _uuid
from decimal import Decimal
from typing import Optional

from sqlalchemy import CheckConstraint, Index
from sqlmodel import Column, Field, Numeric, String, func, select
from sqlmodel.ext.asyncio.session import AsyncSession

from fastai.items.schemas import ItemBase, ItemCreate, ItemUpdate
from fastai.utils.models import TimestampMixin


class Item(ItemBase, TimestampMixin, table=True):
    """Database table model for items."""

    __tablename__ = "items"  # pyright: ignore[reportAssignmentType]
    __table_args__ = (
        CheckConstraint("quantity >= 0", name="ck_items_quantity_nonneg"),
        CheckConstraint("cost >= 0", name="ck_items_cost_nonneg"),
        Index(
            "ix_items_name_trgm",
            "name",
            postgresql_using="gin",
            postgresql_ops={"name": "gin_trgm_ops"},
        ),
    )

    id: _uuid.UUID = Field(default_factory=_uuid.uuid4, primary_key=True)
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
        statement = (
            select(cls)
            .order_by(cls.created_at.desc())  # pyright: ignore[reportAttributeAccessIssue]
            .offset(offset)
            .limit(limit)
        )
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
        escaped = re.sub(r"([%_\\])", r"\\\1", query)
        statement = (
            select(cls)
            .where(cls.name.ilike(f"%{escaped}%"))  # pyright: ignore[reportAttributeAccessIssue]
            .limit(limit)
        )
        results = await session.exec(statement)
        return list(results.all())

    def build_embedding_text(self) -> str:
        """Build embeddable text from item fields, enriched with metadata labels.

        Field labels give the embedding model semantic anchors, improving
        retrieval quality for short content.
        """
        parts = [f"Item: {self.name}"]
        if self.description:
            parts.append(f"Description: {self.description}")
        if self.cost is not None:
            parts.append(f"Cost: ${self.cost}")
        parts.append(f"Quantity: {self.quantity}")
        return "\n".join(parts)

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
