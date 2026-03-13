from datetime import datetime, timedelta, timezone

import pytest
import pytest_asyncio
from sqlmodel.ext.asyncio.session import AsyncSession

from fastai.auth.core import PasswordService
from fastai.users.models import User
from fastai.users.schemas import AccountStatus, UserCreate

pytestmark = pytest.mark.integration


@pytest.fixture
def hasher() -> PasswordService:
    return PasswordService()


@pytest_asyncio.fixture
async def sample_user(test_db_session: AsyncSession, hasher: PasswordService) -> User:
    """Create a user for login tracking tests."""
    user_in = UserCreate(
        first_name="Login",
        last_name="Tester",
        email="login@example.com",
        password="securepassword123",
    )
    return await User.create(test_db_session, user_in, hasher=hasher)


class TestRecordLoginSuccess:
    """Tests for User.record_login_success."""

    @pytest.mark.asyncio
    async def test_updates_last_login_at(
        self, test_db_session: AsyncSession, sample_user: User
    ) -> None:
        assert sample_user.last_login_at is None

        updated = await sample_user.record_login_success(
            test_db_session, ip_address="127.0.0.1"
        )

        assert updated.last_login_at is not None
        assert updated.last_login_ip == "127.0.0.1"

    @pytest.mark.asyncio
    async def test_resets_failed_login_count(
        self, test_db_session: AsyncSession, sample_user: User
    ) -> None:
        # Simulate some failed attempts first
        sample_user.failed_login_count = 3
        test_db_session.add(sample_user)
        await test_db_session.commit()
        await test_db_session.refresh(sample_user)

        updated = await sample_user.record_login_success(test_db_session)
        assert updated.failed_login_count == 0

    @pytest.mark.asyncio
    async def test_clears_lockout(
        self, test_db_session: AsyncSession, sample_user: User
    ) -> None:
        # Simulate a locked account
        sample_user.locked_until = datetime.now(tz=timezone.utc) + timedelta(minutes=30)
        test_db_session.add(sample_user)
        await test_db_session.commit()
        await test_db_session.refresh(sample_user)

        updated = await sample_user.record_login_success(test_db_session)
        assert updated.locked_until is None

    @pytest.mark.asyncio
    async def test_ip_address_optional(
        self, test_db_session: AsyncSession, sample_user: User
    ) -> None:
        updated = await sample_user.record_login_success(test_db_session)
        assert updated.last_login_ip is None


class TestRecordLoginFailure:
    """Tests for User.record_login_failure."""

    @pytest.mark.asyncio
    async def test_increments_failed_count(
        self, test_db_session: AsyncSession, sample_user: User
    ) -> None:
        assert sample_user.failed_login_count == 0

        updated = await sample_user.record_login_failure(test_db_session)
        assert updated.failed_login_count == 1

    @pytest.mark.asyncio
    async def test_locks_after_max_attempts(
        self, test_db_session: AsyncSession, sample_user: User
    ) -> None:
        for _ in range(4):
            sample_user = await sample_user.record_login_failure(
                test_db_session, max_attempts=5, lockout_minutes=30
            )

        assert sample_user.locked_until is None
        assert sample_user.failed_login_count == 4

        # 5th attempt triggers lockout
        sample_user = await sample_user.record_login_failure(
            test_db_session, max_attempts=5, lockout_minutes=30
        )
        assert sample_user.locked_until is not None
        assert sample_user.status == AccountStatus.LOCKED
        assert sample_user.failed_login_count == 5

    @pytest.mark.asyncio
    async def test_lockout_uses_custom_parameters(
        self, test_db_session: AsyncSession, sample_user: User
    ) -> None:
        for _ in range(3):
            sample_user = await sample_user.record_login_failure(
                test_db_session, max_attempts=3, lockout_minutes=60
            )

        assert sample_user.locked_until is not None
        # Lockout should be ~60 minutes from now
        expected = datetime.now(tz=timezone.utc) + timedelta(minutes=60)
        assert abs(sample_user.locked_until - expected) < timedelta(seconds=5)


class TestIsLocked:
    """Tests for User.is_locked property."""

    @pytest.mark.asyncio
    async def test_not_locked_by_default(
        self, test_db_session: AsyncSession, sample_user: User
    ) -> None:
        assert sample_user.is_locked is False

    @pytest.mark.asyncio
    async def test_locked_when_locked_until_in_future(
        self, test_db_session: AsyncSession, sample_user: User
    ) -> None:
        sample_user.locked_until = datetime.now(tz=timezone.utc) + timedelta(minutes=30)
        assert sample_user.is_locked is True

    @pytest.mark.asyncio
    async def test_not_locked_when_locked_until_in_past(
        self, test_db_session: AsyncSession, sample_user: User
    ) -> None:
        sample_user.locked_until = datetime.now(tz=timezone.utc) - timedelta(minutes=1)
        assert sample_user.is_locked is False
