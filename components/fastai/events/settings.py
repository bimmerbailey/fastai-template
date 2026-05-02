import logging

from faststream.nats import JStream, NatsBroker
from pydantic_settings import SettingsConfigDict

from fastai.utils.settings import FastAISettings

# Subject constants — domain contract shared by publisher and subscriber
SUBJECT_DOCUMENT_UPLOADED = "document.uploaded"
SUBJECT_DOCUMENT_DELETED = "document.deleted"

# Default stream for subscriber decorators (must exist at import time)
DOCUMENT_STREAM = JStream(name="documents")


class NatsSettings(FastAISettings):
    """NATS connection settings.

    Configure via environment variables prefixed with ``FASTAI_NATS_``.
    """

    model_config = SettingsConfigDict(env_prefix="FASTAI_NATS_")

    url: str = "nats://localhost:4222"
    stream_name: str = "documents"

    def create_broker(self) -> NatsBroker:
        """Create a NatsBroker from these settings."""
        logger = logging.getLogger("faststream.access")
        return NatsBroker(
            self.url,
            logger=logger,
        )

    def create_stream(self) -> JStream:
        """Create a JetStream stream from these settings."""
        return JStream(name=self.stream_name)
