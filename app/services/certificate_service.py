"""Carga y validación de certificados de cliente (admin)."""

from __future__ import annotations

import base64
import datetime as dt

from dte_chile.certificate import Certificate
from sqlalchemy.orm import Session

from app.core import crypto
from app.db.models import Customer, CustomerCertificate


def store_certificate(
    db: Session, customer: Customer, file_base64: str, password: str
) -> CustomerCertificate:
    """Valida el .pfx, extrae RUT/vencimiento y lo guarda CIFRADO."""
    pfx = base64.b64decode(file_base64)
    cert = Certificate.from_pfx_bytes(pfx, password)  # valida el .pfx + password

    if cert.rut and cert.rut != customer.rut:
        # Defensa: el titular del cert debe corresponder a la empresa.
        raise ValueError(
            f"El RUT del certificado ({cert.rut}) no coincide con el del cliente ({customer.rut})."
        )

    due = _expiry(pfx, password)
    row = CustomerCertificate(
        customer_id=customer.id,
        file_base64=crypto.encrypt(pfx),
        password=crypto.encrypt(password),
        due_date=due,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def _expiry(pfx: bytes, password: str) -> dt.date:
    from cryptography.hazmat.primitives.serialization import pkcs12

    _, cert, _ = pkcs12.load_key_and_certificates(pfx, password.encode("utf-8"))
    assert cert is not None
    return cert.not_valid_after_utc.date()
