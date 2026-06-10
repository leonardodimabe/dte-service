"""Asignador de folios en BD (HA, anti-duplicación).

La fila ``FolioPointer(customer, doc_type)`` se bloquea con ``SELECT ... FOR
UPDATE``; así dos workers/hosts no entregan el mismo folio. El CAF (con la llave
de timbre) se carga descifrado en memoria vía ``load_caf_bytes``.
"""

from __future__ import annotations

from dte_chile import FolioError, FoliosExhausted
from dte_chile.caf import CAF, load_caf_bytes
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core import crypto
from app.db.models import Caf, FolioAssignment, FolioPointer


def ensure_pointer(db: Session, customer_id: int, doc_type: int, *, commit: bool = True) -> None:
    """Crea el puntero (last_folio=0) si no existe. Llamar al subir un CAF."""
    exists = db.get(FolioPointer, (customer_id, doc_type))
    if exists is None:
        db.add(FolioPointer(customer_id=customer_id, doc_type=doc_type, last_folio=0))
        if commit:
            db.commit()
        else:
            db.flush()


def next_folio(
    db: Session, customer_id: int, doc_type: int, request_id: str = "-"
) -> tuple[int, CAF]:
    """Asigna el siguiente folio disponible y devuelve (folio, CAF).

    Registra la asignación en ``FolioAssignment`` (mismo commit que avanza el
    puntero) para trazar qué request consumió cada folio.
    """
    ptr = db.execute(
        select(FolioPointer)
        .where(FolioPointer.customer_id == customer_id, FolioPointer.doc_type == doc_type)
        .with_for_update()
    ).scalar_one_or_none()
    if ptr is None:
        raise FolioError(f"No hay CAF cargado para el tipo {doc_type}.")

    target = ptr.last_folio + 1
    caf_row = (
        db.query(Caf)
        .filter(
            Caf.customer_id == customer_id,
            Caf.doc_type == doc_type,
            Caf.exhausted.is_(False),
            Caf.folio_to >= target,
        )
        .order_by(Caf.folio_from)
        .first()
    )
    if caf_row is None:
        raise FoliosExhausted(f"Folios agotados para tipo {doc_type} (último: {ptr.last_folio}).")

    folio = max(target, caf_row.folio_from)  # salta huecos entre CAF
    ptr.last_folio = folio
    if folio >= caf_row.folio_to:
        caf_row.exhausted = True
    db.add(
        FolioAssignment(
            customer_id=customer_id, doc_type=doc_type, folio=folio, request_id=request_id
        )
    )
    db.commit()

    caf = load_caf_bytes(crypto.decrypt(caf_row.xml_encrypted))
    return folio, caf


def mark_assignment(db: Session, customer_id: int, doc_type: int, folio: int, status: str) -> None:
    """Actualiza el desenlace de un folio asignado (``issued`` / ``failed``)."""
    row = db.execute(
        select(FolioAssignment).where(
            FolioAssignment.customer_id == customer_id,
            FolioAssignment.doc_type == doc_type,
            FolioAssignment.folio == folio,
        )
    ).scalar_one_or_none()
    if row is not None:
        row.status = status
        db.commit()
