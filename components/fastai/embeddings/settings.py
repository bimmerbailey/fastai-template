from pydantic import Field
from pydantic_settings import SettingsConfigDict

from fastai.utils.settings import FastAISettings


class EmbeddingSettings(FastAISettings):
    """Settings for the embedding service.

    API keys are handled by the respective provider SDKs
    via their own environment variables (e.g. OPENAI_API_KEY).
    This class only controls embedding-level configuration.
    """

    model_config = SettingsConfigDict(env_prefix="FASTAI_EMBEDDING_")

    model: str = Field(
        default="openai:text-embedding-3-small",
        description=(
            "Embedding model in provider:model format. "
            "Examples: 'openai:text-embedding-3-small', "
            "'ollama:nomic-embed-text'"
        ),
    )
    dimensions: int = Field(
        default=1536,
        gt=0,
        description=(
            "Vector dimensions. Must match the model's output size. "
            "Changing this after data exists requires a database migration "
            "to alter the HALFVEC column."
        ),
    )
    batch_size: int = Field(
        default=100,
        gt=0,
        description="Max texts per embedding API call.",
    )
