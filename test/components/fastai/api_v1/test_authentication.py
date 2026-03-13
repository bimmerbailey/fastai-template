import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlmodel.ext.asyncio.session import AsyncSession

from fastai.users.models import User

pytestmark = pytest.mark.integration

TEST_PASSWORD = "securepassword123"
COOKIE_NAME = "refresh_token"


@pytest_asyncio.fixture
async def registered_user(create_user) -> User:
    """Create a user for login/auth tests."""
    return await create_user(email="auth@example.com", password=TEST_PASSWORD)


def _extract_refresh_cookie(response) -> str:
    """Extract the refresh_token value from Set-Cookie headers."""
    for header_name, header_value in response.headers.multi_items():
        if header_name == "set-cookie" and header_value.startswith(f"{COOKIE_NAME}="):
            return header_value.split(";")[0].split("=", 1)[1]
    raise AssertionError("No refresh_token cookie found in response")


def _assert_cookie_is_httponly(response) -> None:
    """Assert the refresh token cookie has HttpOnly flag."""
    for header_name, header_value in response.headers.multi_items():
        if header_name == "set-cookie" and header_value.startswith(f"{COOKIE_NAME}="):
            assert "httponly" in header_value.lower()
            return
    raise AssertionError("No refresh_token cookie found in response")


async def _login(client: AsyncClient, email: str, password: str):
    """Helper to perform a login and return the response."""
    return await client.post(
        "/auth/login",
        data={"username": email, "password": password},
    )


class TestRegister:
    """Tests for POST /auth/register."""

    @pytest.mark.asyncio
    async def test_returns_201_with_access_token(
        self, api_v1_client: AsyncClient
    ) -> None:
        response = await api_v1_client.post(
            "/auth/register",
            json={
                "first_name": "New",
                "last_name": "User",
                "email": "newuser@example.com",
                "password": TEST_PASSWORD,
            },
        )

        assert response.status_code == 201
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"

    @pytest.mark.asyncio
    async def test_refresh_token_in_cookie_not_body(
        self, api_v1_client: AsyncClient
    ) -> None:
        response = await api_v1_client.post(
            "/auth/register",
            json={
                "first_name": "Cookie",
                "last_name": "User",
                "email": "cookie@example.com",
                "password": TEST_PASSWORD,
            },
        )

        assert "refresh_token" not in response.json()
        _extract_refresh_cookie(response)
        _assert_cookie_is_httponly(response)

    @pytest.mark.asyncio
    async def test_duplicate_email_returns_409(
        self, api_v1_client: AsyncClient, registered_user: User
    ) -> None:
        response = await api_v1_client.post(
            "/auth/register",
            json={
                "first_name": "Dup",
                "last_name": "User",
                "email": "auth@example.com",
                "password": TEST_PASSWORD,
            },
        )

        assert response.status_code == 409

    @pytest.mark.asyncio
    async def test_short_password_returns_422(self, api_v1_client: AsyncClient) -> None:
        response = await api_v1_client.post(
            "/auth/register",
            json={
                "first_name": "Weak",
                "last_name": "User",
                "email": "weak@example.com",
                "password": "short",
            },
        )

        assert response.status_code == 422


class TestLogin:
    """Tests for POST /auth/login."""

    @pytest.mark.asyncio
    async def test_returns_access_token_and_cookie(
        self, api_v1_client: AsyncClient, registered_user: User
    ) -> None:
        response = await _login(api_v1_client, "auth@example.com", TEST_PASSWORD)

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" not in data
        _extract_refresh_cookie(response)
        _assert_cookie_is_httponly(response)

    @pytest.mark.asyncio
    async def test_wrong_password_returns_401(
        self, api_v1_client: AsyncClient, registered_user: User
    ) -> None:
        response = await _login(api_v1_client, "auth@example.com", "wrongpassword123")

        assert response.status_code == 401
        assert "Invalid email or password" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_nonexistent_user_returns_401(
        self, api_v1_client: AsyncClient
    ) -> None:
        response = await _login(api_v1_client, "nobody@example.com", TEST_PASSWORD)

        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_locked_account_returns_423(
        self,
        api_v1_client: AsyncClient,
        registered_user: User,
        test_db_session: AsyncSession,
    ) -> None:
        for _ in range(5):
            await registered_user.record_login_failure(
                test_db_session, max_attempts=5, lockout_minutes=30
            )

        response = await _login(api_v1_client, "auth@example.com", TEST_PASSWORD)

        assert response.status_code == 423

    @pytest.mark.asyncio
    async def test_suspended_account_returns_403(
        self,
        api_v1_client: AsyncClient,
        registered_user: User,
        test_db_session: AsyncSession,
    ) -> None:
        from fastai.users.schemas import AccountStatus, UserUpdate

        await registered_user.update(
            test_db_session, UserUpdate(status=AccountStatus.SUSPENDED)
        )

        response = await _login(api_v1_client, "auth@example.com", TEST_PASSWORD)

        assert response.status_code == 403


class TestRefresh:
    """Tests for POST /auth/refresh."""

    @pytest.mark.asyncio
    async def test_rotates_tokens(
        self, api_v1_client: AsyncClient, registered_user: User
    ) -> None:

        login_response = await _login(api_v1_client, "auth@example.com", TEST_PASSWORD)
        refresh_token = _extract_refresh_cookie(login_response)

        api_v1_client.cookies.set("refresh_token", refresh_token, path="/auth")

        response = await api_v1_client.post("/auth/refresh")

        assert response.status_code == 200
        assert "access_token" in response.json()
        new_refresh = _extract_refresh_cookie(response)
        assert new_refresh != refresh_token

    @pytest.mark.asyncio
    async def test_missing_cookie_returns_401(self, api_v1_client: AsyncClient) -> None:
        response = await api_v1_client.post("/auth/refresh")

        assert response.status_code == 401
        assert "missing" in response.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_invalid_token_returns_401(self, api_v1_client: AsyncClient) -> None:
        response = await api_v1_client.post("/auth/refresh")
        api_v1_client.cookies.set("refresh_token", "garbage", path="/auth")

        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_reused_token_returns_401(
        self, api_v1_client: AsyncClient, registered_user: User
    ) -> None:
        login_response = await _login(api_v1_client, "auth@example.com", TEST_PASSWORD)
        refresh_token = _extract_refresh_cookie(login_response)

        api_v1_client.cookies.set("refresh_token", refresh_token, path="/auth")

        # First use succeeds (rotates the token)
        await api_v1_client.post("/auth/refresh")

        # Second use of the same token fails (reuse detection)
        response = await api_v1_client.post("/auth/refresh")

        assert response.status_code == 401
        assert "revoked" in response.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_access_token_as_refresh_fails(
        self, api_v1_client: AsyncClient, registered_user: User
    ) -> None:
        login_response = await _login(api_v1_client, "auth@example.com", TEST_PASSWORD)
        access_token = login_response.json()["access_token"]

        api_v1_client.cookies.set("refresh_token", access_token, path="/auth")

        response = await api_v1_client.post("/auth/refresh")

        assert response.status_code == 401


class TestLogout:
    """Tests for POST /auth/logout."""

    @pytest.mark.asyncio
    async def test_revokes_refresh_token(
        self, api_v1_client: AsyncClient, registered_user: User
    ) -> None:
        login_response = await _login(api_v1_client, "auth@example.com", TEST_PASSWORD)
        refresh_token = _extract_refresh_cookie(login_response)
        api_v1_client.cookies.set("refresh_token", refresh_token, path="/auth")

        response = await api_v1_client.post("/auth/logout")
        assert response.status_code == 204

        # Refresh with the revoked token should fail
        refresh_response = await api_v1_client.post("/auth/refresh")
        assert refresh_response.status_code == 401

    @pytest.mark.asyncio
    async def test_without_cookie_returns_204(self, api_v1_client: AsyncClient) -> None:
        response = await api_v1_client.post("/auth/logout")
        assert response.status_code == 204

    @pytest.mark.asyncio
    async def test_unknown_token_returns_204(self, api_v1_client: AsyncClient) -> None:
        api_v1_client.cookies.set("refresh_token", "unknown-token", path="/auth")
        response = await api_v1_client.post("/auth/logout")
        assert response.status_code == 204
