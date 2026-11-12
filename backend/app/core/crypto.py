"""Encryption for secrets at rest (OAuth refresh tokens, API credentials).

Tokens are encrypted with Fernet (AES-128-CBC + HMAC) using ENCRYPTION_KEY.
If no key is configured the application refuses to persist a secret rather
than writing plaintext - a missing key is a configuration error, not a
reason to downgrade security.
"""

from __future__ import annotations

import base64
import hashlib

from cryptography.fernet import Fernet, InvalidToken

from app.core.config import settings


class EncryptionNotConfigured(RuntimeError):
    pass


def _fernet() -> Fernet:
    key = settings.encryption_key
    if not key:
        if settings.environment in ("development", "test"):
            # Deterministic dev-only key derived from SECRET_KEY so local work
            # does not require extra setup. Never used in staging/production.
            digest = hashlib.sha256(settings.secret_key.encode()).digest()
            key = base64.urlsafe_b64encode(digest).decode()
        else:
            raise EncryptionNotConfigured(
                "ENCRYPTION_KEY is required to store credentials in "
                f"{settings.environment}. Generate one with: python -c "
                '"from cryptography.fernet import Fernet;'
                'print(Fernet.generate_key().decode())"'
            )
    return Fernet(key.encode() if isinstance(key, str) else key)


def encrypt(plaintext: str) -> str:
    return _fernet().encrypt(plaintext.encode()).decode()


def decrypt(ciphertext: str) -> str:
    try:
        return _fernet().decrypt(ciphertext.encode()).decode()
    except InvalidToken as exc:  # pragma: no cover - key rotation path
        raise EncryptionNotConfigured(
            "Stored credential could not be decrypted: ENCRYPTION_KEY changed."
        ) from exc


def mask(value: str | None, keep: int = 4) -> str:
    if not value:
        return ""
    if len(value) <= keep:
        return "*" * len(value)
    return "*" * (len(value) - keep) + value[-keep:]
