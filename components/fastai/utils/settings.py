from pydantic_settings import BaseSettings, SettingsConfigDict


class FastAISettings(BaseSettings):
    model_config = SettingsConfigDict(
        frozen=True,
        env_file=("example.env", ".env"),
        extra="ignore",
    )
