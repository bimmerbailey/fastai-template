import uuid
from typing import AsyncGenerator

import pytest
import pytest_asyncio
from fastapi import FastAPI
from fastapi.testclient import TestClient
from httpx import ASGITransport, AsyncClient
from sqlmodel.ext.asyncio.session import AsyncSession

from fastai.api_v1 import init_api_v1
from fastai.auth.core import PasswordService
from fastai.database.core import DatabaseSettings
from fastai.users.models import User
from fastai.users.schemas import UserCreate


@pytest_asyncio.fixture
async def app(
    test_db_settings: DatabaseSettings, test_db_engine
) -> AsyncGenerator[FastAPI, None]:
    """Create FastAPI test application."""
    application = init_api_v1(test_db_engine)
    yield application


# TODO: Remove this if unused
@pytest.fixture
def client(app: FastAPI) -> TestClient:
    """Create synchronous test client."""
    return TestClient(app)


@pytest_asyncio.fixture
async def api_v1_client(app: FastAPI) -> AsyncGenerator[AsyncClient, None]:
    """Create asynchronous test client."""
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://testserver"
    ) as ac:
        yield ac


# TODO: Return the user instead of just id
@pytest_asyncio.fixture
async def sample_user_id(test_db_session: AsyncSession) -> uuid.UUID:
    """Create a sample user in the database and return its ID.

    This is needed for conversation tests because conversations have a
    foreign-key constraint on the users table.
    """
    hasher = PasswordService()
    user_in = UserCreate(
        first_name="Test",
        last_name="User",
        email="testuser@example.com",
        password="securepassword123",
    )
    user = await User.create(test_db_session, user_in, hasher=hasher)
    assert user.id is not None
    return user.id
