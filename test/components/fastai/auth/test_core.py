import pytest

from fastai.auth.core import PasswordService


@pytest.fixture
def hasher() -> PasswordService:
    return PasswordService()


class TestPasswordService:
    """Unit tests for the PasswordService — no database required."""

    def test_hash_returns_different_string(self, hasher: PasswordService) -> None:
        hashed = hasher.hash("mysecretpassword")
        assert hashed != "mysecretpassword"
        assert len(hashed) > 0

    def test_hash_is_not_deterministic(self, hasher: PasswordService) -> None:
        """Two hashes of the same password should differ (unique salt)."""
        h1 = hasher.hash("mysecretpassword")
        h2 = hasher.hash("mysecretpassword")
        assert h1 != h2

    def test_verify_correct_password(self, hasher: PasswordService) -> None:
        hashed = hasher.hash("correctpassword")
        assert hasher.verify("correctpassword", hashed) is True

    def test_verify_wrong_password(self, hasher: PasswordService) -> None:
        hashed = hasher.hash("correctpassword")
        assert hasher.verify("wrongpassword", hashed) is False

    def test_verify_and_update_valid(self, hasher: PasswordService) -> None:
        hashed = hasher.hash("mypassword")
        is_valid, updated = hasher.verify_and_update("mypassword", hashed)
        assert is_valid is True
        # When the hash parameters haven't changed, updated should be None
        assert updated is None

    def test_verify_and_update_invalid(self, hasher: PasswordService) -> None:
        hashed = hasher.hash("mypassword")
        is_valid, updated = hasher.verify_and_update("wrongpassword", hashed)
        assert is_valid is False
        assert updated is None

    def test_hash_contains_argon2_marker(self, hasher: PasswordService) -> None:
        """Verify the hash uses Argon2id algorithm."""
        hashed = hasher.hash("testpassword")
        assert "$argon2id$" in hashed
