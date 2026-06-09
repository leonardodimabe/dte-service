"""Servicio RCV: descarga normalizada para conciliar contra Odoo."""

from __future__ import annotations

from dte_chile.certificate import Certificate
from dte_chile.rcv import RCVClient, RcvDocument


def list_documents(
    cert: Certificate, issuer_rut: str, period: str, operation: str
) -> list[RcvDocument]:
    with RCVClient(cert) as rcv:
        return rcv.documents(issuer_rut, period, operation)
