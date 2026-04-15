import hashlib
from collections.abc import Sequence
from typing import AsyncGenerator, Generator, Literal

import pytest
import pytest_asyncio
from pydantic_ai import Agent, models
from pydantic_ai.embeddings import Embedder, EmbeddingModel, EmbeddingResult
from pydantic_ai.embeddings.settings import EmbeddingSettings as PAIEmbeddingSettings
from pydantic_ai.models.test import TestModel
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine
from sqlmodel import SQLModel
from sqlmodel.ext.asyncio.session import AsyncSession

from fastai.agents import AgentDeps, AgentSettings, create_agent
from fastai.auth import PasswordService
from fastai.database.core import (
    PostgresSettings,
    create_db_engine,
    destroy_engine,
    get_db_session,
)
from fastai.embeddings.core import KnowledgeBase
from fastai.embeddings.settings import EmbeddingSettings
from fastai.users import User, UserCreate

_TEST_EMBEDDING_DIM = EmbeddingSettings().dimensions

models.ALLOW_MODEL_REQUESTS = False


@pytest.fixture
def test_db_settings(monkeypatch) -> PostgresSettings:
    """Database settings for testing with in-memory database."""
    monkeypatch.setenv("FASTAI_POSTGRES_NAME", "test_fastai")
    return PostgresSettings()  # pyright: ignore[reportCallIssue]


@pytest_asyncio.fixture
async def test_db_engine(
    test_db_settings: PostgresSettings,
) -> AsyncGenerator[AsyncEngine, None]:
    """Create a test database engine."""
    engine = create_db_engine(test_db_settings)
    async with engine.begin() as conn:
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS pg_trgm"))
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
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


@pytest.fixture
def agent_settings() -> AgentSettings:
    """Agent settings for testing."""
    return AgentSettings(model="test")


def _deterministic_vector(
    text: str, dimensions: int = _TEST_EMBEDDING_DIM
) -> list[float]:
    """Generate a deterministic vector from text for testing."""
    seed = int(hashlib.md5(text.encode()).hexdigest(), 16)
    vector = []
    for _ in range(dimensions):
        seed = (seed * 1103515245 + 12345) & 0x7FFFFFFF
        vector.append((seed / 0x7FFFFFFF) * 2 - 1)
    return vector


class DeterministicEmbeddingModel(EmbeddingModel):
    """Test embedding model that produces deterministic vectors from content."""

    @property
    def model_name(self) -> str:
        return "mock-embed"

    @property
    def system(self) -> str:
        return "test"

    async def embed(
        self,
        inputs: str | Sequence[str],
        *,
        input_type: Literal["query", "document"],
        settings: PAIEmbeddingSettings | None = None,
    ) -> EmbeddingResult:
        texts, settings = self.prepare_embed(inputs, settings)
        embeddings = [_deterministic_vector(t) for t in texts]
        return EmbeddingResult(
            embeddings=embeddings,
            inputs=texts,
            input_type=input_type,
            model_name=self.model_name,
            provider_name=self.system,
        )


@pytest.fixture
def embedder() -> Embedder:
    """Create a test Embedder with deterministic vectors."""
    return Embedder(DeterministicEmbeddingModel())


@pytest.fixture
def knowledge_base(embedder: Embedder) -> KnowledgeBase:
    """Create a test KnowledgeBase with deterministic embeddings."""
    return KnowledgeBase(embedder)


@pytest.fixture
def test_agent(agent_settings: AgentSettings) -> Generator[Agent[AgentDeps, str]]:
    """Create a test agent with TestModel to avoid real LLM calls."""
    agent = create_agent(agent_settings)
    with agent.override(model=TestModel()):
        yield agent
