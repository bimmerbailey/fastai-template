from __future__ import annotations

import uuid as _uuid

from sqlmodel import Column, Field, Integer, SQLModel, String, UniqueConstraint, select
from sqlmodel.ext.asyncio.session import AsyncSession

from fastai.utils.models import TimestampMixin


class UserOAuthAccount(TimestampMixin, SQLModel, table=True):
    """Stores linked OAuth/OIDC provider accounts for a user.

    Each row represents one link between a user and an external identity
    provider. A single user can have multiple rows (e.g. Google + GitHub).
    The (oauth_provider, oauth_subject) pair is unique across the table.
    """

    __tablename__ = "user_oauth_accounts"
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
