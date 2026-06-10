"""Gestión de claves de máquina para /admin (solo superadmin).

La clave en claro se devuelve UNA sola vez al crearla; en BD solo vive el hash.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.models import MachineKey, User
from app.db.session import get_db
from app.schemas.machine_key import MachineKeyCreate, MachineKeyCreated, MachineKeyOut
from app.security.auth import require_superadmin
from app.services import audit_service, machine_key_service
from app.services.machine_key_service import MachineKeyError

router = APIRouter(prefix="/machine-keys", tags=["Machine Keys"])


@router.post("", response_model=MachineKeyCreated)
def create_machine_key(
    data: MachineKeyCreate,
    actor: User = Depends(require_superadmin),
    db: Session = Depends(get_db),
) -> MachineKeyCreated:
    try:
        row, api_key = machine_key_service.create_key(db, data.name, data.role, commit=False)
    except MachineKeyError as ex:
        raise HTTPException(status_code=400, detail=str(ex)) from ex
    audit_service.record_change(
        db, actor.id, "machine_key.create", "machine_key", str(row.id), f"{row.name} ({row.role})"
    )
    return MachineKeyCreated(
        id=row.id,
        name=row.name,
        key_id=row.key_id,
        role=row.role,
        is_active=row.is_active,
        created_at=row.created_at,
        api_key=api_key,
    )


@router.get("", response_model=list[MachineKeyOut])
def list_machine_keys(
    actor: User = Depends(require_superadmin), db: Session = Depends(get_db)
) -> list[MachineKey]:
    return machine_key_service.list_keys(db)


@router.delete("/{mk_id}", response_model=MachineKeyOut)
def revoke_machine_key(
    mk_id: int,
    actor: User = Depends(require_superadmin),
    db: Session = Depends(get_db),
) -> MachineKey:
    row = machine_key_service.revoke(db, mk_id, commit=False)
    if row is None:
        raise HTTPException(status_code=404, detail="clave no encontrada")
    audit_service.record_change(
        db, actor.id, "machine_key.revoke", "machine_key", str(row.id), row.name
    )
    return row
