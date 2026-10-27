"""Password hashing helpers.

Uses PBKDF2-HMAC-SHA256 from the standard library, so no extra dependency is
required. Stored format: ``pbkdf2_sha256$<iterations>$<salt_hex>$<hash_hex>``.
"""

from __future__ import annotations

import hashlib
import hmac
import os

ALGORITHM = "pbkdf2_sha256"
ITERATIONS = 260_000
SALT_BYTES = 16


def hash_password(password: str) -> str:
    """Return a salted PBKDF2 hash for ``password``."""
    salt = os.urandom(SALT_BYTES)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, ITERATIONS)
    return f"{ALGORITHM}${ITERATIONS}${salt.hex()}${digest.hex()}"


def verify_password(password: str, stored: str | None) -> bool:
    """Check ``password`` against a stored hash.

    Rows created before hashing was introduced hold plain text; they are
    compared directly so restoring an old backup does not lock anyone out.
    """
    if not stored:
        return False

    if not stored.startswith(f"{ALGORITHM}$"):
        return hmac.compare_digest(stored, password)

    try:
        _, iterations, salt_hex, digest_hex = stored.split("$")
        digest = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            bytes.fromhex(salt_hex),
            int(iterations),
        )
    except (ValueError, TypeError):
        return False

    return hmac.compare_digest(digest.hex(), digest_hex)
