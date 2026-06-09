"""Endpoints del RCV per-tenant (cada cliente consulta SUS compras/ventas)."""

from __future__ import annotations

from dte_chile.certificate import Certificate
from fastapi import APIRouter, Depends

from app.core.concurrency import run_blocking
from app.db.models import Customer
from app.deps.auth import require_rcv
from app.deps.certificate import cert_rcv
from app.schemas.rcv import RcvDocumentOut, RcvDocumentsRequest, RcvDocumentsResponse
from app.services import rcv_service

router = APIRouter(prefix="/rcv", tags=["RCV"])


@router.post("/documents", response_model=RcvDocumentsResponse)
async def documents(
    req: RcvDocumentsRequest,
    customer: Customer = Depends(require_rcv),
    cert: Certificate = Depends(cert_rcv),
) -> RcvDocumentsResponse:
    # El RUT es el del propio cliente (resuelto por el tenant), no se pide en el body.
    docs = await run_blocking(
        rcv_service.list_documents, cert, customer.rut, req.period, req.operation
    )
    return RcvDocumentsResponse(
        issuer_rut=customer.rut,
        period=req.period,
        operation=req.operation,
        count=len(docs),
        documents=[RcvDocumentOut.model_validate(d) for d in docs],
    )
