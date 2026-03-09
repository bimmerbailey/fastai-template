from contextlib import asynccontextmanager
from functools import partial

import logfire
import structlog.stdlib
from asgi_correlation_id import CorrelationIdMiddleware
from fastapi import FastAPI
from fastapi.middleware import Middleware
from sqlalchemy.ext.asyncio import AsyncEngine

from fastai.admin_v1 import init_admin_v1_app
from fastai.api_v1 import init_api_v1
from fastai.database import DatabaseSettings, create_db_engine, destroy_engine
from fastai.logger.core import setup_api_logging
from fastai.logger.middleware import LoggingMiddleware

logger = structlog.stdlib.get_logger(__name__)


@asynccontextmanager
async def lifespan(db_engine: AsyncEngine, app: FastAPI):
    logger.info("Initializing api")
    yield
    await destroy_engine(engine=db_engine)
    logger.info("Shutting down api")


def init_api(db_settings: DatabaseSettings | None = None) -> FastAPI:
    db_settings = db_settings or DatabaseSettings()

    setup_api_logging()

    # TODO: Setup jaeger to send to
    logfire.configure(send_to_logfire=False)
    logfire.instrument_pydantic_ai()
    logfire.instrument_sqlalchemy()

    engine = create_db_engine(db_settings)
    app = FastAPI(
        lifespan=partial(lifespan, engine),
        middleware=[
            Middleware(CorrelationIdMiddleware),
            Middleware(LoggingMiddleware, logger=logger),
        ],
    )
    logfire.instrument_fastapi(app=app)

    # Mount sub-applications
    app.mount("/admin/v1", init_admin_v1_app(engine))
    app.mount("/api/v1", init_api_v1(engine))

    return app
