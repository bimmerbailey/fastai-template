import uuid as _uuid
from datetime import datetime, timedelta, timezone

from pydantic import AwareDatetime
from sqlmodel import Column, DateTime, Field, String, select
from sqlmodel.ext.asyncio.session import AsyncSession
import structlog.stdlib

from fastai.auth import AuthSettings
from fastai.auth.core import PasswordService, password_service
from fastai.users.schemas import AccountStatus, UserBase, UserCreate, UserUpdate
from fastai.utils.models import TimestampMixin
from fastai.users.exceptions import (
    UserLockedError,
    UserNotFoundError,
    UserStatusError,
    UserInvalidCredentials,
)

logger = structlog.stdlib.get_logger(__name__)


class User(UserBase, TimestampMixin, table=True):
    """Database table model for users.

    Production-ready user model with:
    - UUID primary key
    - Argon2id password hashing
    - Account status lifecycle (active, suspended, locked, pending)
    - Email verification tracking
    - Login attempt tracking and brute-force protection
    - Soft delete support
    - MFA/2FA readiness
    - OIDC account linking (via UserOAuthAccount in auth component)
    """

    __tablename__ = "users"

    # ── Primary key ──
    id: _uuid.UUID | None = Field(default_factory=_uuid.uuid4, primary_key=True)

    # ── Authentication ──
    password_hash: str | None = Field(
        default=None,
        sa_column=Column(String, nullable=True),
        description="Argon2id hash. Nullable for OIDC-only users.",
    )
    is_admin: bool = Field(default=False)

    # ── Account status ──
    status: AccountStatus = Field(default=AccountStatus.PENDING_VERIFICATION)
    is_active: bool = Field(default=True)

    # ── Email verification ──
    is_email_verified: bool = Field(default=False)
    email_verified_at: AwareDatetime | None = Field(
        default=None,
        sa_type=DateTime(timezone=True),
    )

    # ── Login tracking ──
    last_login_at: AwareDatetime | None = Field(
        default=None,
        sa_type=DateTime(timezone=True),
    )
    last_login_ip: str | None = Field(default=None)

    # ── Brute-force protection ──
    failed_login_count: int = Field(default=0)
    locked_until: AwareDatetime | None = Field(
        default=None,
        sa_type=DateTime(timezone=True),
    )

    # ── Soft delete ──
    deleted_at: AwareDatetime | None = Field(
        default=None,
        sa_type=DateTime(timezone=True),
    )

    # ── Terms of Service ──
    tos_accepted_at: AwareDatetime | None = Field(
        default=None,
        sa_type=DateTime(timezone=True),
    )

    # ── MFA / 2FA ──
    mfa_enabled: bool = Field(default=False)
    mfa_secret: str | None = Field(
        default=None,
        description="TOTP secret. Must be encrypted at rest in production.",
    )
    mfa_recovery_codes: str | None = Field(
        default=None,
        description="JSON array of recovery codes. Encrypted at rest.",
    )

    # ── CRUD methods ──

    @classmethod
    async def create(
        cls,
        session: AsyncSession,
        user_in: UserCreate,
        *,
        hasher: PasswordService = password_service,
    ) -> "User":
        """Create a new user with hashed password and persist to the database."""
        data = user_in.model_dump(exclude={"password"})
        data["password_hash"] = hasher.hash(user_in.password)
        user = cls.model_validate(data)
        session.add(user)
        await session.commit()
        await session.refresh(user)
        return user

    @classmethod
    async def get(cls, session: AsyncSession, user_id: _uuid.UUID) -> "User | None":
        """Get a single user by ID. Excludes soft-deleted users."""
        user = await session.get(cls, user_id)
        if user is not None and user.deleted_at is not None:
            return None
        return user

    @classmethod
    async def get_by_email(cls, session: AsyncSession, email: str) -> "User | None":
        """Get a single user by email. Excludes soft-deleted users."""
        statement = select(cls).where(
            cls.email == email,
            cls.deleted_at.is_(None),  # type: ignore[union-attr]
        )
        results = await session.exec(statement)
        return results.first()

    @classmethod
    async def get_all(
        cls,
        session: AsyncSession,
        offset: int = 0,
        limit: int = 100,
        *,
        include_deleted: bool = False,
    ) -> "list[User]":
        """Get a paginated list of users. Excludes soft-deleted by default."""
        statement = select(cls)
        if not include_deleted:
            statement = statement.where(
                cls.deleted_at.is_(None)  # type: ignore[union-attr]
            )
        statement = statement.offset(offset).limit(limit)
        results = await session.exec(statement)
        return list(results.all())

    async def update(
        self,
        session: AsyncSession,
        user_in: UserUpdate,
        *,
        hasher: PasswordService = password_service,
    ) -> "User":
        """Update this user with partial data. Hashes password if provided."""
        update_data = user_in.model_dump(exclude_unset=True)

        # Hash password if it was included in the update
        if "password" in update_data:
            plain_password = update_data.pop("password")
            if plain_password is not None:
                update_data["password_hash"] = hasher.hash(plain_password)

        self.sqlmodel_update(update_data)
        session.add(self)
        await session.commit()
        await session.refresh(self)
        return self

    async def soft_delete(self, session: AsyncSession) -> "User":
        """Soft-delete this user by setting deleted_at timestamp."""
        self.deleted_at = datetime.now(tz=timezone.utc)
        self.is_active = False
        self.status = AccountStatus.SUSPENDED
        session.add(self)
        await session.commit()
        await session.refresh(self)
        return self

    async def delete(self, session: AsyncSession) -> None:
        """Permanently delete this user from the database.

        Prefer soft_delete() in production.
        """
        await session.delete(self)
        await session.commit()

    def verify_password(
        self,
        password: str,
        *,
        hasher: PasswordService = password_service,
    ) -> bool:
        """Verify a plain-text password against this user's hash.

        Returns False if the user has no password set (OIDC-only accounts).
        """
        if self.password_hash is None:
            return False
        return hasher.verify(password, self.password_hash)

    @classmethod
    async def login(
        cls,
        session: AsyncSession,
        *,
        email: str,
        password: str,
        auth_settings: AuthSettings,
        ip_address: str | None = None,
        hasher: PasswordService = password_service,
    ) -> "User":
        user = await cls.get_by_email(session, email)
        if user is None:
            raise UserNotFoundError("Invalid email or password.")

        # Check account lockout
        if user.is_locked:
            logger.warning(
                "Login attempt on locked account",
                user_id=str(user.id),
                locked_until=str(user.locked_until),
            )
            raise UserLockedError(
                "Account is temporarily locked due to too many failed login attempts."
            )

        # Check account status
        if not user.is_active or user.status == AccountStatus.SUSPENDED:
            raise UserStatusError("Account is inactive or suspended.")

        # Verify password
        if not user.verify_password(password, hasher=hasher):
            await user.record_login_failure(
                session,
                max_attempts=auth_settings.max_failed_login_attempts,
                lockout_minutes=auth_settings.lockout_duration_minutes,
            )
            logger.warning(
                "Failed login attempt",
                user_id=str(user.id),
                failed_count=user.failed_login_count,
            )
            raise UserInvalidCredentials("Invalid email or password.")

        # Success — record and issue tokens
        await user.record_login_success(session, ip_address=ip_address)

        logger.info("User logged in", actor=str(user.email))
        return user

    # ── Login tracking ──

    @property
    def is_locked(self) -> bool:
        """Whether the account is currently locked due to failed login attempts."""
        if self.locked_until is None:
            return False
        return datetime.now(tz=timezone.utc) < self.locked_until

    async def record_login_success(
        self,
        session: AsyncSession,
        *,
        ip_address: str | None = None,
    ) -> "User":
        """Record a successful login: update timestamps and reset failure count."""
        self.last_login_at = datetime.now(tz=timezone.utc)
        self.last_login_ip = ip_address
        self.failed_login_count = 0
        self.locked_until = None
        session.add(self)
        await session.commit()
        await session.refresh(self)
        return self

    async def record_login_failure(
        self,
        session: AsyncSession,
        *,
        max_attempts: int = 5,
        lockout_minutes: int = 30,
    ) -> "User":
        """Record a failed login attempt.

        Increments ``failed_login_count`` and locks the account when the
        threshold is reached.

        Args:
            session: AsyncSession
            max_attempts: Number of consecutive failures before lockout.
            lockout_minutes: How long the account stays locked, in minutes.
        """
        self.failed_login_count += 1
        if self.failed_login_count >= max_attempts:
            self.locked_until = datetime.now(tz=timezone.utc) + timedelta(
                minutes=lockout_minutes
            )
            self.status = AccountStatus.LOCKED
        session.add(self)
        await session.commit()
        await session.refresh(self)
        return self
