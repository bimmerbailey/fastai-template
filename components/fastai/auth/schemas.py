from __future__ import annotations

import uuid

from pydantic import AwareDatetime
from sqlmodel import SQLModel


class OAuthAccountRead(SQLModel):
    """Public representation of a linked OAuth account."""

    id: uuid.UUID
    user_id: uuid.UUID
    oauth_provider: str
    created_at: AwareDatetime
    updated_at: AwareDatetime
    # Intentionally omits: access_token, refresh_token, expires_at, oauth_subject
