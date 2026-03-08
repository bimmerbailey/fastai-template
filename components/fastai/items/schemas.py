from decimal import Decimal
from typing import Optional

from pydantic import AwareDatetime
from sqlmodel import Field, SQLModel


class ItemBase(SQLModel):
    """Shared item fields for API schemas. No database concerns."""

    name: str
    cost: Optional[Decimal] = Field(default=None, decimal_places=2)
    description: Optional[str] = None
    quantity: int = 0


class ItemCreate(ItemBase):
    """Schema for creating a new item. No id/timestamps."""

    pass


class ItemRead(ItemBase):
    """Schema for reading an item. Includes id and timestamps."""

    id: int
    created_at: AwareDatetime
    updated_at: AwareDatetime


class ItemUpdate(SQLModel):
    """Schema for partially updating an item. All fields optional."""

    name: Optional[str] = None
    cost: Optional[Decimal] = None
    description: Optional[str] = None
    quantity: Optional[int] = None
