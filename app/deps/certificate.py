"""Resolución del ``Certificate`` del cliente por request (per-tenant).

Sin caché (como el .NET): toma el certificado vigente más reciente del cliente,
lo descifra y lo construye en threadpool. La lógica vive en
``certificate_service.resolve_certificate`` (reusada por los endpoints de operador).
"""

from __future__ import annotations

from collections.abc import Callable

from dte_chile.certificate import Certificate
from fastapi import Depends
from sqlalchemy.orm import Session

from app.core.concurrency import run_blocking
from app.db.models import Customer
from app.db.session import get_db
from app.deps.auth import require_book, require_dte, require_exchange, require_rcv
from app.errors.exceptions import CertificateUnavailable
from app.services import certificate_service


def _certificate_dep(tenant_dependency: Callable[..., Customer]) -> Callable[..., Certificate]:
    async def _dep(
        customer: Customer = Depends(tenant_dependency),
        db: Session = Depends(get_db),
    ) -> Certificate:
        cert = await run_blocking(certificate_service.resolve_certificate, db, customer)
        if cert is None:
            raise CertificateUnavailable(customer.id)
        return cert

    return _dep


cert_rcv = _certificate_dep(require_rcv)
cert_dte = _certificate_dep(require_dte)
cert_book = _certificate_dep(require_book)
cert_exchange = _certificate_dep(require_exchange)
