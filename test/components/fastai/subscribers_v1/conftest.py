import pytest

from fastai.extraction.core import ExtractionService


@pytest.fixture
def extraction_service() -> ExtractionService:
    """Create a real ExtractionService for integration tests.

    Requires docling to be installed (available in the worker project venv).
    """
    pytest.importorskip("docling")
    return ExtractionService()
