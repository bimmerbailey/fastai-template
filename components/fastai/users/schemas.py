from typing import Optional

from pydantic import AwareDatetime, EmailStr
from sqlmodel import SQLModel


class UserBase(SQLModel):
    """Shared user fields for API schemas. No database concerns."""

    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: EmailStr


class UserCreate(UserBase):
    """Schema for creating a new user. Accepts password, no id/timestamps."""

    password: str


class UserRead(UserBase):
    """Schema for reading a user. Excludes password, includes id and timestamps."""

    id: int
    is_admin: bool
    created_at: AwareDatetime
    updated_at: AwareDatetime


class UserUpdate(SQLModel):
    """Schema for partially updating a user. All fields optional."""

    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[EmailStr] = None
    password: Optional[str] = None
    is_admin: Optional[bool] = None
