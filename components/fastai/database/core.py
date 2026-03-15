from typing import Any, AsyncIterator, Literal
from urllib.parse import parse_qs, urlparse

import structlog.stdlib
from pydantic import PostgresDsn, SecretStr, computed_field, model_validator
from pydantic_settings import SettingsConfigDict
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine
from sqlmodel import text
from sqlmodel.ext.asyncio.session import AsyncSession

from fastai.utils.settings import FastAISettings

SslMode = Literal["disable", "allow", "prefer", "require", "verify-ca", "verify-full"]


class PostgresSettings(FastAISettings):
    """PostgreSQL connection settings with two mutually exclusive modes:

    1. **Full URL** — set ``FASTAI_POSTGRES_URL`` with a provider connection
       string (Neon, Supabase, Heroku, AWS RDS, etc.). All parts are extracted
       automatically; individual field env vars are ignored.
    2. **Individual fields** — omit the URL and set ``FASTAI_POSTGRES_HOSTNAME``,
       ``_NAME``, ``_USER``, ``_PASSWORD``, etc. The DSN is built from these parts.
    """

    model_config = SettingsConfigDict(env_prefix="FASTAI_POSTGRES_")

    url: str | None = None
    hostname: str
    port: int = 5432
    name: str
    user: str
    password: SecretStr
    sslmode: SslMode = "prefer"
    options: str | None = None

    @model_validator(mode="before")
    @classmethod
    def extract_parts_from_url(cls, values: dict[str, Any]) -> dict[str, Any]:
        url = values.get("url")
        if not url:
            return values

        # Normalize postgres:// to postgresql:// for parsing
        if isinstance(url, str) and url.startswith("postgres://"):
            url = "postgresql://" + url[len("postgres://") :]

        parsed = urlparse(url)
        values["hostname"] = parsed.hostname
        values["port"] = parsed.port or 5432
        values["name"] = parsed.path.lstrip("/")
        values["user"] = parsed.username
        values["password"] = parsed.password

        # Extract known query params

        params = parse_qs(parsed.query)
        if "sslmode" in params:
            values["sslmode"] = params["sslmode"][0]
        if "options" in params:
            values["options"] = params["options"][0]

        return values

    @computed_field
    @property
    def dsn(self) -> PostgresDsn:
        query_parts: list[str] = []
        if self.sslmode != "prefer":
            query_parts.append(f"sslmode={self.sslmode}")
        if self.options:
            query_parts.append(f"options={self.options}")
        query = "&".join(query_parts)
        suffix = f"?{query}" if query else ""

        return PostgresDsn(
            f"postgresql+asyncpg://{self.user}:{self.password.get_secret_value()}@"
            f"{self.hostname}:{self.port}/{self.name}{suffix}"
        )


logger = structlog.stdlib.get_logger(__name__)


def create_db_engine(settings: PostgresSettings | None = None) -> AsyncEngine:

    if settings is None:
        settings = PostgresSettings()  # pyright: ignore[reportCallIssue]

    logger.info("Creating database engine")
    return create_async_engine(str(settings.dsn), pool_pre_ping=True)


async def destroy_engine(engine: AsyncEngine):
    logger.info("Destroying database engine")
    await engine.dispose()


async def get_db_session(engine: AsyncEngine) -> AsyncIterator[AsyncSession]:
    async with AsyncSession(engine) as session:
        try:
            yield session
            # await session.commit()
        except Exception:
            logger.exception("Failed to get session")
            await session.rollback()
            raise
        finally:
            await session.close()


async def health_check(session: AsyncSession):
    try:
        # Simple query to test database connectivity
        result = await session.exec(text("SELECT 1 as test"))  # pyright: ignore[reportCallIssue, reportArgumentType]
        row = result.fetchone()

        if row and row[0] == 1:
            return {"status": "ready"}
        else:
            return {"status": "not ready"}
    except Exception:
        logger.exception("Error in database health check")
        return {"status": "not ready"}
