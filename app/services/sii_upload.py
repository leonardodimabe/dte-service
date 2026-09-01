"""Subida de archivos al SII (DTEUpload).

El mismo CGI recibe los sobres de documentos y los libros, así que el envío
vive acá y no dentro del servicio de DTE: el de libros necesita exactamente lo
mismo, y duplicarlo dejaría dos sitios donde recordar los requisitos del SII
(User-Agent, token, RUT de quien envía).
"""

from __future__ import annotations

from dte_chile.certificate import Certificate
from dte_chile.sii_client import Environment, SIIClient, SubmissionResult

from app.db.models import Customer


def upload(
    customer: Customer, cert: Certificate, xml: bytes, issuer_rut: str, timeout_s: int
) -> SubmissionResult:
    """Sube el archivo al ambiente del cliente y devuelve el TrackID."""
    client = SIIClient(cert, Environment[customer.environment.name], timeout=timeout_s)
    try:
        return client.send_dte(xml, issuer_rut, cert.rut or issuer_rut)
    finally:
        client.session.close()  # liberar la sesión HTTP (no hay caché de cliente)
