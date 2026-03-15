from pydantic_settings import BaseSettings, SettingsConfigDict


class FastAISettings(BaseSettings):
    model_config = SettingsConfigDict(
        frozen=True,
        env_file=(".env", "example.env"),
        extra="ignore",
    )
