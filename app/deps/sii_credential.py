"""Resolución de la clave tributaria del cliente por request (per-tenant).

Análogo a ``deps.certificate`` pero para el login web del SII (BHE): descifra la
clave guardada del cliente en threadpool. La lógica vive en
``sii_credential_service.resolve_sii_password``.
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable

from fastapi import Depends
from sqlalchemy.orm import Session

from app.core.concurrency import run_blocking
from app.db.models import Customer
from app.db.session import get_db
from app.deps.auth import require_bhe
from app.errors.exceptions import SiiCredentialUnavailable
from app.services import sii_credential_service


def _sii_password_dep(tenant_dependency: Callable[..., Customer]) -> Callable[..., Awaitable[str]]:
    async def _dep(
        customer: Customer = Depends(tenant_dependency),
        db: Session = Depends(get_db),
    ) -> str:
        password = await run_blocking(sii_credential_service.resolve_sii_password, db, customer)
        if password is None:
            raise SiiCredentialUnavailable(customer.id)
        return password

    return _dep


sii_pwd_bhe = _sii_password_dep(require_bhe)
