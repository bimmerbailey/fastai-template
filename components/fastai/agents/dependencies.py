from dataclasses import dataclass

from pydantic_ai.embeddings import Embedder
from sqlalchemy.ext.asyncio import AsyncEngine

from fastai.agents.settings import AgentSettings


@dataclass
class AgentDeps:
    """Dependencies injected into the agent at runtime.

    Provides access to the database engine, agent settings, and embedder
    for use in tools and dynamic instructions via
    ``RunContext[AgentDeps]``.

    Tools receive the engine rather than a shared session because
    PydanticAI may call multiple tools concurrently, and SQLAlchemy
    sessions are not safe for concurrent use.
    """

    engine: AsyncEngine
    settings: AgentSettings
    embedder: Embedder
