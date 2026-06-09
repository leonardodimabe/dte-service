"""Endpoints de administración (datos maestros + RCV de operador).

Acceso vía ``admin_access``: JWT con rol de escritura (operador/superadmin) **o**
la ``X-Admin-Key`` de máquina (Odoo). Las mutaciones quedan en ``AdminAudit``.
"""

from __future__ import annotations

import datetime as dt

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.concurrency import run_blocking
from app.db.models import Customer, User
from app.db.session import get_db
from app.schemas.admin import (
    CafInfo,
    CafOut,
    CafUpload,
    CertificateInfo,
    CertificateOut,
    CertificateUpload,
    CustomerCreate,
    CustomerOut,
    GrantedServiceOut,
    ServiceGrant,
    ServiceGrantOut,
    ServiceInfo,
)
from app.schemas.rcv import RcvDocumentOut, RcvDocumentsRequest, RcvDocumentsResponse
from app.security.auth import admin_access, admin_read_access
from app.security.service_codes import ALL_SERVICES
from app.services import audit_service, certificate_service, customer_service, rcv_service

router = APIRouter(prefix="/admin", tags=["Admin"])


def _get_customer(db: Session, customer_id: int) -> Customer:
    customer = db.get(Customer, customer_id)
    if customer is None:
        raise HTTPException(status_code=404, detail="cliente no encontrado")
    return customer


def _actor_id(actor: User | None) -> int | None:
    return actor.id if actor else None


@router.get("/customers", response_model=list[CustomerOut])
async def list_customers(
    actor: User | None = Depends(admin_read_access), db: Session = Depends(get_db)
) -> list[Customer]:
    return customer_service.list_customers(db)


@router.get("/services", response_model=list[ServiceInfo])
async def list_services(actor: User | None = Depends(admin_read_access)) -> list[ServiceInfo]:
    return [ServiceInfo(code=code, name=name) for code, name in ALL_SERVICES.items()]


@router.get("/customers/{customer_id}", response_model=CustomerOut)
async def get_customer(
    customer_id: int,
    actor: User | None = Depends(admin_read_access),
    db: Session = Depends(get_db),
) -> Customer:
    return _get_customer(db, customer_id)


@router.get("/customers/{customer_id}/services", response_model=list[GrantedServiceOut])
async def customer_services(
    customer_id: int,
    actor: User | None = Depends(admin_read_access),
    db: Session = Depends(get_db),
) -> list[GrantedServiceOut]:
    customer = _get_customer(db, customer_id)
    return [
        GrantedServiceOut(service_code=s.code, name=s.name)
        for s in customer_service.list_services_for(db, customer)
    ]


@router.get("/customers/{customer_id}/certificates", response_model=list[CertificateInfo])
async def customer_certificates(
    customer_id: int,
    actor: User | None = Depends(admin_read_access),
    db: Session = Depends(get_db),
) -> list[CertificateInfo]:
    customer = _get_customer(db, customer_id)
    today = dt.date.today()
    return [
        CertificateInfo(
            id=c.id, due_date=c.due_date, created_at=c.created_at, expired=c.due_date < today
        )
        for c in customer_service.list_certificates(db, customer)
    ]


@router.get("/customers/{customer_id}/cafs", response_model=list[CafInfo])
async def customer_cafs(
    customer_id: int,
    actor: User | None = Depends(admin_read_access),
    db: Session = Depends(get_db),
) -> list[CafInfo]:
    customer = _get_customer(db, customer_id)
    pointers = customer_service.folio_pointers(db, customer_id)
    return [
        CafInfo(
            id=c.id,
            doc_type=c.doc_type,
            folio_from=c.folio_from,
            folio_to=c.folio_to,
            exhausted=c.exhausted,
            last_folio=pointers.get(c.doc_type, 0),
        )
        for c in customer_service.list_cafs(db, customer)
    ]


@router.post("/customers", response_model=CustomerOut)
async def create_customer(
    data: CustomerCreate,
    actor: User | None = Depends(admin_access),
    db: Session = Depends(get_db),
) -> Customer:
    customer = await run_blocking(customer_service.create_customer, db, data)
    audit_service.record_change(
        db, _actor_id(actor), "customer.create", "customer", str(customer.id), customer.name
    )
    return customer


@router.post("/customers/{customer_id}/certificate", response_model=CertificateOut)
async def upload_certificate(
    customer_id: int,
    data: CertificateUpload,
    actor: User | None = Depends(admin_access),
    db: Session = Depends(get_db),
) -> CertificateOut:
    customer = _get_customer(db, customer_id)
    row = await run_blocking(
        certificate_service.store_certificate, db, customer, data.file_base64, data.password
    )
    audit_service.record_change(
        db,
        _actor_id(actor),
        "certificate.upload",
        "customer",
        str(customer.id),
        f"vence {row.due_date}",
    )
    return CertificateOut(id=row.id, rut=customer.rut, due_date=row.due_date)


@router.post("/customers/{customer_id}/caf", response_model=CafOut)
async def upload_caf(
    customer_id: int,
    data: CafUpload,
    actor: User | None = Depends(admin_access),
    db: Session = Depends(get_db),
) -> CafOut:
    customer = _get_customer(db, customer_id)
    row = await run_blocking(customer_service.add_caf, db, customer, data.xml_base64)
    audit_service.record_change(
        db,
        _actor_id(actor),
        "caf.upload",
        "customer",
        str(customer.id),
        f"tipo {row.doc_type} folios {row.folio_from}-{row.folio_to}",
    )
    return CafOut(
        id=row.id, doc_type=row.doc_type, folio_from=row.folio_from, folio_to=row.folio_to
    )


@router.post("/customers/{customer_id}/services", response_model=ServiceGrantOut)
async def grant_service(
    customer_id: int,
    data: ServiceGrant,
    actor: User | None = Depends(admin_access),
    db: Session = Depends(get_db),
) -> ServiceGrantOut:
    customer = _get_customer(db, customer_id)
    await run_blocking(customer_service.grant_service, db, customer, data.service_code, data.apikey)
    audit_service.record_change(
        db, _actor_id(actor), "service.grant", "customer", str(customer.id), data.service_code
    )
    return ServiceGrantOut(service_code=data.service_code, granted=True)


@router.delete("/customers/{customer_id}/services/{service_code}", response_model=ServiceGrantOut)
async def revoke_service(
    customer_id: int,
    service_code: str,
    actor: User | None = Depends(admin_access),
    db: Session = Depends(get_db),
) -> ServiceGrantOut:
    customer = _get_customer(db, customer_id)
    removed = customer_service.revoke_service(db, customer, service_code)
    if not removed:
        raise HTTPException(status_code=404, detail="el cliente no tiene ese servicio")
    audit_service.record_change(
        db, _actor_id(actor), "service.revoke", "customer", str(customer.id), service_code
    )
    return ServiceGrantOut(service_code=service_code, granted=False)


@router.post("/customers/{customer_id}/rcv", response_model=RcvDocumentsResponse)
async def customer_rcv(
    customer_id: int,
    req: RcvDocumentsRequest,
    actor: User | None = Depends(admin_access),
    db: Session = Depends(get_db),
) -> RcvDocumentsResponse:
    """RCV de operador: compras/ventas de cualquier cliente usando su cert guardado
    (para Odoo con X-Admin-Key o un operador desde el panel con JWT)."""
    customer = _get_customer(db, customer_id)
    docs = await run_blocking(
        rcv_service.list_documents_for_customer, db, customer, req.period, req.operation
    )
    return RcvDocumentsResponse(
        issuer_rut=customer.rut,
        period=req.period,
        operation=req.operation,
        count=len(docs),
        documents=[RcvDocumentOut.model_validate(d) for d in docs],
    )
