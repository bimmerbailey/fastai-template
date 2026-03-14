from __future__ import annotations

import uuid as _uuid
from datetime import datetime, timezone

from pydantic import AwareDatetime
from sqlmodel import (
    Column,
    DateTime,
    Field,
    Integer,
    SQLModel,
    String,
    UniqueConstraint,
    select,
)
from sqlmodel.ext.asyncio.session import AsyncSession

from fastai.utils.models import TimestampMixin


class UserOAuthAccount(TimestampMixin, SQLModel, table=True):
    """Stores linked OAuth/OIDC provider accounts for a user.

    Each row represents one link between a user and an external identity
    provider. A single user can have multiple rows (e.g. Google + GitHub).
    The (oauth_provider, oauth_subject) pair is unique across the table.
    """

    __tablename__ = "user_oauth_accounts"  # pyright: ignore[reportAssignmentType]
    __table_args__ = (
        UniqueConstraint(
            "oauth_provider",
            "oauth_subject",
            name="uq_oauth_provider_subject",
        ),
    )

    id: _uuid.UUID = Field(default_factory=_uuid.uuid4, primary_key=True)
    user_id: _uuid.UUID = Field(
        foreign_key="users.id",
        index=True,
        nullable=False,
    )

    # Provider identification
    oauth_provider: str = Field(
        sa_column=Column(String, nullable=False, index=True),
        description="Provider name, e.g. 'google', 'github', 'microsoft'",
    )
    oauth_subject: str = Field(
        sa_column=Column(String, nullable=False),
        description="The 'sub' claim from the OIDC token — unique per provider",
    )

    # Token storage (encrypt at rest in production)
    access_token: str = Field(
        sa_column=Column(String, nullable=False),
    )
    refresh_token: str | None = Field(default=None)
    expires_at: int | None = Field(
        default=None,
        sa_column=Column(Integer, nullable=True),
        description="Token expiry as a unix timestamp",
    )

    # ── CRUD helpers ──

    @classmethod
    async def create(
        cls,
        session: AsyncSession,
        *,
        user_id: _uuid.UUID,
        oauth_provider: str,
        oauth_subject: str,
        access_token: str,
        refresh_token: str | None = None,
        expires_at: int | None = None,
    ) -> UserOAuthAccount:
        """Create a new OAuth account link."""
        account = cls(
            user_id=user_id,
            oauth_provider=oauth_provider,
            oauth_subject=oauth_subject,
            access_token=access_token,
            refresh_token=refresh_token,
            expires_at=expires_at,
        )
        session.add(account)
        await session.commit()
        await session.refresh(account)
        return account

    @classmethod
    async def get_by_provider_subject(
        cls,
        session: AsyncSession,
        *,
        oauth_provider: str,
        oauth_subject: str,
    ) -> UserOAuthAccount | None:
        """Look up an OAuth account by provider + subject."""
        statement = select(cls).where(
            cls.oauth_provider == oauth_provider,
            cls.oauth_subject == oauth_subject,
        )
        results = await session.exec(statement)
        return results.first()

    @classmethod
    async def get_by_user_id(
        cls,
        session: AsyncSession,
        user_id: _uuid.UUID,
    ) -> list[UserOAuthAccount]:
        """Return all OAuth accounts linked to a user."""
        statement = select(cls).where(cls.user_id == user_id)
        results = await session.exec(statement)
        return list(results.all())

    async def update_tokens(
        self,
        session: AsyncSession,
        *,
        access_token: str,
        refresh_token: str | None = None,
        expires_at: int | None = None,
    ) -> UserOAuthAccount:
        """Update the stored tokens for this OAuth link."""
        self.access_token = access_token
        self.refresh_token = refresh_token
        self.expires_at = expires_at
        session.add(self)
        await session.commit()
        await session.refresh(self)
        return self

    async def delete(self, session: AsyncSession) -> None:
        """Remove this OAuth account link."""
        await session.delete(self)
        await session.commit()


# NOTE: Think about using Redis if we bring that in
class RefreshToken(SQLModel, table=True):
    """Stores hashed refresh tokens for server-side revocation.

    Only the SHA-256 hash of the JWT is stored — the raw token is never
    persisted. This allows the server to revoke individual tokens or all
    tokens for a given user without relying solely on JWT expiration.
    """

    __tablename__ = "refresh_tokens"  # pyright: ignore[reportAssignmentType]

    id: _uuid.UUID = Field(default_factory=_uuid.uuid4, primary_key=True)
    user_id: _uuid.UUID = Field(
        foreign_key="users.id",
        index=True,
        nullable=False,
    )
    token_hash: str = Field(
        sa_column=Column(String, nullable=False, unique=True, index=True),
        description="SHA-256 hex digest of the refresh token JWT.",
    )
    expires_at: AwareDatetime = Field(
        sa_type=DateTime(timezone=True),  # pyright: ignore[reportArgumentType]
        nullable=False,
    )
    revoked_at: AwareDatetime | None = Field(
        default=None,
        sa_type=DateTime(timezone=True),  # pyright: ignore[reportArgumentType]
    )
    created_at: AwareDatetime = Field(
        default_factory=lambda: datetime.now(tz=timezone.utc),
        sa_type=DateTime(timezone=True),  # pyright: ignore[reportArgumentType]
    )

    # ── CRUD helpers ──

    @classmethod
    async def create(
        cls,
        session: AsyncSession,
        *,
        user_id: _uuid.UUID,
        token_hash: str,
        expires_at: datetime,
    ) -> RefreshToken:
        """Persist a new refresh token record."""
        record = cls(
            user_id=user_id,
            token_hash=token_hash,
            expires_at=expires_at,
        )
        session.add(record)
        await session.commit()
        await session.refresh(record)
        return record

    @classmethod
    async def get_by_token_hash(
        cls,
        session: AsyncSession,
        token_hash: str,
    ) -> RefreshToken | None:
        """Look up a refresh token by its hash."""
        statement = select(cls).where(cls.token_hash == token_hash)
        results = await session.exec(statement)
        return results.first()

    async def revoke(self, session: AsyncSession) -> RefreshToken:
        """Mark this refresh token as revoked."""
        self.revoked_at = datetime.now(tz=timezone.utc)
        session.add(self)
        await session.commit()
        await session.refresh(self)
        return self

    @classmethod
    async def revoke_all_for_user(
        cls,
        session: AsyncSession,
        user_id: _uuid.UUID,
    ) -> int:
        """Revoke all active refresh tokens for a user.

        Returns the number of tokens revoked.
        """
        now = datetime.now(tz=timezone.utc)
        statement = select(cls).where(
            cls.user_id == user_id,
            cls.revoked_at.is_(None),  # pyright: ignore[reportOptionalMemberAccess, reportAttributeAccessIssue]
        )
        results = await session.exec(statement)
        tokens = list(results.all())
        count = 0
        for token in tokens:
            token.revoked_at = now
            session.add(token)
            count += 1
        if count > 0:
            await session.commit()
        return count

    @classmethod
    async def cleanup_expired(cls, session: AsyncSession) -> int:
        """Delete all expired refresh tokens.

        Returns the number of tokens deleted.
        """
        now = datetime.now(tz=timezone.utc)
        statement = select(cls).where(cls.expires_at < now)
        results = await session.exec(statement)
        tokens = list(results.all())
        count = 0
        for token in tokens:
            await session.delete(token)
            count += 1
        if count > 0:
            await session.commit()
        return count

    @property
    def is_revoked(self) -> bool:
        """Whether this token has been revoked."""
        return self.revoked_at is not None

    @property
    def is_expired(self) -> bool:
        """Whether this token has expired."""
        return datetime.now(tz=timezone.utc) >= self.expires_at
