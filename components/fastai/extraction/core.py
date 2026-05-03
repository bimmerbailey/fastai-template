# TODO: For garbled PDFs (broken ToUnicode CMap), add a vision LLM agent as
# a lightweight OCR fallback (pymupdf for page images + pydantic-ai). For
# DOCX/PPTX/XLSX/image extraction, docling can return as a separate
# sidecar/API (similar to Open-WebUI's architecture).
import asyncio
import os
from functools import partial
from io import BytesIO

import ftfy  # pyright: ignore[reportMissingImports]
import structlog.stdlib
from pypdf import PdfReader  # pyright: ignore[reportMissingImports]

logger = structlog.stdlib.get_logger(__name__)

# Separators used by the recursive character splitter, tried in order.
_SEPARATORS = ["\n\n", "\n", ". ", " ", ""]

_TEXT_EXTENSIONS = {".md", ".markdown", ".html", ".htm", ".txt", ".text"}


def _chunk_text(text: str, max_chars: int = 1500, overlap: int = 100) -> list[str]:
    """Split *text* into chunks using recursive character splitting.

    Tries splitting on paragraph boundaries first, then newlines, then
    sentences, then spaces, and finally hard character splits. Chunks
    include *overlap* characters from the end of the previous chunk to
    preserve context across boundaries.
    """
    text = text.strip()
    if not text:
        return []
    if len(text) <= max_chars:
        return [text]

    # Find the best separator that produces a split
    for sep in _SEPARATORS:
        if sep and sep not in text:
            continue
        parts = text.split(sep) if sep else list(text)
        if len(parts) <= 1 and sep:
            continue

        chunks: list[str] = []
        current = parts[0]
        for part in parts[1:]:
            candidate = current + sep + part if sep else current + part
            if len(candidate) <= max_chars:
                current = candidate
            else:
                if current.strip():
                    chunks.append(current.strip())
                # Start new chunk with overlap from the previous one
                if overlap and current:
                    tail = current[-overlap:]
                    current = tail + sep + part if sep else tail + part
                else:
                    current = part

        if current.strip():
            chunks.append(current.strip())

        if len(chunks) > 1:
            return chunks

    # Fallback: hard split (shouldn't normally reach here)
    return [text[i : i + max_chars] for i in range(0, len(text), max_chars - overlap)]


class ExtractionService:
    """Document text extraction and chunking using pypdf.

    Reuses lightweight pypdf readers per call (no model loading).
    Extraction runs in a thread executor to avoid blocking the event loop.
    """

    # ------------------------------------------------------------------
    # Extraction
    # ------------------------------------------------------------------

    @staticmethod
    def _extract_pdf(file_bytes: bytes) -> str:
        """Extract text from a PDF using pypdf."""
        reader = PdfReader(BytesIO(file_bytes))
        pages = [page.extract_text() or "" for page in reader.pages]
        return "\n\n".join(pages)

    @staticmethod
    def _extract_text_content(file_bytes: bytes) -> str:
        """Decode raw bytes as UTF-8 text."""
        return file_bytes.decode("utf-8", errors="replace")

    def _extract_sync(self, file_bytes: bytes, filename: str) -> str:
        """Synchronous text extraction, routed by file extension."""
        ext = os.path.splitext(filename)[1].lower()
        if ext == ".pdf":
            raw = self._extract_pdf(file_bytes)
        elif ext in _TEXT_EXTENSIONS:
            raw = self._extract_text_content(file_bytes)
        else:
            raw = self._extract_text_content(file_bytes)

        return ftfy.fix_text(raw)

    async def extract_text(self, file_bytes: bytes, filename: str) -> str:
        """Extract text from a document.

        Runs extraction in a thread executor since pypdf is synchronous.

        Args:
            file_bytes: The raw file content.
            filename: The filename (used to infer format).

        Returns:
            Extracted and cleaned text.
        """
        loop = asyncio.get_running_loop()
        text = await loop.run_in_executor(
            None,
            partial(self._extract_sync, file_bytes, filename),
        )
        logger.info("Extracted text", filename=filename, text_length=len(text))
        return text

    # ------------------------------------------------------------------
    # Chunking
    # ------------------------------------------------------------------

    def _chunk_sync(self, file_bytes: bytes, filename: str) -> list[str]:
        """Synchronous extraction + chunking."""
        text = self._extract_sync(file_bytes, filename)
        chunks = _chunk_text(text)
        return [c for c in chunks if c.strip()]

    async def extract_and_chunk(self, file_bytes: bytes, filename: str) -> list[str]:
        """Extract text and split into chunks for embedding.

        Uses recursive character splitting on paragraph, newline,
        and sentence boundaries.

        Args:
            file_bytes: The raw file content.
            filename: The filename (used to infer format).

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
