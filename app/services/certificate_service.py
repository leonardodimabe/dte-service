"""Carga y validación de certificados de cliente (admin)."""

from __future__ import annotations

import base64
import binascii
import datetime as dt

from dte_chile.certificate import Certificate
from sqlalchemy.orm import Session

from app.core import crypto
from app.db.models import Customer, CustomerCertificate
from app.errors.exceptions import DomainError


def resolve_certificate(db: Session, customer: Customer) -> Certificate | None:
    """Carga el certificado vigente más reciente del cliente (o None si no hay).

    Reusado por la dependencia per-tenant y por los endpoints de operador.
    Hace cripto (from_pfx_bytes) → conviene llamarlo dentro de run_blocking.
    """
    row = (
        db.query(CustomerCertificate)
        .filter(
            CustomerCertificate.customer_id == customer.id,
            CustomerCertificate.due_date >= dt.date.today(),
        )
        .order_by(CustomerCertificate.created_at.desc())
        .first()
    )
    if row is None:
        return None
    pfx = crypto.decrypt(row.file_base64)
    return Certificate.from_pfx_bytes(pfx, crypto.decrypt_str(row.password))


def store_certificate(
    db: Session, customer: Customer, file_base64: str, password: str, *, commit: bool = True
) -> CustomerCertificate:
    """Valida el .pfx, extrae RUT/vencimiento y lo guarda CIFRADO."""
    try:
        pfx = base64.b64decode(file_base64, validate=True)
    except (binascii.Error, ValueError) as ex:
        raise DomainError("file_base64 no es base64 válido") from ex
    try:
        Certificate.from_pfx_bytes(pfx, password)  # valida que el .pfx + password sean correctos
    except ValueError as ex:
        raise DomainError("PFX inválido o contraseña incorrecta") from ex

    # Nota: NO se exige que el RUT del certificado sea igual al del cliente.
    # En Chile el certificado digital del SII se emite a una persona natural
    # (el representante), por lo que su RUT normalmente difiere del de la empresa.
    # El SII valida la autorización del firmante; aquí basta con un .pfx válido.

    due = _expiry(pfx, password)
    row = CustomerCertificate(
        customer_id=customer.id,
        file_base64=crypto.encrypt(pfx),
        password=crypto.encrypt(password),
        due_date=due,
    )
    db.add(row)
    db.flush()
    db.refresh(row)
    if commit:
        db.commit()
    return row


def _expiry(pfx: bytes, password: str) -> dt.date:
    from cryptography.hazmat.primitives.serialization import pkcs12

    _, cert, _ = pkcs12.load_key_and_certificates(pfx, password.encode("utf-8"))
    if cert is None:  # no usar assert: desaparece con `python -O`
        raise DomainError("el PFX no contiene un certificado")
    return cert.not_valid_after_utc.date()
