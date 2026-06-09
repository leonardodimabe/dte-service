"""Autenticación de usuarios del portal (JWT) + dependencias de RBAC."""

from __future__ import annotations

from collections.abc import Awaitable, Callable

from fastapi import Depends, Header, HTTPException, Request
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.security import decode_access_token
from app.db.models import User
from app.db.session import get_db
from app.security.roles import ADMIN_ROLES, WRITE_ROLES, Role


async def get_current_user(
    request: Request,
    authorization: str = Header(default=""),
    db: Session = Depends(get_db),
) -> User:
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="falta token Bearer")
    try:
        payload = decode_access_token(authorization[7:])
    except Exception as ex:
        raise HTTPException(status_code=401, detail="token inválido o expirado") from ex

    user = db.get(User, int(payload["sub"]))
    if user is None or not user.is_active:
        raise HTTPException(status_code=401, detail="usuario inexistente o inactivo")
    request.state.principal = ("user", user.id, user.role)
    return user


def require_roles(*roles: str) -> Callable[..., Awaitable[User]]:
    allowed = {str(r) for r in roles}

    async def _dep(user: User = Depends(get_current_user)) -> User:
        if user.role not in allowed:
            raise HTTPException(status_code=403, detail="permiso insuficiente")
        return user

    return _dep


require_superadmin = require_roles(Role.SUPERADMIN)
require_write = require_roles(*WRITE_ROLES)  # superadmin + operator
require_admin_panel = require_roles(*ADMIN_ROLES)  # cualquier rol interno


async def _admin_principal(
    request: Request, authorization: str, x_admin_key: str, db: Session, allowed: set[str]
) -> User | None:
    """Resuelve el principal de /admin: JWT con rol en ``allowed`` **o** la
    X-Admin-Key de máquina. Devuelve el ``User`` (JWT) o ``None`` (máquina)."""
    if x_admin_key and x_admin_key == get_settings().admin_api_key:
        request.state.principal = ("system", None, "admin")
        return None
    if authorization.startswith("Bearer "):
        try:
            payload = decode_access_token(authorization[7:])
        except Exception as ex:
            raise HTTPException(status_code=401, detail="token inválido o expirado") from ex
        user = db.get(User, int(payload["sub"]))
        if user is None or not user.is_active:
            raise HTTPException(status_code=401, detail="usuario inexistente o inactivo")
        if user.role not in allowed:
            raise HTTPException(status_code=403, detail="permiso insuficiente")
        request.state.principal = ("user", user.id, user.role)
        return user
    raise HTTPException(status_code=401, detail="falta autenticación (Bearer o X-Admin-Key)")


async def admin_access(
    request: Request,
    authorization: str = Header(default=""),
    x_admin_key: str = Header(default="", alias="X-Admin-Key"),
    db: Session = Depends(get_db),
) -> User | None:
    """Escritura en /admin: rol superadmin/operator (JWT) o X-Admin-Key (máquina)."""
    return await _admin_principal(
        request, authorization, x_admin_key, db, {str(r) for r in WRITE_ROLES}
    )


async def admin_read_access(
    request: Request,
    authorization: str = Header(default=""),
    x_admin_key: str = Header(default="", alias="X-Admin-Key"),
    db: Session = Depends(get_db),
) -> User | None:
    """Lectura en /admin: cualquier rol interno (incluye auditor) o X-Admin-Key."""
    return await _admin_principal(
        request, authorization, x_admin_key, db, {str(r) for r in ADMIN_ROLES}
    )
