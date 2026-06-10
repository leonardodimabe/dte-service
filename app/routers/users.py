"""Gestión de usuarios del portal (solo superadmin).

Endpoints ``def`` (síncronos): corren en el threadpool, así el argon2 y la BD
no bloquean el event loop.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.models import User
from app.db.session import get_db
from app.schemas.user import UserActiveUpdate, UserCreate, UserOut
from app.security.auth import require_superadmin
from app.services import audit_service, user_service
from app.services.user_service import UserError

router = APIRouter(prefix="/users", tags=["Usuarios"])


@router.post("", response_model=UserOut)
def create_user(
    data: UserCreate,
    actor: User = Depends(require_superadmin),
    db: Session = Depends(get_db),
) -> User:
    try:
        user = user_service.create_user(db, data.email, data.password, data.role, data.customer_id)
    except UserError as ex:
        raise HTTPException(status_code=400, detail=str(ex)) from ex
    audit_service.record_change(
        db, actor.id, "user.create", "user", str(user.id), f"{user.email} ({user.role})"
    )
    return user


@router.get("", response_model=list[UserOut])
def list_users(
    actor: User = Depends(require_superadmin), db: Session = Depends(get_db)
) -> list[User]:
    return user_service.list_users(db)


@router.patch("/{user_id}/active", response_model=UserOut)
def set_active(
    user_id: int,
    data: UserActiveUpdate,
    actor: User = Depends(require_superadmin),
    db: Session = Depends(get_db),
) -> User:
    try:
        user = user_service.set_active(db, user_id, data.is_active)
    except UserError as ex:
        raise HTTPException(status_code=400, detail=str(ex)) from ex
    audit_service.record_change(
        db, actor.id, "user.set_active", "user", str(user.id), f"is_active={data.is_active}"
    )
    return user
