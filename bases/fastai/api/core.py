from contextlib import asynccontextmanager
from functools import partial

import structlog.stdlib
from asgi_correlation_id import CorrelationIdMiddleware
from fastapi import FastAPI
from fastapi.middleware import Middleware
from sqlalchemy.ext.asyncio import AsyncEngine

from fastai.database import DatabaseSettings, create_db_engine, destroy_engine
from fastai.logging.middleware import LoggingMiddleware
from fastai.logging.core import setup_api_logging

logger = structlog.stdlib.get_logger(__name__)


@asynccontextmanager
async def lifespan(db_engine: AsyncEngine, app: FastAPI):
    logger.info("Initializing api")
    yield
    await destroy_engine(engine=db_engine)
    logger.info("Shutting down api")


def init_api(db_settings: DatabaseSettings = DatabaseSettings()) -> FastAPI:
    setup_api_logging()
    engine = create_db_engine(db_settings)
    app = FastAPI(
        root_path="/api",
        lifespan=partial(lifespan, engine),
        middleware=[
            Middleware(CorrelationIdMiddleware),
            Middleware(LoggingMiddleware, logger=logger),
        ],
    )
    return app
