from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic_ai import Agent
from sqlalchemy.ext.asyncio import AsyncEngine

from fastai.agents.core import create_agent
from fastai.agents.dependencies import AgentDeps
from fastai.agents.settings import AgentSettings
from fastai.api_v1 import authentication, chats, conversations, health, items
from pydantic_ai.embeddings import Embedder

from fastai.auth.settings import AuthSettings
from fastai.auth.token_service import TokenService
from fastai.embeddings.providers import create_embedder
from fastai.embeddings.settings import EmbeddingSettings


def init_api_v1(
    engine: AsyncEngine,
    agent: Agent[AgentDeps, str] | None = None,
    agent_settings: AgentSettings | None = None,
    auth_settings: AuthSettings | None = None,
    embedding_settings: EmbeddingSettings | None = None,
    embedder: Embedder | None = None,
) -> FastAPI:
    """Create the API v1 FastAPI sub-application.

    This is a standalone FastAPI app that can be mounted on the main
    application or deployed independently. It receives its own database
    engine so that ``request.app.state.db_engine`` resolves correctly
    within the sub-app's dependency chain.

    Args:
        engine: The async database engine.
        agent: An optional pre-configured agent instance. If not provided,
            one will be created from ``agent_settings``.
        agent_settings: Settings for the AI agent. Defaults will be loaded
            from environment variables if not provided.
        auth_settings: JWT authentication settings. Defaults will be loaded
            from environment variables if not provided.
        embedding_settings: Settings for the embedding service. Defaults
            will be loaded from environment variables if not provided.
    """
    settings = agent_settings or AgentSettings()
    auth = auth_settings or AuthSettings()  # pyright: ignore[reportCallIssue]  # reads secret_key from env
    emb_settings = embedding_settings or EmbeddingSettings()
    emb = embedder or create_embedder(emb_settings)

    app = FastAPI(
        title="API v1",
        docs_url="/docs",
        openapi_url="/openapi.json",
    )
    app.add_middleware(
        CORSMiddleware,
        # TODO: ABSOLUTELY COME BACK TO THIS
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.state.db_engine = engine
    app.state.agent_settings = settings
    app.state.agent = agent or create_agent(settings)
    app.state.auth_settings = auth
    app.state.token_service = TokenService(auth)
    app.state.embedder = emb

    app.include_router(authentication.router)
    app.include_router(items.router)
    app.include_router(health.router)
    app.include_router(chats.router)
    app.include_router(conversations.router)

    return app
