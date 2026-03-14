import uuid
from typing import AsyncGenerator, Generator

import pytest
import pytest_asyncio
from pydantic_ai import Agent, models
from pydantic_ai.models.test import TestModel
from sqlalchemy.ext.asyncio import AsyncEngine
from sqlmodel import SQLModel
from sqlmodel.ext.asyncio.session import AsyncSession

from fastai.agents import AgentDeps, AgentSettings, create_agent
from fastai.auth import PasswordService
from fastai.database.core import (
    DatabaseSettings,
    create_db_engine,
    destroy_engine,
    get_db_session,
)
from fastai.users import User, UserCreate

models.ALLOW_MODEL_REQUESTS = False


@pytest.fixture
def test_db_settings() -> DatabaseSettings:
    """Database settings for testing with in-memory database."""
    return DatabaseSettings(name="test_fastai")


@pytest_asyncio.fixture
async def test_db_engine(
    test_db_settings: DatabaseSettings,
) -> AsyncGenerator[AsyncEngine, None]:
    """Create a test database engine."""
    engine = create_db_engine(test_db_settings)
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)

    yield engine

    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.drop_all)

    await destroy_engine(engine)


@pytest_asyncio.fixture
async def test_db_session(
    test_db_engine: AsyncEngine,
) -> AsyncGenerator[AsyncSession, None]:
    """Create a test database session."""
    async for session in get_db_session(test_db_engine):
        yield session


@pytest.fixture
def password_service() -> PasswordService:
    return PasswordService()


@pytest.fixture
def create_user(test_db_session: AsyncSession, password_service: PasswordService):
    """Create a test user in the database"""

    async def _create(
        email: str | None = None,
        password: str | None = None,
        first_name: str | None = None,
        last_name: str | None = None,
        admin: bool = False,
    ) -> User:
        email = email or "testuser@example.com"
        password = password or "securepassword123"
        first_name = first_name or "Test"
        last_name = last_name or "User"
        to_create = UserCreate(
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name,
            is_admin=admin,
        )
        return await User.create(session=test_db_session, user_in=to_create)

    return _create


@pytest_asyncio.fixture
async def sample_user_id(create_user) -> uuid.UUID:
    """Create a sample user in the database and return its ID.

    This is needed for conversation tests because conversations have a
    foreign-key constraint on the users table.
    """
    user = await create_user()
    assert user.id is not None
    return user.id


@pytest.fixture
def agent_settings() -> AgentSettings:
    """Agent settings for testing."""
    return AgentSettings(model="test")


@pytest.fixture
def test_agent(agent_settings: AgentSettings) -> Generator[Agent[AgentDeps, str]]:
    """Create a test agent with TestModel to avoid real LLM calls."""
    agent = create_agent(agent_settings)
    with agent.override(model=TestModel()):
        yield agent
