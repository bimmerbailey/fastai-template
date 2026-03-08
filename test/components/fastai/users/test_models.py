import pytest
import pytest_asyncio
from sqlmodel.ext.asyncio.session import AsyncSession

from fastai.users.models import User
from fastai.users.schemas import UserCreate, UserUpdate

pytestmark = pytest.mark.integration


@pytest_asyncio.fixture
async def sample_user(test_db_session: AsyncSession) -> User:
    """Create a sample user for tests that need an existing record."""
    user_in = UserCreate(
        first_name="Jane",
        last_name="Doe",
        email="jane@example.com",
        password="securepassword123",
    )
    return await User.create(test_db_session, user_in)


@pytest.mark.asyncio
async def test_create_user(test_db_session: AsyncSession) -> None:
    user_in = UserCreate(
        first_name="John",
        last_name="Smith",
        email="john@example.com",
        password="password123",
    )

    user = await User.create(test_db_session, user_in)

    assert user.id is not None
    assert user.first_name == "John"
    assert user.last_name == "Smith"
    assert user.email == "john@example.com"
    assert user.password == "password123"
    assert user.is_admin is False
    assert user.created_at is not None
    assert user.updated_at is not None


@pytest.mark.asyncio
async def test_create_user_defaults(test_db_session: AsyncSession) -> None:
    user_in = UserCreate(
        email="minimal@example.com",
        password="password123",
    )

    user = await User.create(test_db_session, user_in)

    assert user.id is not None
    assert user.first_name is None
    assert user.last_name is None
    assert user.is_admin is False


@pytest.mark.asyncio
async def test_get_user(test_db_session: AsyncSession, sample_user: User) -> None:
    assert sample_user.id is not None
    fetched = await User.get(test_db_session, sample_user.id)

    assert fetched is not None
    assert fetched.id == sample_user.id
    assert fetched.email == sample_user.email


@pytest.mark.asyncio
async def test_get_user_not_found(test_db_session: AsyncSession) -> None:
    fetched = await User.get(test_db_session, 99999)

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
async def test_get_all_users(test_db_session: AsyncSession, sample_user: User) -> None:
    second = await User.create(
        test_db_session,
        UserCreate(email="second@example.com", password="pass"),
    )

    users = await User.get_all(test_db_session)

    assert len(users) >= 2
    user_ids = [u.id for u in users]
    assert sample_user.id in user_ids
    assert second.id in user_ids


@pytest.mark.asyncio
async def test_get_all_users_pagination(
    test_db_session: AsyncSession,
) -> None:
    for i in range(5):
        await User.create(
            test_db_session,
            UserCreate(email=f"user{i}@example.com", password="pass"),
        )

    page = await User.get_all(test_db_session, offset=2, limit=2)

    assert len(page) == 2


@pytest.mark.asyncio
async def test_update_user(test_db_session: AsyncSession, sample_user: User) -> None:
    update_in = UserUpdate(first_name="Janet", is_admin=True)

    updated = await sample_user.update(test_db_session, update_in)

    assert updated.id == sample_user.id
    assert updated.first_name == "Janet"
    assert updated.is_admin is True
    # Unset fields should remain unchanged
    assert updated.last_name == "Doe"
    assert updated.email == "jane@example.com"
    assert updated.password == "securepassword123"


@pytest.mark.asyncio
async def test_update_user_partial(
    test_db_session: AsyncSession, sample_user: User
) -> None:
    update_in = UserUpdate(email="newemail@example.com")

    updated = await sample_user.update(test_db_session, update_in)

    assert updated.first_name == "Jane"
    assert updated.last_name == "Doe"
    assert updated.email == "newemail@example.com"
    assert updated.password == "securepassword123"


@pytest.mark.asyncio
async def test_delete_user(test_db_session: AsyncSession, sample_user: User) -> None:
    assert sample_user.id is not None
    user_id = sample_user.id

    await sample_user.delete(test_db_session)

    fetched = await User.get(test_db_session, user_id)
    assert fetched is None
