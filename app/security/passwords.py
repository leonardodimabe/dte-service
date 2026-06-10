"""Hash y verificación de passwords de usuarios del portal (argon2)."""

from __future__ import annotations

from argon2 import PasswordHasher

_ph = PasswordHasher()
# Hash señuelo para igualar el tiempo de respuesta cuando el usuario no existe
# (evita enumeración de emails por timing).
_DUMMY_HASH = _ph.hash("dummy-password-for-constant-time")


def hash_password(raw: str) -> str:
    return _ph.hash(raw)


def verify_password(raw: str, hashed: str) -> bool:
    try:
        return _ph.verify(hashed, raw)
    except Exception:
        return False


def dummy_verify() -> None:
    """Ejecuta un verify contra un hash señuelo (gasta el tiempo de argon2)."""
    try:
        _ph.verify(_DUMMY_HASH, "wrong")
    except Exception:
        pass
