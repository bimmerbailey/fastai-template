import uuid

import pytest
from faststream.nats import NatsBroker, TestNatsBroker

from fastai.events import DOCUMENT_STREAM, SUBJECT_DOCUMENT_UPLOADED, NatsSettings
from fastai.events.core import EventPublisher
from fastai.events.schemas import DocumentUploaded


@pytest.mark.asyncio
async def test_publish_document_uploaded() -> None:
    """EventPublisher publishes a DocumentUploaded event to the correct subject."""
    broker = NatsBroker()

    received: list[DocumentUploaded] = []

    @broker.subscriber(SUBJECT_DOCUMENT_UPLOADED, stream=DOCUMENT_STREAM)
    async def handler(event: DocumentUploaded) -> None:
        received.append(event)

    settings = NatsSettings()  # pyright: ignore[reportCallIssue]
    async with TestNatsBroker(broker) as br:
        publisher = EventPublisher(settings, broker=br)
        event = DocumentUploaded(
            document_id=uuid.uuid4(),
            storage_path="documents/test.pdf",
            content_type="application/pdf",
            filename="test.pdf",
        )
        await publisher.publish_document_uploaded(event)

    assert len(received) == 1
    assert received[0].filename == "test.pdf"
    assert received[0].content_type == "application/pdf"


@pytest.mark.asyncio
async def test_publish_preserves_document_id() -> None:
    """Published event preserves the document_id UUID."""
    broker = NatsBroker()
    doc_id = uuid.uuid4()

    received: list[DocumentUploaded] = []

    @broker.subscriber(SUBJECT_DOCUMENT_UPLOADED, stream=DOCUMENT_STREAM)
    async def handler(event: DocumentUploaded) -> None:
        received.append(event)

    settings = NatsSettings()  # pyright: ignore[reportCallIssue]
    async with TestNatsBroker(broker) as br:
        publisher = EventPublisher(settings, broker=br)
        event = DocumentUploaded(
            document_id=doc_id,
            storage_path="documents/test.pdf",
            content_type="application/pdf",
            filename="test.pdf",
        )
        await publisher.publish_document_uploaded(event)

    assert received[0].document_id == doc_id
