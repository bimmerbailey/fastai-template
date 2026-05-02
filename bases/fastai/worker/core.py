import logging
from contextlib import asynccontextmanager

import structlog.stdlib
from faststream import ContextRepo, FastStream

from fastai.database.core import create_db_engine, destroy_engine
from fastai.embeddings.core import KnowledgeBase
from fastai.embeddings.providers import create_embedder
from fastai.embeddings.settings import EmbeddingSettings
from fastai.events import NatsSettings
from fastai.extraction.core import ExtractionService
from fastai.logger.core import setup_worker_logging
from fastai.storage.core import StorageSettings
from fastai.subscribers_v1 import init_subscribers_v1

logger = structlog.stdlib.get_logger(__name__)


@asynccontextmanager
async def lifespan(context: ContextRepo):
    """Initialise long-lived singletons and expose them via ContextRepo."""
    engine = create_db_engine()
    storage_settings = StorageSettings()  # pyright: ignore[reportCallIssue]
    extraction_service = ExtractionService()
    embedding_settings = EmbeddingSettings()  # pyright: ignore[reportCallIssue]
    embedder = create_embedder(embedding_settings)
    knowledge_base = KnowledgeBase(embedder, embedding_settings)

    context.set_global("db_engine", engine)
    context.set_global("storage_settings", storage_settings)
    context.set_global("extraction_service", extraction_service)
    context.set_global("knowledge_base", knowledge_base)

    yield

    await destroy_engine(engine)


def create_app(nats_settings: NatsSettings | None = None) -> FastStream:
    """Create the FastStream worker application.

    Args:
        nats_settings: NATS connection settings. Loaded from env if not provided.

    Returns:
        A configured FastStream application with all subscribers registered.
    """
    setup_worker_logging()

    settings = nats_settings or NatsSettings()  # pyright: ignore[reportCallIssue]

    broker = settings.create_broker()
    broker.include_router(init_subscribers_v1())

    app_logger = logging.getLogger("faststream")
    app = FastStream(broker, logger=app_logger, lifespan=lifespan)

    logger.info("Worker app created", nats_url=settings.url)
    return app
