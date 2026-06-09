"""Emisión y verificación de tokens JWT (acceso) del portal."""

from __future__ import annotations

import datetime as dt

import jwt

from app.core.config import get_settings

_ALGORITHM = "HS256"


def create_access_token(user_id: int, role: str, customer_id: int | None) -> str:
    settings = get_settings()
    now = dt.datetime.now(dt.UTC)
    payload = {
        "sub": str(user_id),
        "role": role,
        "cid": customer_id,
        "iat": now,
        "exp": now + dt.timedelta(minutes=settings.jwt_expire_minutes),
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=_ALGORITHM)


def decode_access_token(token: str) -> dict:
    return jwt.decode(token, get_settings().jwt_secret, algorithms=[_ALGORITHM])
