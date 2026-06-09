"""Endpoints del RCV (conciliación de compras/ventas contra Odoo)."""

from __future__ import annotations

from dte_chile.certificate import Certificate
from fastapi import APIRouter, Depends

from app.core.concurrency import run_blocking
from app.deps.certificate import cert_rcv
from app.schemas.rcv import RcvDocumentOut, RcvDocumentsRequest, RcvDocumentsResponse
from app.services import rcv_service

router = APIRouter(prefix="/rcv", tags=["RCV"])


@router.post("/documents", response_model=RcvDocumentsResponse)
async def documents(
    req: RcvDocumentsRequest, cert: Certificate = Depends(cert_rcv)
) -> RcvDocumentsResponse:
    docs = await run_blocking(
        rcv_service.list_documents, cert, req.issuer_rut, req.period, req.operation
    )
    return RcvDocumentsResponse(
        period=req.period,
        operation=req.operation,
        count=len(docs),
        documents=[RcvDocumentOut.model_validate(d) for d in docs],
    )
