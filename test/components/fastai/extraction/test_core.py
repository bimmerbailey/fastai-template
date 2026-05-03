import pytest

from fastai.extraction.core import ExtractionService, _chunk_text

pytestmark = pytest.mark.integration


@pytest.mark.asyncio
async def test_extract_text_markdown_simple() -> None:
    """ExtractionService can extract text from a markdown file."""
    service = ExtractionService()
    text = await service.extract_text(b"Hello, world!", "test.md")
    assert "Hello" in text


@pytest.mark.asyncio
async def test_extract_and_chunk_markdown() -> None:
    """ExtractionService chunks markdown into at least one chunk."""
    service = ExtractionService()
    chunks = await service.extract_and_chunk(b"Hello, world!", "test.md")
    assert len(chunks) >= 1
    assert any("Hello" in c for c in chunks)


@pytest.mark.asyncio
async def test_extract_text_markdown() -> None:
    """ExtractionService can extract text from a markdown file."""
    content = b"# Title\n\nSome paragraph text.\n\n## Subtitle\n\nMore text here."
    service = ExtractionService()
    text = await service.extract_text(content, "test.md")
    assert "Title" in text
    assert "paragraph" in text


def test_chunk_text_splits_on_paragraphs() -> None:
    """Chunks are split on paragraph boundaries."""
    text = "First paragraph.\n\nSecond paragraph.\n\nThird paragraph."
    chunks = _chunk_text(text, max_chars=30, overlap=0)
    assert len(chunks) >= 2
    assert any("First" in c for c in chunks)
    assert any("Third" in c for c in chunks)


def test_chunk_text_respects_max_chars() -> None:
    """No chunk exceeds max_chars (except when a single word is longer)."""
    text = "Short sentence. " * 100
    chunks = _chunk_text(text, max_chars=50, overlap=0)
    assert all(len(c) <= 50 for c in chunks)


def test_chunk_text_single_chunk() -> None:
    """Short text returns a single chunk."""
    text = "Hello, world!"
    chunks = _chunk_text(text, max_chars=1500, overlap=100)
    assert chunks == ["Hello, world!"]


def test_chunk_text_empty() -> None:
    """Empty text returns no chunks."""
    assert _chunk_text("") == []
    assert _chunk_text("   ") == []
