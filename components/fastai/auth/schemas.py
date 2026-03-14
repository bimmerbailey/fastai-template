import uuid
from datetime import datetime

from pydantic import AwareDatetime, Field
from sqlmodel import SQLModel


class OAuthAccountRead(SQLModel):
    """Public representation of a linked OAuth account."""

    id: uuid.UUID
    user_id: uuid.UUID
    oauth_provider: str
    created_at: AwareDatetime
    updated_at: AwareDatetime
    # Intentionally omits: access_token, refresh_token, expires_at, oauth_subject


class TokenPayload(SQLModel):
    """Decoded JWT claims."""

    sub: str = Field(description="User ID as a string.")
    type: str = Field(description="Token type: 'access' or 'refresh'.")
    exp: datetime = Field(description="Expiration timestamp.")
    iat: datetime = Field(description="Issued-at timestamp.")
    scopes: list[str] = Field(default_factory=list, description="OAuth2 scopes granted to this token.")


class TokenResponse(SQLModel):
    """Response body containing an access token.

    The refresh token is delivered separately via an HttpOnly cookie.
    """

    access_token: str
    token_type: str = "bearer"
