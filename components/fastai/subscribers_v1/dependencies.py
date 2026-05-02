from collections.abc import AsyncIterator
from typing import Annotated

from faststream import Context, Depends
from sqlalchemy.ext.asyncio import AsyncEngine

from fastai.embeddings.core import KnowledgeBase
from fastai.extraction.core import ExtractionService
from fastai.storage.core import StorageService, StorageSettings

# Singletons — set in lifespan via ContextRepo.set_global()
EngineDep = Annotated[AsyncEngine, Context("db_engine")]
ExtractionDep = Annotated[ExtractionService, Context("extraction_service")]
KnowledgeBaseDep = Annotated[KnowledgeBase, Context("knowledge_base")]


# Per-message — yield handles async context manager lifecycle
async def get_storage(
    settings: Annotated[StorageSettings, Context("storage_settings")],
) -> AsyncIterator[StorageService]:
    async with StorageService(settings) as service:
        yield service


StorageServiceDep = Annotated[StorageService, Depends(get_storage)]
