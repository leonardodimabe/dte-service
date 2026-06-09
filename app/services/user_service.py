"""Gestión de usuarios del portal (admin + cliente) + seed de superadmin."""

from __future__ import annotations

import datetime as dt

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db.models import User
from app.security.passwords import hash_password, verify_password
from app.security.roles import Role


class UserError(Exception):
    """Error de gestión de usuarios (se mapea a 4xx en el router)."""


def authenticate(db: Session, email: str, password: str) -> User | None:
    user = db.execute(select(User).where(User.email == email.lower())).scalar_one_or_none()
    if user is None or not user.is_active or not verify_password(password, user.password_hash):
        return None
    user.last_login = dt.datetime.now(dt.UTC).replace(tzinfo=None)
    db.commit()
    return user


def create_user(db: Session, email: str, password: str, role: str, customer_id: int | None) -> User:
    if role not in {str(r) for r in Role}:
        raise UserError(f"rol inválido: {role}")
    if role == Role.CLIENT and customer_id is None:
        raise UserError("un usuario 'client' requiere customer_id")
    if role != Role.CLIENT and customer_id is not None:
        raise UserError("un usuario interno no lleva customer_id")
    if db.execute(select(User).where(User.email == email.lower())).scalar_one_or_none():
        raise UserError("el email ya existe")

    user = User(
        email=email.lower(),
        password_hash=hash_password(password),
        role=role,
        customer_id=customer_id,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def list_users(db: Session) -> list[User]:
    return list(db.execute(select(User).order_by(User.id)).scalars())


def set_active(db: Session, user_id: int, is_active: bool) -> User:
    user = db.get(User, user_id)
    if user is None:
        raise UserError("usuario no encontrado")
    # Guardia: no dejar el sistema sin superadmin activo.
    if not is_active and user.role == Role.SUPERADMIN and _active_superadmins(db) <= 1:
        raise UserError("no puedes desactivar el último superadmin")
    user.is_active = is_active
    db.commit()
    db.refresh(user)
    return user


def _active_superadmins(db: Session) -> int:
    return db.execute(
        select(func.count())
        .select_from(User)
        .where(User.role == Role.SUPERADMIN, User.is_active.is_(True))
    ).scalar_one()


def seed_superadmin(db: Session, email: str, password: str) -> None:
    """Crea el superadmin inicial si no existe (idempotente)."""
    if not email or not password:
        return
    existing = db.execute(select(User).where(User.email == email.lower())).scalar_one_or_none()
    if existing is not None:
        return
    db.add(
        User(
            email=email.lower(),
            password_hash=hash_password(password),
            role=str(Role.SUPERADMIN),
            customer_id=None,
        )
    )
    db.commit()
