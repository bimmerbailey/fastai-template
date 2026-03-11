import uuid
from typing import AsyncGenerator

import pytest
import pytest_asyncio
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from pydantic_ai import Agent
from pydantic_ai.models.test import TestModel
from sqlmodel.ext.asyncio.session import AsyncSession

from fastai.agents.core import create_agent
from fastai.agents.dependencies import AgentDeps
from fastai.agents.settings import AgentSettings
from fastai.api_v1 import init_api_v1
from fastai.auth.core import PasswordService
from fastai.database.core import DatabaseSettings
from fastai.users.models import User
from fastai.users.schemas import UserCreate


@pytest.fixture
def agent_settings() -> AgentSettings:
    """Agent settings for testing."""
    return AgentSettings(model="test")


@pytest.fixture
def test_agent(agent_settings: AgentSettings) -> Agent[AgentDeps, str]:
    """Create a test agent with TestModel to avoid real LLM calls."""
    agent = create_agent(agent_settings)
    return agent


@pytest_asyncio.fixture
async def app(
    test_db_settings: DatabaseSettings,
    test_db_engine,
    test_agent: Agent[AgentDeps, str],
    agent_settings: AgentSettings,
) -> AsyncGenerator[FastAPI, None]:
    """Create FastAPI test application with agent using TestModel."""
    with test_agent.override(model=TestModel()):
        application = init_api_v1(
            test_db_engine,
            agent=test_agent,
            agent_settings=agent_settings,
        )
        yield application


@pytest_asyncio.fixture
async def chat_client(app: FastAPI) -> AsyncGenerator[AsyncClient, None]:
    """Create asynchronous test client for chat endpoints."""
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://testserver"
    ) as ac:
        yield ac


@pytest_asyncio.fixture
async def sample_user_id(test_db_session: AsyncSession) -> uuid.UUID:
    """Create a sample user in the database and return its ID.

    Needed because conversations have a foreign-key constraint on users.
    """
    hasher = PasswordService()
    user_in = UserCreate(
        first_name="Chat",
        last_name="Tester",
        email="chattester@example.com",
        password="securepassword123",
    )
    user = await User.create(test_db_session, user_in, hasher=hasher)
    assert user.id is not None
    return user.id
