from typing import AsyncGenerator

import pytest
import pytest_asyncio
from fastapi import FastAPI
from fastapi.testclient import TestClient
from httpx import ASGITransport, AsyncClient

from fastai.admin_v1.core import init_admin_v1_app
from fastai.database.core import (
    DatabaseSettings,
)


@pytest_asyncio.fixture
async def app(
    test_db_settings: DatabaseSettings, test_db_engine
) -> AsyncGenerator[FastAPI, None]:
    """Create FastAPI test application."""
    application = init_admin_v1_app(test_db_engine)
    yield application


@pytest.fixture
def client(app: FastAPI) -> TestClient:
    """Create synchronous test client."""
    return TestClient(app)


@pytest_asyncio.fixture
async def admin_client(app: FastAPI) -> AsyncGenerator[AsyncClient, None]:
    """Create asynchronous test client."""
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://testserver"
    ) as ac:
        yield ac
