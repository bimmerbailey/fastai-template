from typing import Self

import structlog.stdlib
from faststream.nats import NatsBroker

from fastai.events.schemas import DocumentDeleted, DocumentUploaded
from fastai.events.settings import (
    SUBJECT_DOCUMENT_DELETED,
    SUBJECT_DOCUMENT_UPLOADED,
    NatsSettings,
)

logger = structlog.stdlib.get_logger(__name__)


class EventPublisher:
    """Publishes domain events to NATS JetStream.

    Must be used as an async context manager to manage broker lifecycle::

        async with EventPublisher(settings) as publisher:
            await publisher.publish_document_uploaded(event)
    """

    def __init__(
        self, settings: NatsSettings, *, broker: NatsBroker | None = None
    ) -> None:
        self._settings = settings
        self._broker = broker or settings.create_broker()
        self._stream = settings.create_stream()

    async def __aenter__(self) -> Self:
        await self._broker.start()
        return self

    async def __aexit__(self, *exc_info: object) -> None:
        await self._broker.stop()

    async def publish_document_uploaded(self, event: DocumentUploaded) -> None:
        """Publish a DocumentUploaded event."""
        await self._broker.publish(
            event,
            subject=SUBJECT_DOCUMENT_UPLOADED,
            stream=self._stream.name,
        )
        logger.info(
            "Published document.uploaded event",
            document_id=str(event.document_id),
        )

    async def publish_document_deleted(self, event: DocumentDeleted) -> None:
        """Publish a DocumentDeleted event."""
        await self._broker.publish(
            event,
            subject=SUBJECT_DOCUMENT_DELETED,
            stream=self._stream.name,
        )
        logger.info(
            "Published document.deleted event",
            document_id=str(event.document_id),
        )
