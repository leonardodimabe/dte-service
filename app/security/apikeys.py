"""Hash y verificación de API keys (argon2)."""

from __future__ import annotations

import secrets

from argon2 import PasswordHasher


def generate_apikey(nbytes: int = 32) -> str:
    """Genera una API key aleatoria URL-safe (se devuelve UNA vez; se guarda hasheada)."""
    return secrets.token_urlsafe(nbytes)


_ph = PasswordHasher()
# Hash señuelo para igualar el tiempo de respuesta cuando el (cliente, servicio)
# no existe (evita enumeración de customerCode por timing).
_DUMMY_HASH = _ph.hash("dummy-apikey-for-constant-time")


def hash_apikey(raw: str) -> str:
    return _ph.hash(raw)


def verify_apikey(raw: str, hashed: str) -> bool:
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
