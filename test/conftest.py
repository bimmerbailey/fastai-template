from typing import AsyncGenerator

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncEngine
from sqlmodel import SQLModel
from sqlmodel.ext.asyncio.session import AsyncSession

from fastai.database.core import (
    DatabaseSettings,
    create_db_engine,
    destroy_engine,
    get_db_session,
)


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
