from collections.abc import AsyncIterator
from typing import Annotated

from fastapi import Depends, Request

from fastai.events.core import EventPublisher
from fastai.storage.core import StorageService, StorageSettings


def get_storage_settings(request: Request) -> StorageSettings:
    """Retrieve storage settings from application state."""
    settings: StorageSettings = request.app.state.storage_settings
    return settings


StorageSettingsDep = Annotated[StorageSettings, Depends(get_storage_settings)]


async def get_storage(
    settings: StorageSettingsDep,
) -> AsyncIterator[StorageService]:
    """Yield a per-request StorageService with its own S3 resource."""
    async with StorageService(settings) as service:
        yield service


StorageServiceDep = Annotated[StorageService, Depends(get_storage)]


def get_event_publisher(request: Request) -> EventPublisher:
    """Retrieve event publisher from application state."""
    publisher: EventPublisher = request.app.state.event_publisher
    return publisher


EventPublisherDep = Annotated[EventPublisher, Depends(get_event_publisher)]
