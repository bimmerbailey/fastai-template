from fastapi import FastAPI
from pydantic_ai import Agent
from sqlalchemy.ext.asyncio import AsyncEngine

from fastai.agents.core import create_agent
from fastai.agents.dependencies import AgentDeps
from fastai.agents.settings import AgentSettings
from fastai.api_v1 import chats, conversations, health, items, authentication
from fastai.auth.settings import AuthSettings
from fastai.auth.token_service import TokenService


def init_api_v1(
    engine: AsyncEngine,
    agent: Agent[AgentDeps, str] | None = None,
    agent_settings: AgentSettings | None = None,
    auth_settings: AuthSettings | None = None,
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
    """
    settings = agent_settings or AgentSettings()
    auth = auth_settings or AuthSettings()

    app = FastAPI(
        title="API v1",
        docs_url="/docs",
        openapi_url="/openapi.json",
    )

    app.state.db_engine = engine
    app.state.agent_settings = settings
    app.state.agent = agent or create_agent(settings)
    app.state.auth_settings = auth
    app.state.token_service = TokenService(auth)

    app.include_router(authentication.router)
    app.include_router(items.router)
    app.include_router(health.router)
    app.include_router(chats.router)
    app.include_router(conversations.router)

    return app
