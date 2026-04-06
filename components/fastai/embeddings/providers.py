from __future__ import annotations

import os
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Literal

import httpx
import structlog.stdlib

from pydantic_ai.embeddings import Embedder, EmbeddingModel, EmbeddingResult
from pydantic_ai.embeddings.settings import EmbeddingSettings as PAIEmbeddingSettings

from fastai.embeddings.settings import EmbeddingSettings

logger = structlog.stdlib.get_logger(__name__)

EmbedInputType = Literal["query", "document"]


# NOTE: This is a temporary stop-gap until it is OpenAI compatible
@dataclass(init=False)
class OllamaEmbeddingModel(EmbeddingModel):
    """Pydantic-AI compatible embedding model for Ollama's native /api/embed endpoint."""

    _model_name: str
    _base_url: str

    def __init__(
        self,
        model_name: str,
        *,
        base_url: str | None = None,
        settings: PAIEmbeddingSettings | None = None,
    ) -> None:
        self._model_name = model_name
        raw_url = base_url or os.environ.get(
            "OLLAMA_BASE_URL", "http://localhost:11434/v1"
        )
        # Strip /v1 suffix so we hit the native Ollama API, not the
        # OpenAI-compatible endpoint.  OLLAMA_BASE_URL typically includes /v1
        # because pydantic-ai's OllamaProvider requires it for chat models.
        self._base_url = raw_url.rstrip("/").removesuffix("/v1")
        super().__init__(settings=settings)

    @property
    def model_name(self) -> str:
        return self._model_name

    @property
    def system(self) -> str:
        return "ollama"

    @property
    def base_url(self) -> str | None:
        return self._base_url

    async def embed(
        self,
        inputs: str | Sequence[str],
        *,
        input_type: EmbedInputType,
        settings: PAIEmbeddingSettings | None = None,
    ) -> EmbeddingResult:
        texts, settings = self.prepare_embed(inputs, settings)

        url = f"{self._base_url}/api/embed"
        async with httpx.AsyncClient() as client:
            response = await client.post(
                url,
                json={"input": texts, "model": self._model_name},
                timeout=60.0,
            )
            response.raise_for_status()
            data = response.json()

        return EmbeddingResult(
            embeddings=data["embeddings"],
            inputs=texts,
            input_type=input_type,
            model_name=self.model_name,
            provider_name=self.system,
        )


def create_embedder(settings: EmbeddingSettings) -> Embedder:
    """Create a pydantic-ai Embedder from application settings.

    For OpenAI models, uses the built-in ``openai:model`` string.
    For Ollama models, creates a custom ``OllamaEmbeddingModel``.

    Args:
        settings: Application embedding configuration.

    Returns:
        A configured pydantic-ai Embedder.
    """
    model_str = settings.model
    provider, model_name = model_str.split(":", 1)

    pai_settings: PAIEmbeddingSettings | None = None
    if settings.dimensions:
        pai_settings = PAIEmbeddingSettings(dimensions=settings.dimensions)

    if provider == "ollama":
        model = OllamaEmbeddingModel(model_name, settings=pai_settings)
        return Embedder(model)

    # For OpenAI and other built-in providers, pass the full string directly.
    # pydantic-ai resolves "openai:text-embedding-3-small" natively.
    return Embedder(model_str, settings=pai_settings)
