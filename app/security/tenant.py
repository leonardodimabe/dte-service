"""Autenticación multi-tenant por headers + resolución del cliente.

Mirror del patrón .NET: el request trae ``apiKey`` y ``customerCode`` y cada
endpoint exige un ``service_code``. Se valida que el cliente exista, tenga ese
servicio habilitado y la apikey calce (hash). Se audita cada request.
"""

from __future__ import annotations

from collections.abc import Callable

from fastapi import Depends, Header, HTTPException
from sqlalchemy.orm import Session

from app.core.logging import request_id_var
from app.db.models import Customer, CustomerRequest, CustomerService, Service
from app.db.session import get_db
from app.security.apikeys import verify_apikey


def _audit(db: Session, customer_id: int | None, service_code: str, status: str) -> None:
    if customer_id is None:
        return
    db.add(
        CustomerRequest(
            customer_id=customer_id,
            service_code=service_code,
            request_id=request_id_var.get(),
            status=status,
        )
    )
    db.commit()


def tenant_for(service_code: str) -> Callable[..., Customer]:
    """Devuelve una dependencia que resuelve el ``Customer`` para ese servicio."""

    def _dep(
        api_key: str = Header(alias="apiKey"),
        customer_code: str = Header(alias="customerCode"),
        db: Session = Depends(get_db),
    ) -> Customer:
        cs = (
            db.query(CustomerService)
            .join(CustomerService.service)
            .join(CustomerService.customer)
            .filter(Customer.key == customer_code, Service.code == service_code)
            .first()
        )
        if cs is None or not verify_apikey(api_key, cs.apikey_hash):
            _audit(db, cs.customer_id if cs else None, service_code, "denied")
            raise HTTPException(status_code=401, detail="credenciales inválidas")

        _audit(db, cs.customer_id, service_code, "ok")
        return cs.customer

    return _dep
