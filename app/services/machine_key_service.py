"""Gestión de claves de máquina (consumidores tipo Odoo) para /admin.

Cada clave es ``<key_id>.<secret>``: ``key_id`` es un prefijo público indexado
y ``secret`` se guarda hasheado (argon2). En autenticación se ubica la fila por
``key_id`` y se verifica un único hash (O(1), sin recorrer todas las claves).
"""

from __future__ import annotations

import secrets

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import MachineKey
from app.security.apikeys import hash_apikey, verify_apikey
from app.security.roles import Role


class MachineKeyError(Exception):
    """Error de gestión de claves de máquina (se mapea a 4xx en el router)."""


# Una máquina nunca es superadmin: solo operador (escritura) o auditor (lectura).
_MACHINE_ROLES = {str(Role.OPERATOR), str(Role.AUDITOR)}


def create_key(db: Session, name: str, role: str, *, commit: bool = True) -> tuple[MachineKey, str]:
    """Crea una clave y devuelve (fila, clave_en_claro). El claro se ve UNA vez."""
    if role not in _MACHINE_ROLES:
        raise MachineKeyError(f"rol inválido para máquina: {role}")
    key_id = secrets.token_hex(8)
    secret = secrets.token_urlsafe(32)
    row = MachineKey(name=name, key_id=key_id, secret_hash=hash_apikey(secret), role=role)
    db.add(row)
    db.flush()
    db.refresh(row)
    if commit:
        db.commit()
    return row, f"{key_id}.{secret}"


def authenticate(db: Session, presented: str) -> MachineKey | None:
    """Valida una clave ``<key_id>.<secret>``. Devuelve la fila o None."""
    if "." not in presented:
        return None
    key_id, _, secret = presented.partition(".")
    row = db.execute(select(MachineKey).where(MachineKey.key_id == key_id)).scalar_one_or_none()
    if row is None or not row.is_active:
        return None
    if not verify_apikey(secret, row.secret_hash):
        return None
    return row


def list_keys(db: Session, *, limit: int = 100, offset: int = 0) -> list[MachineKey]:
    return list(
        db.execute(select(MachineKey).order_by(MachineKey.id).limit(limit).offset(offset)).scalars()
    )


def revoke(db: Session, mk_id: int, *, commit: bool = True) -> MachineKey | None:
    """Desactiva la clave (no borra: preserva trazabilidad). None si no existe."""
    row = db.get(MachineKey, mk_id)
    if row is None:
        return None
    row.is_active = False
    db.flush()
    db.refresh(row)
    if commit:
        db.commit()
    return row
