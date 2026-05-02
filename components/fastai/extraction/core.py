import asyncio
from functools import partial
from io import BytesIO

import structlog.stdlib
from docling.datamodel.base_models import (
    DocumentStream,  # pyright: ignore[reportMissingImports]
)
from docling.document_converter import (
    DocumentConverter,  # pyright: ignore[reportMissingImports]
)
from docling_core.transforms.chunker.hierarchical_chunker import (  # pyright: ignore[reportMissingImports]
    HierarchicalChunker,
)

logger = structlog.stdlib.get_logger(__name__)


class ExtractionService:
    """Document text extraction and chunking using docling.

    Reuses a single DocumentConverter instance to avoid reloading
    models on every call. Docling is synchronous, so extraction runs
    in a thread executor.
    """

    def __init__(self) -> None:

        self._converter = DocumentConverter()
        self._chunker = HierarchicalChunker()

    def _extract_sync(self, file_bytes: bytes, filename: str) -> str:
        """Synchronous text extraction via docling."""

        source = DocumentStream(name=filename, stream=BytesIO(file_bytes))
        result = self._converter.convert(source)
        return result.document.export_to_markdown()

    async def extract_text(self, file_bytes: bytes, filename: str) -> str:
        """Extract text from a document. Returns markdown text.

        Runs docling in a thread executor since it is synchronous.

        Args:
            file_bytes: The raw file content.
            filename: The filename (used by docling to infer format).

        Returns:
            Extracted text in markdown format.
        """
        loop = asyncio.get_running_loop()
        text = await loop.run_in_executor(
            None,
            partial(self._extract_sync, file_bytes, filename),
        )
        logger.info("Extracted text", filename=filename, text_length=len(text))
        return text

    def _chunk_sync(self, file_bytes: bytes, filename: str) -> list[str]:
        """Synchronous extraction + chunking."""

        source = DocumentStream(name=filename, stream=BytesIO(file_bytes))
        result = self._converter.convert(source)
        chunks = list(self._chunker.chunk(result.document))
        return [chunk.text for chunk in chunks]

    async def extract_and_chunk(self, file_bytes: bytes, filename: str) -> list[str]:
        """Extract text and split into chunks for embedding.

        Uses docling's HierarchicalChunker for intelligent splitting
        that respects document structure.

        Args:
            file_bytes: The raw file content.
            filename: The filename (used by docling to infer format).

        Returns:
            A list of text chunks suitable for embedding.
        """
        loop = asyncio.get_running_loop()
        chunks = await loop.run_in_executor(
            None,
            partial(self._chunk_sync, file_bytes, filename),
        )
        logger.info(
            "Extracted and chunked document",
            filename=filename,
            chunk_count=len(chunks),
        )
        return chunks
