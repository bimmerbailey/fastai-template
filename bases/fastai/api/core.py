from contextlib import asynccontextmanager
from functools import partial

from fastapi import FastAPI
import structlog.stdlib
from sqlalchemy.ext.asyncio import AsyncEngine

from fastai.database import create_db_engine, destroy_engine, DatabaseSettings


logger = structlog.stdlib.get_logger(__name__)


@asynccontextmanager
async def lifespan(db_engine: AsyncEngine, app: FastAPI):
    logger.info("Initializing api")
    yield
    await destroy_engine(engine=db_engine)
    logger.info("Shutting down api")


def init_api(db_settings: DatabaseSettings = DatabaseSettings()) -> FastAPI:
    engine = create_db_engine(db_settings)
    app = FastAPI(root_path="/api", lifespan=partial(lifespan, engine))
    return app
