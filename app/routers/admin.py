"""Endpoints de administración (alta de clientes, certificados, CAF, servicios).

Protegidos por la API key global ``DTE_ADMIN_API_KEY`` (header ``X-Admin-Key``).
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy.orm import Session

from app.core.concurrency import run_blocking
from app.core.config import get_settings
from app.db.models import Customer
from app.db.session import get_db
from app.schemas.admin import (
    CafOut,
    CafUpload,
    CertificateOut,
    CertificateUpload,
    CustomerCreate,
    CustomerOut,
    ServiceGrant,
    ServiceGrantOut,
)
from app.schemas.rcv import RcvDocumentOut, RcvDocumentsRequest, RcvDocumentsResponse
from app.services import certificate_service, customer_service, rcv_service

router = APIRouter(prefix="/admin", tags=["Admin"])


def require_admin(x_admin_key: str = Header(alias="X-Admin-Key")) -> None:
    if x_admin_key != get_settings().admin_api_key:
        raise HTTPException(status_code=401, detail="admin key inválida")


def _get_customer(db: Session, customer_id: int) -> Customer:
    customer = db.get(Customer, customer_id)
    if customer is None:
        raise HTTPException(status_code=404, detail="cliente no encontrado")
    return customer


@router.post("/customers", response_model=CustomerOut, dependencies=[Depends(require_admin)])
async def create_customer(data: CustomerCreate, db: Session = Depends(get_db)) -> Customer:
    return await run_blocking(customer_service.create_customer, db, data)


@router.post(
    "/customers/{customer_id}/certificate",
    response_model=CertificateOut,
    dependencies=[Depends(require_admin)],
)
async def upload_certificate(
    customer_id: int, data: CertificateUpload, db: Session = Depends(get_db)
) -> CertificateOut:
    customer = _get_customer(db, customer_id)
    row = await run_blocking(
        certificate_service.store_certificate, db, customer, data.file_base64, data.password
    )
    return CertificateOut(id=row.id, rut=customer.rut, due_date=row.due_date)


@router.post(
    "/customers/{customer_id}/caf",
    response_model=CafOut,
    dependencies=[Depends(require_admin)],
)
async def upload_caf(customer_id: int, data: CafUpload, db: Session = Depends(get_db)) -> CafOut:
    customer = _get_customer(db, customer_id)
    row = await run_blocking(customer_service.add_caf, db, customer, data.xml_base64)
    return CafOut(
        id=row.id, doc_type=row.doc_type, folio_from=row.folio_from, folio_to=row.folio_to
    )


@router.post(
    "/customers/{customer_id}/services",
    response_model=ServiceGrantOut,
    dependencies=[Depends(require_admin)],
)
async def grant_service(
    customer_id: int, data: ServiceGrant, db: Session = Depends(get_db)
) -> ServiceGrantOut:
    customer = _get_customer(db, customer_id)
    await run_blocking(customer_service.grant_service, db, customer, data.service_code, data.apikey)
    return ServiceGrantOut(service_code=data.service_code, granted=True)


@router.post(
    "/customers/{customer_id}/rcv",
    response_model=RcvDocumentsResponse,
    dependencies=[Depends(require_admin)],
)
async def customer_rcv(
    customer_id: int, req: RcvDocumentsRequest, db: Session = Depends(get_db)
) -> RcvDocumentsResponse:
    """RCV de operador: trae compras/ventas de cualquier cliente con UNA credencial
    (X-Admin-Key), usando el certificado guardado del cliente. Para conciliación
    masiva desde Odoo sin manejar la apiKey de cada cliente."""
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
