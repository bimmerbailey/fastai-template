import uuid
from datetime import timedelta, timezone

import pytest

from fastai.auth.settings import AuthSettings
from fastai.auth.token_service import TokenError, TokenService


@pytest.fixture
def auth_settings() -> AuthSettings:
    return AuthSettings(secret_key="test-secret-key-at-least-32-characters-long")


@pytest.fixture
def token_service(auth_settings: AuthSettings) -> TokenService:
    return TokenService(auth_settings)


@pytest.fixture
def user_id() -> uuid.UUID:
    return uuid.uuid4()


class TestCreateAccessToken:
    """Tests for access token creation."""

    def test_creates_valid_token(
        self, token_service: TokenService, user_id: uuid.UUID
    ) -> None:
        token = token_service.create_access_token(user_id)
        assert isinstance(token, str)
        assert len(token) > 0

    def test_token_contains_correct_claims(
        self, token_service: TokenService, user_id: uuid.UUID
    ) -> None:
        token = token_service.create_access_token(user_id, is_admin=True)
        payload = token_service.decode_access_token(token)

        assert payload.sub == str(user_id)
        assert payload.type == "access"
        assert payload.is_admin is True
        assert payload.iat is not None
        assert payload.exp is not None

    def test_default_is_admin_false(
        self, token_service: TokenService, user_id: uuid.UUID
    ) -> None:
        token = token_service.create_access_token(user_id)
        payload = token_service.decode_access_token(token)
        assert payload.is_admin is False

    def test_token_expires_in_configured_minutes(
        self,
        auth_settings: AuthSettings,
        token_service: TokenService,
        user_id: uuid.UUID,
    ) -> None:
        token = token_service.create_access_token(user_id)
        payload = token_service.decode_access_token(token)

        expected_delta = timedelta(minutes=auth_settings.access_token_expire_minutes)
        actual_delta = payload.exp - payload.iat
        # Allow 5 seconds of tolerance for test execution time
        assert abs(actual_delta - expected_delta) < timedelta(seconds=5)


class TestCreateRefreshToken:
    """Tests for refresh token creation."""

    def test_creates_valid_token(
        self, token_service: TokenService, user_id: uuid.UUID
    ) -> None:
        token = token_service.create_refresh_token(user_id)
        assert isinstance(token, str)
        assert len(token) > 0

    def test_token_contains_correct_claims(
        self, token_service: TokenService, user_id: uuid.UUID
    ) -> None:
        token = token_service.create_refresh_token(user_id)
        payload = token_service.decode_refresh_token(token)

        assert payload.sub == str(user_id)
        assert payload.type == "refresh"
        assert payload.is_admin is False

    def test_token_expires_in_configured_days(
        self,
        auth_settings: AuthSettings,
        token_service: TokenService,
        user_id: uuid.UUID,
    ) -> None:
        token = token_service.create_refresh_token(user_id)
        payload = token_service.decode_refresh_token(token)

        expected_delta = timedelta(days=auth_settings.refresh_token_expire_days)
        actual_delta = payload.exp - payload.iat
        assert abs(actual_delta - expected_delta) < timedelta(seconds=5)


class TestDecodeAccessToken:
    """Tests for access token decoding and validation."""

    def test_rejects_refresh_token(
        self, token_service: TokenService, user_id: uuid.UUID
    ) -> None:
        refresh = token_service.create_refresh_token(user_id)
        with pytest.raises(TokenError, match="invalid claim"):
            token_service.decode_access_token(refresh)

    def test_rejects_expired_token(self, user_id: uuid.UUID) -> None:
        """Create a token that is already expired by using joserfc directly."""
        from datetime import datetime

        from joserfc import jwt as jose_jwt
        from joserfc.jwk import OctKey

        secret = "test-secret-key-at-least-32-characters-long"
        key = OctKey.import_key(secret)
        now = datetime.now(tz=timezone.utc)

        # Create a token that expired 1 hour ago
        claims = {
            "sub": str(user_id),
            "type": "access",
            "is_admin": False,
            "iat": now - timedelta(hours=2),
            "exp": now - timedelta(hours=1),
        }
        expired_token = jose_jwt.encode({"alg": "HS256"}, claims, key)

        settings = AuthSettings(secret_key=secret)
        service = TokenService(settings)

        with pytest.raises(TokenError, match="expired"):
            service.decode_access_token(expired_token)

    def test_rejects_invalid_signature(
        self, token_service: TokenService, user_id: uuid.UUID
    ) -> None:
        token = token_service.create_access_token(user_id)

        # Create a different service with a different secret
        other_settings = AuthSettings(
            secret_key="different-secret-key-at-least-32-chars-long"
        )
        other_service = TokenService(other_settings)

        with pytest.raises(TokenError, match="Invalid token signature"):
            other_service.decode_access_token(token)

    def test_rejects_garbage_token(self, token_service: TokenService) -> None:
        with pytest.raises(TokenError):
            token_service.decode_access_token("not-a-real-token")


class TestDecodeRefreshToken:
    """Tests for refresh token decoding and validation."""

    def test_rejects_access_token(
        self, token_service: TokenService, user_id: uuid.UUID
    ) -> None:
        access = token_service.create_access_token(user_id)
        with pytest.raises(TokenError, match="invalid claim"):
            token_service.decode_refresh_token(access)

    def test_rejects_invalid_signature(
        self, token_service: TokenService, user_id: uuid.UUID
    ) -> None:
        token = token_service.create_refresh_token(user_id)

        other_settings = AuthSettings(
            secret_key="different-secret-key-at-least-32-chars-long"
        )
        other_service = TokenService(other_settings)

        with pytest.raises(TokenError, match="Invalid token signature"):
            other_service.decode_refresh_token(token)


class TestHashToken:
    """Tests for the static hash_token helper."""

    def test_produces_hex_digest(self) -> None:
        result = TokenService.hash_token("some-token")
        assert isinstance(result, str)
        assert len(result) == 64  # SHA-256 hex digest

    def test_deterministic(self) -> None:
        h1 = TokenService.hash_token("same-token")
        h2 = TokenService.hash_token("same-token")
        assert h1 == h2

    def test_different_tokens_different_hashes(self) -> None:
        h1 = TokenService.hash_token("token-a")
        h2 = TokenService.hash_token("token-b")
        assert h1 != h2
