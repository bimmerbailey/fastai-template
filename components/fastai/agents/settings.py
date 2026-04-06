from pydantic import Field
from pydantic_settings import SettingsConfigDict

from fastai.utils.settings import FastAISettings


class AgentSettings(FastAISettings):
    """Settings for the AI agent.

    Model API keys are handled by the respective provider SDKs
    via their own environment variables (e.g. OPENAI_API_KEY,
    ANTHROPIC_API_KEY). This class only controls agent-level
    configuration.
    """

    model_config = SettingsConfigDict(env_prefix="FASTAI_AGENT_")

    model: str = Field(
        default="openai:gpt-5.4-nano",
        description=(
            "Model identifier in provider:model format. "
            "Examples: 'openai:gpt-4o', 'anthropic:claude-sonnet-4-20250514', "
            "'openrouter:meta-llama/llama-3-70b-instruct'"
        ),
    )
    temperature: float = Field(
        default=0.7,
        ge=0.0,
        le=2.0,
        description="Sampling temperature for the model.",
    )
    max_tokens: int = Field(
        default=4096,
        gt=0,
        description="Maximum number of tokens in the model response.",
    )
    request_limit: int = Field(
        default=10,
        gt=0,
        description="Maximum number of LLM requests per agent run.",
    )
    timeout: int = Field(
        default=30,
        gt=0,
        description="Request timeout in seconds.",
    )
