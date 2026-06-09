"""Hash y verificación de API keys (argon2)."""

from __future__ import annotations

from argon2 import PasswordHasher

_ph = PasswordHasher()


def hash_apikey(raw: str) -> str:
    return _ph.hash(raw)


def verify_apikey(raw: str, hashed: str) -> bool:
    try:
        return _ph.verify(hashed, raw)
    except Exception:
        return False
