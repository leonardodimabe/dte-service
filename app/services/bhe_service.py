"""Servicio BHE: descarga de Boletas de Honorarios recibidas del SII."""

from __future__ import annotations

from dte_chile.bhe import BheClient, BheDocument
from sqlalchemy.orm import Session

from app.db.models import Customer
from app.errors.exceptions import SiiCredentialUnavailable
from app.services import sii_credential_service


def list_received(rut: str, password: str, year: int, month: int) -> list[BheDocument]:
    with BheClient(rut, password) as cli:
        return cli.fetch_received(year, month)


def list_received_for_customer(
    db: Session, customer: Customer, year: int, month: int
) -> list[BheDocument]:
    """Versión de operador: resuelve la clave tributaria guardada del cliente.

    El ``rut`` se toma del propio cliente (no se pide en el request).
    """
    password = sii_credential_service.resolve_sii_password(db, customer)
    if password is None:
        raise SiiCredentialUnavailable(customer.id)
    return list_received(customer.rut, password, year, month)
