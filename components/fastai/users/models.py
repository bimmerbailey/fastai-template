from typing import Optional

from pydantic import AwareDatetime, EmailStr
from sqlmodel import Boolean, Column, DateTime, Field, Integer, SQLModel, String, func

from fastai.utils.fields import date_now


class UserBase(SQLModel):
    # TODO: Make sure tz-aware is working properly
    created_at: AwareDatetime = Field(
        default_factory=date_now,
        sa_column=Column(type_=DateTime(timezone=True), server_default=func.now()),
    )
    updated_at: AwareDatetime = Field(
        default_factory=date_now,
        sa_column=Column(type_=DateTime(timezone=True), onupdate=func.now()),
    )
    first_name: Optional[str] = Field(sa_column=Column(String, nullable=True))
    last_name: Optional[str] = Field(sa_column=Column(String, nullable=True))
    email: EmailStr = Field(sa_column=Column(String, nullable=False, unique=True))
    password: str = Field(sa_column=Column(String, nullable=False))
    is_admin: bool = Field(default=False, sa_column=Column(Boolean, nullable=False))


class User(UserBase, table=True):
    __tablename__ = "users"

    id: int | None = Field(default=None, sa_column=Column(Integer, primary_key=True))
