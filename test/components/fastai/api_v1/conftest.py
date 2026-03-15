from typing import AsyncGenerator

import pytest_asyncio
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from pydantic import SecretStr
from pydantic_ai import Agent

from fastai.agents import AgentDeps, AgentSettings
from fastai.api_v1 import init_api_v1
from fastai.auth.settings import AuthSettings
from fastai.database.core import PostgresSettings


@pytest_asyncio.fixture
async def app(
    test_db_settings: PostgresSettings,
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


async def _login_client(client: AsyncClient, email: str, password: str) -> AsyncClient:
    """Log in and set the Authorization header on the client."""
    res = await client.post(
        "/auth/login", data={"username": email, "password": password}
    )
    assert res.status_code == 200, f"Login failed: {res.text}"
    token = res.json()["access_token"]
    client.headers["Authorization"] = f"Bearer {token}"
    return client


@pytest_asyncio.fixture
async def authenticated_client(
    api_v1_client: AsyncClient, create_user
) -> AsyncGenerator[AsyncClient, None]:
    """Client authenticated as a regular (non-admin) user."""
    user = await create_user(
        email="user@example.com", password="securepassword123", admin=False
    )
    await _login_client(api_v1_client, user.email, "securepassword123")
    yield api_v1_client


@pytest_asyncio.fixture
async def admin_client(
    api_v1_client: AsyncClient, create_user, test_db_session
) -> AsyncGenerator[AsyncClient, None]:
    """Client authenticated as an admin user."""
    user = await create_user(
        email="admin@example.com", password="securepassword123", admin=True
    )
    await _login_client(api_v1_client, user.email, "securepassword123")
    yield api_v1_client
