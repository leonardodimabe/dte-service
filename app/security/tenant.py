"""Autenticación multi-tenant por headers + resolución del cliente.

Mirror del patrón .NET: el request trae ``apiKey`` y ``customerCode`` y cada
endpoint exige un ``service_code``. Se valida que el cliente exista, tenga ese
servicio habilitado y la apikey calce (hash). La auditoría la escribe el
middleware de access-log; este dep solo fija el principal en ``request.state``.
"""

from __future__ import annotations

from collections.abc import Callable

from fastapi import Depends, Header, HTTPException, Request
from sqlalchemy.orm import Session

from app.db.models import Customer, CustomerService, Service
from app.db.session import get_db
from app.security.apikeys import verify_apikey
from app.security.roles import Role


def tenant_for(service_code: str) -> Callable[..., Customer]:
    """Devuelve una dependencia que resuelve el ``Customer`` para ese servicio."""

    def _dep(
        request: Request,
        api_key: str = Header(alias="apiKey"),
        customer_code: str = Header(alias="customerCode"),
        db: Session = Depends(get_db),
    ) -> Customer:
        request.state.service_code = service_code
        cs = (
            db.query(CustomerService)
            .join(CustomerService.service)
            .join(CustomerService.customer)
            .filter(Customer.key == customer_code, Service.code == service_code)
            .first()
        )
        if cs is None or not verify_apikey(api_key, cs.apikey_hash):
            raise HTTPException(status_code=401, detail="credenciales inválidas")

        request.state.principal = ("customer", cs.customer_id, str(Role.CLIENT))
        return cs.customer

    return _dep
