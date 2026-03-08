import uuid

import pytest
import pytest_asyncio
from sqlmodel.ext.asyncio.session import AsyncSession

from fastai.auth.core import PasswordService
from fastai.users.models import User
from fastai.users.schemas import AccountStatus, UserCreate, UserUpdate

pytestmark = pytest.mark.integration


@pytest.fixture
def hasher() -> PasswordService:
    return PasswordService()


@pytest_asyncio.fixture
async def sample_user(test_db_session: AsyncSession, hasher: PasswordService) -> User:
    """Create a sample user for tests that need an existing record."""
    user_in = UserCreate(
        first_name="Jane",
        last_name="Doe",
        email="jane@example.com",
        password="securepassword123",
    )
    return await User.create(test_db_session, user_in, hasher=hasher)


@pytest.mark.asyncio
async def test_create_user(
    test_db_session: AsyncSession, hasher: PasswordService
) -> None:
    user_in = UserCreate(
        first_name="John",
        last_name="Smith",
        email="john@example.com",
        password="password12345",
    )

    user = await User.create(test_db_session, user_in, hasher=hasher)

    assert user.id is not None
    assert isinstance(user.id, uuid.UUID)
    assert user.first_name == "John"
    assert user.last_name == "Smith"
    assert user.email == "john@example.com"
    # Password should be hashed, not stored as plain text
    assert user.password_hash is not None
    assert user.password_hash != "password12345"
    assert hasher.verify("password12345", user.password_hash)
    assert user.is_admin is False
    assert user.status == AccountStatus.PENDING_VERIFICATION
    assert user.is_active is True
    assert user.is_email_verified is False
    assert user.deleted_at is None
    assert user.mfa_enabled is False
    assert user.created_at is not None
    assert user.updated_at is not None


@pytest.mark.asyncio
async def test_create_user_defaults(
    test_db_session: AsyncSession, hasher: PasswordService
) -> None:
    user_in = UserCreate(
        email="minimal@example.com",
        password="password12345",
    )

    user = await User.create(test_db_session, user_in, hasher=hasher)

    assert user.id is not None
    assert isinstance(user.id, uuid.UUID)
    assert user.first_name is None
    assert user.last_name is None
    assert user.display_name is None
    assert user.avatar_url is None
    assert user.is_admin is False
    assert user.status == AccountStatus.PENDING_VERIFICATION


@pytest.mark.asyncio
async def test_get_user(test_db_session: AsyncSession, sample_user: User) -> None:
    assert sample_user.id is not None
    fetched = await User.get(test_db_session, sample_user.id)

    assert fetched is not None
    assert fetched.id == sample_user.id
    assert fetched.email == sample_user.email


@pytest.mark.asyncio
async def test_get_user_not_found(test_db_session: AsyncSession) -> None:
    fetched = await User.get(test_db_session, uuid.uuid4())

    assert fetched is None


@pytest.mark.asyncio
async def test_get_by_email(test_db_session: AsyncSession, sample_user: User) -> None:
    fetched = await User.get_by_email(test_db_session, "jane@example.com")

    assert fetched is not None
    assert fetched.id == sample_user.id
    assert fetched.email == "jane@example.com"


@pytest.mark.asyncio
async def test_get_by_email_not_found(test_db_session: AsyncSession) -> None:
    fetched = await User.get_by_email(test_db_session, "nobody@example.com")

    assert fetched is None


@pytest.mark.asyncio
async def test_get_all_users(
    test_db_session: AsyncSession,
    sample_user: User,
    hasher: PasswordService,
) -> None:
    second = await User.create(
        test_db_session,
        UserCreate(email="second@example.com", password="password12345"),
        hasher=hasher,
    )

    users = await User.get_all(test_db_session)

    assert len(users) >= 2
    user_ids = [u.id for u in users]
    assert sample_user.id in user_ids
    assert second.id in user_ids


@pytest.mark.asyncio
async def test_get_all_users_pagination(
    test_db_session: AsyncSession,
    hasher: PasswordService,
) -> None:
    for i in range(5):
        await User.create(
            test_db_session,
            UserCreate(email=f"user{i}@example.com", password="password12345"),
            hasher=hasher,
        )

    page = await User.get_all(test_db_session, offset=2, limit=2)

    assert len(page) == 2


@pytest.mark.asyncio
async def test_update_user(
    test_db_session: AsyncSession,
    sample_user: User,
    hasher: PasswordService,
) -> None:
    update_in = UserUpdate(first_name="Janet", is_admin=True)

    updated = await sample_user.update(test_db_session, update_in, hasher=hasher)

    assert updated.id == sample_user.id
    assert updated.first_name == "Janet"
    assert updated.is_admin is True
    # Unset fields should remain unchanged
    assert updated.last_name == "Doe"
    assert updated.email == "jane@example.com"
    # Password hash should remain unchanged (not in update)
    assert updated.password_hash is not None
    assert hasher.verify("securepassword123", updated.password_hash)


@pytest.mark.asyncio
async def test_update_user_partial(
    test_db_session: AsyncSession,
    sample_user: User,
    hasher: PasswordService,
) -> None:
    update_in = UserUpdate(email="newemail@example.com")

    updated = await sample_user.update(test_db_session, update_in, hasher=hasher)

    assert updated.first_name == "Jane"
    assert updated.last_name == "Doe"
    assert updated.email == "newemail@example.com"
    # Password hash should still be valid
    assert updated.password_hash is not None
    assert hasher.verify("securepassword123", updated.password_hash)


@pytest.mark.asyncio
async def test_update_user_password(
    test_db_session: AsyncSession,
    sample_user: User,
    hasher: PasswordService,
) -> None:
    """Updating password should hash the new value."""
    old_hash = sample_user.password_hash
    update_in = UserUpdate(password="newpassword12345")

    updated = await sample_user.update(test_db_session, update_in, hasher=hasher)

    assert updated.password_hash is not None
    assert updated.password_hash != old_hash
    assert updated.password_hash != "newpassword12345"
    assert hasher.verify("newpassword12345", updated.password_hash)
    assert not hasher.verify("securepassword123", updated.password_hash)


@pytest.mark.asyncio
async def test_verify_password(
    test_db_session: AsyncSession, sample_user: User
) -> None:
    assert sample_user.verify_password("securepassword123") is True
    assert sample_user.verify_password("wrongpassword") is False


@pytest.mark.asyncio
async def test_verify_password_no_hash(
    test_db_session: AsyncSession,
) -> None:
    """OIDC-only users have no password hash; verify should return False."""
    user = User(
        email="oidc@example.com",
        password_hash=None,
    )
    assert user.verify_password("anything") is False


@pytest.mark.asyncio
async def test_soft_delete_user(
    test_db_session: AsyncSession, sample_user: User
) -> None:
    assert sample_user.id is not None
    user_id = sample_user.id

    deleted = await sample_user.soft_delete(test_db_session)

    assert deleted.deleted_at is not None
    assert deleted.is_active is False
    assert deleted.status == AccountStatus.SUSPENDED

    # get() should exclude soft-deleted users
    fetched = await User.get(test_db_session, user_id)
    assert fetched is None


@pytest.mark.asyncio
async def test_soft_deleted_excluded_from_get_by_email(
    test_db_session: AsyncSession, sample_user: User
) -> None:
    await sample_user.soft_delete(test_db_session)

    fetched = await User.get_by_email(test_db_session, "jane@example.com")
    assert fetched is None


@pytest.mark.asyncio
async def test_soft_deleted_excluded_from_get_all(
    test_db_session: AsyncSession,
    sample_user: User,
    hasher: PasswordService,
) -> None:
    second = await User.create(
        test_db_session,
        UserCreate(email="active@example.com", password="password12345"),
        hasher=hasher,
    )
    await sample_user.soft_delete(test_db_session)

    users = await User.get_all(test_db_session)

    user_ids = [u.id for u in users]
    assert sample_user.id not in user_ids
    assert second.id in user_ids


@pytest.mark.asyncio
async def test_get_all_include_deleted(
    test_db_session: AsyncSession,
    sample_user: User,
    hasher: PasswordService,
) -> None:
    await User.create(
        test_db_session,
        UserCreate(email="active@example.com", password="password12345"),
        hasher=hasher,
    )
    await sample_user.soft_delete(test_db_session)

    users = await User.get_all(test_db_session, include_deleted=True)

    user_ids = [u.id for u in users]
    assert sample_user.id in user_ids


@pytest.mark.asyncio
async def test_hard_delete_user(
    test_db_session: AsyncSession, sample_user: User
) -> None:
    assert sample_user.id is not None
    user_id = sample_user.id

    await sample_user.delete(test_db_session)

    fetched = await User.get(test_db_session, user_id)
    assert fetched is None


@pytest.mark.asyncio
async def test_password_validation_too_short() -> None:
    with pytest.raises(ValueError, match="at least 10 characters"):
        UserCreate(
            email="test@example.com",
            password="short",
        )


@pytest.mark.asyncio
async def test_password_validation_too_long() -> None:
    with pytest.raises(ValueError, match="at most 128 characters"):
        UserCreate(
            email="test@example.com",
            password="x" * 129,
        )
