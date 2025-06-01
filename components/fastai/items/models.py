from typing import Optional

from pydantic import AwareDatetime
from sqlmodel import Column, DateTime, Field, Float, Integer, SQLModel, String, func

from fastai.utils.fields import date_now


class ItemBase(SQLModel):
    # TODO: Make sure tz-aware is working properly
    created_at: AwareDatetime = Field(
        default_factory=date_now,
        sa_column=Column(type_=DateTime(timezone=True), server_default=func.now()),
    )
    updated_at: AwareDatetime = Field(
        default_factory=date_now,
        sa_column=Column(type_=DateTime(timezone=True), onupdate=func.now()),
    )
    name: str = Field(sa_column=Column(String, nullable=False))
    cost: Optional[float] = Field(
        decimal_places=2, sa_column=Column(Float, nullable=True)
    )
    description: Optional[str] = Field(
        default=None, sa_column=Column(String, nullable=True, unique=False)
    )
    quantity: int = Field(default=0, sa_column=Column(Integer, nullable=False))


class Item(ItemBase, table=True):
    __tablename__ = "items"

    id: int | None = Field(default=None, sa_column=Column(Integer, primary_key=True))
