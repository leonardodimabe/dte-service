"""Servicio RCV: descarga normalizada para conciliar contra Odoo."""

from __future__ import annotations

from dte_chile.certificate import Certificate
from dte_chile.rcv import RCVClient, RcvDocument
from sqlalchemy.orm import Session

from app.db.models import Customer
from app.errors.exceptions import CertificateUnavailable
from app.services import certificate_service


def list_documents(
    cert: Certificate, issuer_rut: str, period: str, operation: str
) -> list[RcvDocument]:
    with RCVClient(cert) as rcv:
        return rcv.documents(issuer_rut, period, operation)


def list_documents_for_customer(
    db: Session, customer: Customer, period: str, operation: str
) -> list[RcvDocument]:
    """Versión de operador: resuelve el cert guardado del cliente y consulta su RCV.

    El ``issuer_rut`` se toma del propio cliente (no se pide en el request).
    """
    cert = certificate_service.resolve_certificate(db, customer)
    if cert is None:
        raise CertificateUnavailable(customer.id)
    return list_documents(cert, customer.rut, period, operation)
