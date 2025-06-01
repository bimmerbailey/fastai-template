import os

import structlog.stdlib
from pydantic import PostgresDsn, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine


class DatabaseSettings(BaseSettings):
    model_config = SettingsConfigDict(frozen=True, env_prefix="DATABASE_")

    hostname: str = "postgres"
    port: int = 27017
    name: str = "fastai"
    user: str = "postgres"
    password: SecretStr = "Password123!"

    @property
    def url(self) -> PostgresDsn:
        # TODO: There is probably a better way to do this
        if not os.environ.get("DATABASE_URL", None):
            return PostgresDsn(
                f"postgresql+asyncpg://{self.user}:{self.password.get_secret_value()}@"
                f"{self.hostname}:{self.port}/{self.name}"
            )
        return PostgresDsn(os.environ.get("DATABASE_URL"))


logger = structlog.stdlib.get_logger(__name__)


def create_db_engine(settings: DatabaseSettings = DatabaseSettings()) -> AsyncEngine:
    logger.info("Creating database engine")
    return create_async_engine(str(settings.url), pool_pre_ping=True)


async def destroy_engine(engine: AsyncEngine):
    logger.info("Destroying database engine")
    await engine.dispose()
