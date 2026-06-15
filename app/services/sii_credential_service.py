"""Clave tributaria del SII por cliente (login web para BHE).

Distinta del certificado: las Boletas de Honorarios recibidas se consultan por
login con clave, no por TLS mutuo. La clave se guarda Fernet-cifrada (write-only).
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.core import crypto
from app.db.models import Customer, CustomerSiiCredential
from app.errors.exceptions import DomainError


def store_sii_password(
    db: Session, customer: Customer, password: str, *, commit: bool = True
) -> CustomerSiiCredential:
    """Guarda (o rota) la clave tributaria del cliente, cifrada."""
    if not password or not password.strip():
        raise DomainError("La clave tributaria no puede estar vacía.")
    row = (
        db.query(CustomerSiiCredential)
        .filter(CustomerSiiCredential.customer_id == customer.id)
        .first()
    )
    token = crypto.encrypt(password)
    if row is None:
        row = CustomerSiiCredential(customer_id=customer.id, password=token)
        db.add(row)
    else:
        row.password = token
    db.flush()
    db.refresh(row)
    if commit:
        db.commit()
    return row


def resolve_sii_password(db: Session, customer: Customer) -> str | None:
    """Devuelve la clave tributaria en claro del cliente (o None si no hay)."""
    row = (
        db.query(CustomerSiiCredential)
        .filter(CustomerSiiCredential.customer_id == customer.id)
        .first()
    )
    if row is None:
        return None
    return crypto.decrypt_str(row.password)
