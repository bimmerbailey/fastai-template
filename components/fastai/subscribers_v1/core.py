from faststream.nats import NatsRouter

from fastai.subscribers_v1 import documents


def init_subscribers_v1() -> NatsRouter:
    """Create the subscribers v1 router.

    All subscriber route modules are included here. Dependencies are resolved
    from the broker's ContextRepo, which must have the following globals set
    by the worker lifespan:

    - ``db_engine`` (AsyncEngine)
    - ``storage_settings`` (StorageSettings)
    - ``extraction_service`` (ExtractionService)
    - ``knowledge_base`` (KnowledgeBase)
    """
    router = NatsRouter()
    router.include_router(documents.router)
    return router
