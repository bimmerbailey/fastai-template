import uuid

import pytest
import pytest_asyncio
from sqlmodel.ext.asyncio.session import AsyncSession

from fastai.auth.core import PasswordService
from fastai.auth.models import UserOAuthAccount
from fastai.users.models import User
from fastai.users.schemas import UserCreate

pytestmark = pytest.mark.integration


@pytest.fixture
def hasher() -> PasswordService:
    return PasswordService()


@pytest_asyncio.fixture
async def sample_user(test_db_session: AsyncSession, hasher: PasswordService) -> User:
    """Create a user to link OAuth accounts to."""
    user_in = UserCreate(
        first_name="OAuth",
        last_name="Tester",
        email="oauth@example.com",
        password="securepassword123",
    )
    return await User.create(test_db_session, user_in, hasher=hasher)


@pytest_asyncio.fixture
async def user_id(sample_user: User) -> uuid.UUID:
    """Extract user_id eagerly to avoid lazy-load issues after commits."""
    assert sample_user.id is not None
    return sample_user.id


@pytest.mark.asyncio
async def test_create_oauth_account(
    test_db_session: AsyncSession, user_id: uuid.UUID
) -> None:
    account = await UserOAuthAccount.create(
        test_db_session,
        user_id=user_id,
        oauth_provider="google",
        oauth_subject="google-sub-123",
        access_token="access-token-abc",
        refresh_token="refresh-token-xyz",
        expires_at=1700000000,
        account_email="user@gmail.com",
    )

    assert account.id is not None
    assert isinstance(account.id, uuid.UUID)
    assert account.user_id == user_id
    assert account.oauth_provider == "google"
    assert account.oauth_subject == "google-sub-123"
    assert account.access_token == "access-token-abc"
    assert account.refresh_token == "refresh-token-xyz"
    assert account.expires_at == 1700000000
    assert account.account_email == "user@gmail.com"
    assert account.created_at is not None
    assert account.updated_at is not None


@pytest.mark.asyncio
async def test_create_oauth_account_minimal(
    test_db_session: AsyncSession, user_id: uuid.UUID
) -> None:
    """Create an OAuth account with only required fields."""
    account = await UserOAuthAccount.create(
        test_db_session,
        user_id=user_id,
        oauth_provider="github",
        oauth_subject="github-sub-456",
        access_token="token-only",
    )

    assert account.refresh_token is None
    assert account.expires_at is None


@pytest.mark.asyncio
async def test_get_by_provider_subject(
    test_db_session: AsyncSession, user_id: uuid.UUID
) -> None:
    await UserOAuthAccount.create(
        test_db_session,
        user_id=user_id,
        oauth_provider="google",
        oauth_subject="google-sub-123",
        access_token="token",
    )

    found = await UserOAuthAccount.get_by_provider_subject(
        test_db_session,
        oauth_provider="google",
        oauth_subject="google-sub-123",
    )

    assert found is not None
    assert found.oauth_provider == "google"
    assert found.oauth_subject == "google-sub-123"


@pytest.mark.asyncio
async def test_get_by_provider_subject_not_found(
    test_db_session: AsyncSession,
) -> None:
    found = await UserOAuthAccount.get_by_provider_subject(
        test_db_session,
        oauth_provider="nonexistent",
        oauth_subject="no-such-id",
    )

    assert found is None


@pytest.mark.asyncio
async def test_get_by_user_id(
    test_db_session: AsyncSession, user_id: uuid.UUID
) -> None:
    await UserOAuthAccount.create(
        test_db_session,
        user_id=user_id,
        oauth_provider="google",
        oauth_subject="google-sub-123",
        access_token="token-g",
    )
    await UserOAuthAccount.create(
        test_db_session,
        user_id=user_id,
        oauth_provider="github",
        oauth_subject="github-sub-456",
        access_token="token-gh",
    )

    accounts = await UserOAuthAccount.get_by_user_id(test_db_session, user_id)

    assert len(accounts) == 2
    providers = {a.oauth_provider for a in accounts}
    assert providers == {"google", "github"}


@pytest.mark.asyncio
async def test_get_by_user_id_empty(
    test_db_session: AsyncSession,
) -> None:
    accounts = await UserOAuthAccount.get_by_user_id(test_db_session, uuid.uuid4())
    assert accounts == []


@pytest.mark.asyncio
async def test_update_tokens(test_db_session: AsyncSession, user_id: uuid.UUID) -> None:
    account = await UserOAuthAccount.create(
        test_db_session,
        user_id=user_id,
        oauth_provider="google",
        oauth_subject="google-sub-123",
        access_token="old-token",
    )

    updated = await account.update_tokens(
        test_db_session,
        access_token="new-token",
        refresh_token="new-refresh",
        expires_at=1800000000,
    )

    assert updated.access_token == "new-token"
    assert updated.refresh_token == "new-refresh"
    assert updated.expires_at == 1800000000


@pytest.mark.asyncio
async def test_delete_oauth_account(
    test_db_session: AsyncSession, user_id: uuid.UUID
) -> None:
    account = await UserOAuthAccount.create(
        test_db_session,
        user_id=user_id,
        oauth_provider="google",
        oauth_subject="google-sub-123",
        access_token="token",
    )

    await account.delete(test_db_session)

    found = await UserOAuthAccount.get_by_provider_subject(
        test_db_session,
        oauth_provider="google",
        oauth_subject="google-sub-123",
    )
    assert found is None


@pytest.mark.asyncio
async def test_create_oauth_account_without_email(
    test_db_session: AsyncSession, user_id: uuid.UUID
) -> None:
    """account_email defaults to None when not provided."""
    account = await UserOAuthAccount.create(
        test_db_session,
        user_id=user_id,
        oauth_provider="github",
        oauth_subject="gh-no-email",
        access_token="token",
    )
    assert account.account_email is None


@pytest.mark.asyncio
async def test_update_account_email(
    test_db_session: AsyncSession, user_id: uuid.UUID
) -> None:
    account = await UserOAuthAccount.create(
        test_db_session,
        user_id=user_id,
        oauth_provider="google",
        oauth_subject="google-email-update",
        access_token="token",
    )
    assert account.account_email is None

    updated = await account.update_account_email(test_db_session, "new@gmail.com")
    assert updated.account_email == "new@gmail.com"


@pytest.mark.asyncio
async def test_get_by_provider_email(
    test_db_session: AsyncSession, user_id: uuid.UUID
) -> None:
    await UserOAuthAccount.create(
        test_db_session,
        user_id=user_id,
        oauth_provider="google",
        oauth_subject="google-by-email",
        access_token="token",
        account_email="findme@gmail.com",
    )

    found = await UserOAuthAccount.get_by_provider_email(
        test_db_session,
        oauth_provider="google",
        account_email="findme@gmail.com",
    )
    assert found is not None
    assert found.account_email == "findme@gmail.com"

    # Different provider should not match
    not_found = await UserOAuthAccount.get_by_provider_email(
        test_db_session,
        oauth_provider="github",
        account_email="findme@gmail.com",
    )
    assert not_found is None
