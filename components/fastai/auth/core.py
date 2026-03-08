from __future__ import annotations

from pwdlib import PasswordHash
from pwdlib.hashers.argon2 import Argon2Hasher


class PasswordService:
    """Service for hashing and verifying passwords using Argon2id.

    Uses pwdlib with the recommended Argon2id configuration.
    Supports verify_and_update to re-hash when algorithm parameters change.
    """

    def __init__(self, hasher: PasswordHash | None = None) -> None:
        self._hasher = hasher or PasswordHash((Argon2Hasher(),))

    def hash(self, password: str) -> str:
        """Hash a plain-text password using Argon2id."""
        return self._hasher.hash(password)

    def verify(self, password: str, hashed: str) -> bool:
        """Verify a plain-text password against a hash."""
        return self._hasher.verify(password, hashed)

    def verify_and_update(self, password: str, hashed: str) -> tuple[bool, str | None]:
        """Verify a password and return an updated hash if parameters changed.

        Returns:
            A tuple of (is_valid, updated_hash). If the password is valid but
            the hash uses outdated parameters, updated_hash will contain the
            new hash. Otherwise updated_hash is None.
        """
        return self._hasher.verify_and_update(password, hashed)


# TODO: Remove this
# Module-level singleton for convenience.
# Components can import this directly or inject their own instance.
password_service = PasswordService()
