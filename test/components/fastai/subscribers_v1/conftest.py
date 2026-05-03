import pytest

from fastai.extraction.core import ExtractionService


@pytest.fixture
def extraction_service() -> ExtractionService:
    """Create a real ExtractionService for integration tests."""
    return ExtractionService()
