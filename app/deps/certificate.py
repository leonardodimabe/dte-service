"""Resolución del ``Certificate`` del cliente por request.

Sin caché (como el .NET): se toma el certificado vigente más reciente del
cliente, se descifra y se construye. El parseo cripto corre en threadpool.
"""

from __future__ import annotations

import datetime as dt
from collections.abc import Callable

from dte_chile.certificate import Certificate
from fastapi import Depends, HTTPException
from sqlalchemy.orm import Session

from app.core import crypto
from app.core.concurrency import run_blocking
from app.db.models import Customer, CustomerCertificate
from app.db.session import get_db
from app.deps.auth import require_book, require_dte, require_exchange, require_rcv


def _load_row(db: Session, customer: Customer) -> CustomerCertificate:
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
        raise HTTPException(status_code=409, detail="el cliente no tiene un certificado vigente")
    return row


def _build(row: CustomerCertificate) -> Certificate:
    pfx = crypto.decrypt(row.file_base64)
    password = crypto.decrypt_str(row.password)
    return Certificate.from_pfx_bytes(pfx, password)


def _certificate_dep(tenant_dependency: Callable[..., Customer]) -> Callable[..., Certificate]:
    async def _dep(
        customer: Customer = Depends(tenant_dependency),
        db: Session = Depends(get_db),
    ) -> Certificate:
        row = _load_row(db, customer)
        return await run_blocking(_build, row)

    return _dep


cert_rcv = _certificate_dep(require_rcv)
cert_dte = _certificate_dep(require_dte)
cert_book = _certificate_dep(require_book)
cert_exchange = _certificate_dep(require_exchange)
