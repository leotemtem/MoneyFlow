# SPDX-License-Identifier: MIT
"""Password hashing for MoneyFlow.

Uses Argon2id (the current OWASP-recommended password KDF) via ``argon2-cffi``.
Hashes embed a per-password random salt and the cost parameters, so passwords
are never stored in plaintext and never hashed with a fast, unsalted digest.
"""

from __future__ import annotations

from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError, VerifyMismatchError

_hasher = PasswordHasher()


def hash_password(password: str) -> str:
    """Return an Argon2id hash (salt + parameters embedded) for a plaintext password."""
    return _hasher.hash(password)


def verify_password(stored_hash: str | None, password: str) -> bool:
    """Return True if ``password`` matches ``stored_hash``. Never raises."""
    if not stored_hash:
        return False
    try:
        return _hasher.verify(stored_hash, password)
    except (VerifyMismatchError, VerificationError, InvalidHashError):
        return False


def needs_rehash(stored_hash: str) -> bool:
    """True if the stored hash should be re-computed with current parameters."""
    try:
        return _hasher.check_needs_rehash(stored_hash)
    except (InvalidHashError, ValueError):
        return False
