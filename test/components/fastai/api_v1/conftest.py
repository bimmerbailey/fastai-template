from typing import AsyncGenerator

import pytest_asyncio
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from pydantic import SecretStr
from pydantic_ai import Agent

from fastai.agents import AgentDeps, AgentSettings
from fastai.api_v1 import init_api_v1
from fastai.auth.settings import AuthSettings
from fastai.database.core import DatabaseSettings


@pytest_asyncio.fixture
async def app(
    test_db_settings: DatabaseSettings,
    test_db_engine,
    agent_settings: AgentSettings,
    test_agent: Agent[AgentDeps, str],
) -> AsyncGenerator[FastAPI, None]:
    """Create FastAPI test application."""
    test_secret = "test-secret-key-at-least-32-characters-long"
    key = SecretStr(test_secret)
    auth_settings = AuthSettings(secret_key=key)
    application = init_api_v1(
        test_db_engine,
        agent=test_agent,
        agent_settings=agent_settings,
        auth_settings=auth_settings,
    )
    yield application


@pytest_asyncio.fixture
async def api_v1_client(app: FastAPI) -> AsyncGenerator[AsyncClient, None]:
    """Create asynchronous test client."""
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://testserver"
    ) as ac:
        yield ac


@pytest_asyncio.fixture
async def authenticated_client(
    api_v1_client, create_user
) -> AsyncGenerator[AsyncClient, None]:

    user = await create_user(email="admin@example.com", password="password")
    await api_v1_client.post(
        "/auth/login", data={"email": user.email, "password": "password"}
    )
    yield api_v1_client
