from fastapi import FastAPI
from sqlalchemy.ext.asyncio import AsyncEngine

from fastai.api_v1 import items, health


def init_api_v1(engine: AsyncEngine) -> FastAPI:
    """Create the API v1 FastAPI sub-application.

    This is a standalone FastAPI app that can be mounted on the main
    application or deployed independently. It receives its own database
    engine so that ``request.app.state.db_engine`` resolves correctly
    within the sub-app's dependency chain.
    """
    app = FastAPI(
        title="API v1",
        docs_url="/docs",
        openapi_url="/openapi.json",
    )

    app.state.db_engine = engine

    app.include_router(items.router)
    app.include_router(health.router)

    return app
