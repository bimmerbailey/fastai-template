from typing import Literal

from pydantic import Field, SecretStr
from pydantic_settings import SettingsConfigDict

from fastai.utils.settings import FastAISettings


class AuthSettings(FastAISettings):
    """JWT authentication settings.

    All values can be overridden via environment variables prefixed
    with ``AUTH_`` (e.g. ``AUTH_SECRET_KEY``, ``AUTH_ALGORITHM``).
    """

    model_config = SettingsConfigDict(env_prefix="FASTAI_AUTH_")

    secret_key: SecretStr = Field(
        ...,
        description=(
            "Secret key for signing JWTs. Must be at least 32 characters. "
            "Set via AUTH_SECRET_KEY environment variable."
        ),
    )
    algorithm: str = Field(
        default="HS256",
        description="JWT signing algorithm.",
    )
    access_token_expire_minutes: int = Field(
        default=15,
        gt=0,
        description="Access token lifetime in minutes.",
    )
    refresh_token_expire_days: int = Field(
        default=7,
        gt=0,
        description="Refresh token lifetime in days.",
    )
    max_failed_login_attempts: int = Field(
        default=5,
        gt=0,
        description="Number of consecutive failed logins before account lockout.",
    )
    lockout_duration_minutes: int = Field(
        default=30,
        gt=0,
        description="Duration of account lockout in minutes after max failed attempts.",
    )

    # Cookie settings for refresh tokens
    cookie_secure: bool = Field(
        default=True,
        description="Set Secure flag on refresh token cookie (requires HTTPS).",
    )
    cookie_samesite: Literal["lax", "strict", "none"] | None = Field(
        default="strict",
        description="SameSite attribute for refresh token cookie.",
    )
    cookie_path: str = Field(
        default="/auth",
        description="Path scope for the refresh token cookie.",
    )
    cookie_name: str = Field(
        default="refresh_token",
        description="Name of the refresh token cookie.",
    )
