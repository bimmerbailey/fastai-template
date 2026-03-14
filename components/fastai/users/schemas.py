from __future__ import annotations

import uuid
from enum import StrEnum

from pydantic import AwareDatetime, EmailStr, field_validator
from sqlmodel import SQLModel


class AccountStatus(StrEnum):
    """User account lifecycle states."""

    ACTIVE = "active"
    SUSPENDED = "suspended"
    LOCKED = "locked"
    PENDING_VERIFICATION = "pending_verification"


class UserBase(SQLModel):
    """Shared user fields for API schemas. No database concerns."""

    first_name: str | None = None
    last_name: str | None = None
    email: EmailStr
    display_name: str | None = None
    avatar_url: str | None = None


class UserCreate(UserBase):
    """Schema for creating a new user. Accepts password, no id/timestamps."""

    password: str
    is_admin: bool = False

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        """Validate password strength per NIST SP 800-63B guidelines."""
        if len(v) < 10:
            raise ValueError("Password must be at least 10 characters")
        if len(v) > 128:
            raise ValueError("Password must be at most 128 characters")
        return v


class UserRead(UserBase):
    """Schema for reading a user.

    Excludes all sensitive fields: password_hash, mfa_secret,
    mfa_recovery_codes, failed_login_count, locked_until, last_login_ip.
    """

    id: uuid.UUID
    is_admin: bool
    status: AccountStatus
    is_active: bool
    is_email_verified: bool
    last_login_at: AwareDatetime | None
    created_at: AwareDatetime
    updated_at: AwareDatetime


class UserUpdate(SQLModel):
    """Schema for partially updating a user. All fields optional."""

    first_name: str | None = None
    last_name: str | None = None
    email: EmailStr | None = None
    password: str | None = None
    is_admin: bool | None = None
    display_name: str | None = None
    avatar_url: str | None = None
    status: AccountStatus | None = None

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str | None) -> str | None:
        """Validate password strength if provided."""
        if v is None:
            return v
        if len(v) < 10:
            raise ValueError("Password must be at least 10 characters")
        if len(v) > 128:
            raise ValueError("Password must be at most 128 characters")
        return v
