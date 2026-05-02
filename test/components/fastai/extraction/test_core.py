import pytest

from fastai.extraction import ExtractionService

pytestmark = pytest.mark.integration


@pytest.mark.asyncio
async def test_extract_text_markdown_simple() -> None:
    """ExtractionService can extract text from a markdown file."""
    pytest.importorskip("docling")
    service = ExtractionService()
    text = await service.extract_text(b"Hello, world!", "test.md")
    assert "Hello" in text


@pytest.mark.asyncio
async def test_extract_and_chunk_markdown() -> None:
    """ExtractionService chunks markdown into at least one chunk."""
    pytest.importorskip("docling")
    service = ExtractionService()
    chunks = await service.extract_and_chunk(b"Hello, world!", "test.md")
    assert len(chunks) >= 1
    assert any("Hello" in c for c in chunks)


@pytest.mark.asyncio
async def test_extract_text_markdown() -> None:
    """ExtractionService can extract text from a markdown file."""
    pytest.importorskip("docling")
    content = b"# Title\n\nSome paragraph text.\n\n## Subtitle\n\nMore text here."
    service = ExtractionService()
    text = await service.extract_text(content, "test.md")
    assert "Title" in text
    assert "paragraph" in text
