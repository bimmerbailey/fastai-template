import pytest
from typing import AsyncGenerator

import pytest_asyncio
from fastapi import FastAPI
from fastapi.testclient import TestClient
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncEngine
from sqlmodel.ext.asyncio.session import AsyncSession

from fastai.database.core import DatabaseSettings, create_db_engine, get_db_session
from fastai.api.core import init_api


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
    yield engine
    await engine.dispose()


@pytest_asyncio.fixture
async def test_db_session(
    test_db_engine: AsyncEngine,
) -> AsyncGenerator[AsyncSession, None]:
    """Create a test database session."""
    async for session in get_db_session(test_db_engine):
        yield session


@pytest_asyncio.fixture
async def app(test_db_settings: DatabaseSettings) -> AsyncGenerator[FastAPI, None]:
    """Create FastAPI test application."""
    application = init_api()
    yield application


@pytest.fixture
def client(app):
    """Create synchronous test client."""
    return TestClient(app)


@pytest_asyncio.fixture
async def async_client(app) -> AsyncGenerator[AsyncClient, None]:
    """Create asynchronous test client."""
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://testserver"
    ) as ac:
        yield ac
