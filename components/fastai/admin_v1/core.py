from fastapi import FastAPI
from sqlalchemy.ext.asyncio import AsyncEngine

from fastai.admin_v1 import users, health


def init_admin_v1_app(engine: AsyncEngine) -> FastAPI:
    """Create the admin v1 FastAPI sub-application.

    This is a standalone FastAPI app that can be mounted on the main
    application or deployed independently. It receives its own database
    engine so that ``request.app.state.db_engine`` resolves correctly
    within the sub-app's dependency chain.
    """
    app = FastAPI(
        title="Admin API v1",
        docs_url="/docs",
        openapi_url="/openapi.json",
    )

    app.state.db_engine = engine

    app.include_router(users.router)
    app.include_router(health.router)

    return app
