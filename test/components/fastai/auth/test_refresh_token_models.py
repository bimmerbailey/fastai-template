import uuid
from datetime import datetime, timedelta, timezone

import pytest
import pytest_asyncio
from sqlmodel.ext.asyncio.session import AsyncSession

from fastai.auth.core import PasswordService
from fastai.auth.models import RefreshToken
from fastai.users.models import User
from fastai.users.schemas import UserCreate

pytestmark = pytest.mark.integration


@pytest.fixture
def hasher() -> PasswordService:
    return PasswordService()


@pytest_asyncio.fixture
async def sample_user(test_db_session: AsyncSession, hasher: PasswordService) -> User:
    """Create a user for refresh token tests."""
    user_in = UserCreate(
        first_name="Token",
        last_name="Tester",
        email="token@example.com",
        password="securepassword123",
    )
    return await User.create(test_db_session, user_in, hasher=hasher)


@pytest_asyncio.fixture
async def user_id(sample_user: User) -> uuid.UUID:
    assert sample_user.id is not None
    return sample_user.id


@pytest.mark.asyncio
async def test_create_refresh_token(
    test_db_session: AsyncSession, user_id: uuid.UUID
) -> None:
    expires = datetime.now(tz=timezone.utc) + timedelta(days=7)
    token = await RefreshToken.create(
        test_db_session,
        user_id=user_id,
        token_hash="abc123hash",
        expires_at=expires,
    )

    assert token.id is not None
    assert isinstance(token.id, uuid.UUID)
    assert token.user_id == user_id
    assert token.token_hash == "abc123hash"
    assert token.revoked_at is None
    assert token.created_at is not None
    # family_id should be auto-generated
    assert token.family_id is not None
    assert isinstance(token.family_id, uuid.UUID)


@pytest.mark.asyncio
async def test_get_by_token_hash(
    test_db_session: AsyncSession, user_id: uuid.UUID
) -> None:
    expires = datetime.now(tz=timezone.utc) + timedelta(days=7)
    await RefreshToken.create(
        test_db_session,
        user_id=user_id,
        token_hash="findme123",
        expires_at=expires,
    )

    found = await RefreshToken.get_by_token_hash(test_db_session, "findme123")
    assert found is not None
    assert found.token_hash == "findme123"


@pytest.mark.asyncio
async def test_get_by_token_hash_not_found(
    test_db_session: AsyncSession,
) -> None:
    found = await RefreshToken.get_by_token_hash(test_db_session, "nonexistent")
    assert found is None


@pytest.mark.asyncio
async def test_revoke(test_db_session: AsyncSession, user_id: uuid.UUID) -> None:
    expires = datetime.now(tz=timezone.utc) + timedelta(days=7)
    token = await RefreshToken.create(
        test_db_session,
        user_id=user_id,
        token_hash="revokeme",
        expires_at=expires,
    )

    assert token.is_revoked is False

    revoked = await token.revoke(test_db_session)
    assert revoked.is_revoked is True
    assert revoked.revoked_at is not None


@pytest.mark.asyncio
async def test_revoke_all_for_user(
    test_db_session: AsyncSession, user_id: uuid.UUID
) -> None:
    expires = datetime.now(tz=timezone.utc) + timedelta(days=7)
    await RefreshToken.create(
        test_db_session,
        user_id=user_id,
        token_hash="token-1",
        expires_at=expires,
    )
    await RefreshToken.create(
        test_db_session,
        user_id=user_id,
        token_hash="token-2",
        expires_at=expires,
    )

    count = await RefreshToken.revoke_all_for_user(test_db_session, user_id)
    assert count == 2

    # Verify both are revoked
    t1 = await RefreshToken.get_by_token_hash(test_db_session, "token-1")
    t2 = await RefreshToken.get_by_token_hash(test_db_session, "token-2")
    assert t1 is not None and t1.is_revoked
    assert t2 is not None and t2.is_revoked


@pytest.mark.asyncio
async def test_revoke_all_skips_already_revoked(
    test_db_session: AsyncSession, user_id: uuid.UUID
) -> None:
    expires = datetime.now(tz=timezone.utc) + timedelta(days=7)
    token = await RefreshToken.create(
        test_db_session,
        user_id=user_id,
        token_hash="already-revoked",
        expires_at=expires,
    )
    await token.revoke(test_db_session)

    count = await RefreshToken.revoke_all_for_user(test_db_session, user_id)
    assert count == 0


@pytest.mark.asyncio
async def test_cleanup_expired(
    test_db_session: AsyncSession, user_id: uuid.UUID
) -> None:
    past = datetime.now(tz=timezone.utc) - timedelta(days=1)
    future = datetime.now(tz=timezone.utc) + timedelta(days=7)

    await RefreshToken.create(
        test_db_session,
        user_id=user_id,
        token_hash="expired-token",
        expires_at=past,
    )
    await RefreshToken.create(
        test_db_session,
        user_id=user_id,
        token_hash="valid-token",
        expires_at=future,
    )

    count = await RefreshToken.cleanup_expired(test_db_session)
    assert count == 1

    # Expired should be gone
    assert (
        await RefreshToken.get_by_token_hash(test_db_session, "expired-token") is None
    )
    # Valid should still exist
    assert (
        await RefreshToken.get_by_token_hash(test_db_session, "valid-token") is not None
    )


@pytest.mark.asyncio
async def test_is_expired_property(
    test_db_session: AsyncSession, user_id: uuid.UUID
) -> None:
    past = datetime.now(tz=timezone.utc) - timedelta(hours=1)
    future = datetime.now(tz=timezone.utc) + timedelta(hours=1)

    await RefreshToken.create(
        test_db_session,
        user_id=user_id,
        token_hash="past-token",
        expires_at=past,
    )
    await RefreshToken.create(
        test_db_session,
        user_id=user_id,
        token_hash="future-token",
        expires_at=future,
    )

    # Re-fetch to ensure attributes are loaded in async context
    fetched_expired = await RefreshToken.get_by_token_hash(
        test_db_session, "past-token"
    )
    fetched_valid = await RefreshToken.get_by_token_hash(
        test_db_session, "future-token"
    )

    assert fetched_expired is not None
    assert fetched_valid is not None
    assert fetched_expired.is_expired is True
    assert fetched_valid.is_expired is False


@pytest.mark.asyncio
async def test_create_with_explicit_family_id(
    test_db_session: AsyncSession, user_id: uuid.UUID
) -> None:
    family = uuid.uuid4()
    expires = datetime.now(tz=timezone.utc) + timedelta(days=7)
    token = await RefreshToken.create(
        test_db_session,
        user_id=user_id,
        token_hash="explicit-family",
        expires_at=expires,
        family_id=family,
    )
    assert token.family_id == family


@pytest.mark.asyncio
async def test_revoke_all_in_family(
    test_db_session: AsyncSession, user_id: uuid.UUID
) -> None:
    family = uuid.uuid4()
    expires = datetime.now(tz=timezone.utc) + timedelta(days=7)
    await RefreshToken.create(
        test_db_session,
        user_id=user_id,
        token_hash="fam-1",
        expires_at=expires,
        family_id=family,
    )
    await RefreshToken.create(
        test_db_session,
        user_id=user_id,
        token_hash="fam-2",
        expires_at=expires,
        family_id=family,
    )

    count = await RefreshToken.revoke_all_in_family(test_db_session, family)
    assert count == 2

    t1 = await RefreshToken.get_by_token_hash(test_db_session, "fam-1")
    t2 = await RefreshToken.get_by_token_hash(test_db_session, "fam-2")
    assert t1 is not None and t1.is_revoked
    assert t2 is not None and t2.is_revoked


@pytest.mark.asyncio
async def test_revoke_family_skips_other_families(
    test_db_session: AsyncSession, user_id: uuid.UUID
) -> None:
    family_a = uuid.uuid4()
    family_b = uuid.uuid4()
    expires = datetime.now(tz=timezone.utc) + timedelta(days=7)

    await RefreshToken.create(
        test_db_session,
        user_id=user_id,
        token_hash="family-a-token",
        expires_at=expires,
        family_id=family_a,
    )
    await RefreshToken.create(
        test_db_session,
        user_id=user_id,
        token_hash="family-b-token",
        expires_at=expires,
        family_id=family_b,
    )

    # Revoke only family A
    count = await RefreshToken.revoke_all_in_family(test_db_session, family_a)
    assert count == 1

    # Family B should be untouched
    tb = await RefreshToken.get_by_token_hash(test_db_session, "family-b-token")
    assert tb is not None and not tb.is_revoked
