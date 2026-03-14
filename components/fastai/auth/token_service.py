from __future__ import annotations

import hashlib
import uuid
from datetime import datetime, timedelta, timezone

from joserfc import jwt
from joserfc.errors import (
    BadSignatureError,
    ExpiredTokenError,
    InvalidClaimError,
    MissingClaimError,
)
from joserfc.jwk import OctKey
from joserfc.jwt import JWTClaimsRegistry

from fastai.auth.schemas import TokenPayload
from fastai.auth.settings import AuthSettings


class TokenError(Exception):
    """Raised when a token cannot be created, decoded, or validated."""

    def __init__(self, detail: str) -> None:
        self.detail = detail
        super().__init__(detail)


class TokenService:
    """JWT token creation and validation using joserfc.

    Produces short-lived access tokens and longer-lived refresh tokens,
    both signed with HS256. Refresh tokens are meant to be stored as
    SHA-256 hashes in the database for server-side revocation.
    """

    def __init__(self, settings: AuthSettings) -> None:
        self._settings = settings
        self._key = OctKey.import_key(settings.secret_key.get_secret_value())

    def create_access_token(
        self, user_id: uuid.UUID, *, scopes: list[str] | None = None
    ) -> str:
        """Create a short-lived access token."""
        now = datetime.now(tz=timezone.utc)
        claims = {
            "jti": str(uuid.uuid4()),
            "sub": str(user_id),
            "type": "access",
            "scopes": scopes or [],
            "iat": now,
            "exp": now + timedelta(minutes=self._settings.access_token_expire_minutes),
        }
        header = {"alg": self._settings.algorithm}
        return jwt.encode(header, claims, self._key)

    def create_refresh_token(self, user_id: uuid.UUID) -> str:
        """Create a long-lived refresh token."""
        now = datetime.now(tz=timezone.utc)
        claims = {
            "jti": str(uuid.uuid4()),
            "sub": str(user_id),
            "type": "refresh",
            "scopes": [],
            "iat": now,
            "exp": now + timedelta(days=self._settings.refresh_token_expire_days),
        }
        header = {"alg": self._settings.algorithm}
        return jwt.encode(header, claims, self._key)

    def decode_access_token(self, token: str) -> TokenPayload:
        """Decode and validate an access token.

        Raises:
            TokenError: If the token is invalid, expired, or not an access token.
        """
        return self._decode(token, expected_type="access")

    def decode_refresh_token(self, token: str) -> TokenPayload:
        """Decode and validate a refresh token.

        Raises:
            TokenError: If the token is invalid, expired, or not a refresh token.
        """
        return self._decode(token, expected_type="refresh")

    def _decode(self, token: str, *, expected_type: str) -> TokenPayload:
        """Internal decode + validate helper."""
        try:
            decoded = jwt.decode(token, self._key)
        except BadSignatureError:
            raise TokenError("Invalid token signature.")
        except Exception:
            raise TokenError("Token could not be decoded.")

        # Validate standard claims (exp, iat) and required custom claims
        registry = JWTClaimsRegistry(
            leeway=30,
            sub={"essential": True},
            type={"essential": True, "value": expected_type},
        )
        try:
            registry.validate(decoded.claims)
        except ExpiredTokenError:
            raise TokenError("Token has expired.")
        except MissingClaimError as exc:
            raise TokenError(f"Token is missing required claim: {exc.claim}.")
        except InvalidClaimError as exc:
            raise TokenError(f"Token has invalid claim: {exc.claim}.")

        return TokenPayload(
            sub=decoded.claims["sub"],
            type=decoded.claims["type"],
            exp=datetime.fromtimestamp(decoded.claims["exp"], tz=timezone.utc),
            iat=datetime.fromtimestamp(decoded.claims["iat"], tz=timezone.utc),
            scopes=decoded.claims.get("scopes", []),
        )

    @staticmethod
    def hash_token(token: str) -> str:
        """Return the SHA-256 hex digest of a token string.

        Used to store refresh tokens in the database without keeping
        the raw JWT, similar to how passwords are hashed before storage.
        """
        return hashlib.sha256(token.encode()).hexdigest()
