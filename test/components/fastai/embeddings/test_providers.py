import pytest
from pydantic_ai.embeddings import Embedder

from fastai.embeddings.providers import OllamaEmbeddingModel, create_embedder
from fastai.embeddings.settings import EmbeddingSettings


class TestOllamaEmbeddingModel:
    """Tests for the custom Ollama embedding model."""

    def test_model_name(self) -> None:
        model = OllamaEmbeddingModel("nomic-embed-text")
        assert model.model_name == "nomic-embed-text"

    def test_system(self) -> None:
        model = OllamaEmbeddingModel("nomic-embed-text")
        assert model.system == "ollama"

    def test_base_url_strips_v1(self) -> None:
        model = OllamaEmbeddingModel(
            "nomic-embed-text", base_url="http://localhost:11434/v1"
        )
        assert model.base_url == "http://localhost:11434"

    def test_base_url_without_v1(self) -> None:
        model = OllamaEmbeddingModel(
            "nomic-embed-text", base_url="http://localhost:11434"
        )
        assert model.base_url == "http://localhost:11434"

    def test_base_url_from_env(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("OLLAMA_BASE_URL", "http://custom:11434/v1")
        model = OllamaEmbeddingModel("nomic-embed-text")
        assert model.base_url == "http://custom:11434"


class TestCreateEmbedder:
    """Tests for the embedder factory."""

    def test_create_openai_embedder(self) -> None:
        settings = EmbeddingSettings(
            model="openai:text-embedding-3-small", dimensions=1536
        )
        embedder = create_embedder(settings)
        assert isinstance(embedder, Embedder)

    def test_create_ollama_embedder(self) -> None:
        settings = EmbeddingSettings(model="ollama:nomic-embed-text", dimensions=768)
        embedder = create_embedder(settings)
        assert isinstance(embedder, Embedder)
        assert isinstance(embedder.model, OllamaEmbeddingModel)
        assert embedder.model.model_name == "nomic-embed-text"
