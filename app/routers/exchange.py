"""Endpoints de acuses de intercambio (responder un EnvioDTE recibido)."""

from __future__ import annotations

from dte_chile.certificate import Certificate
from fastapi import APIRouter, Depends

from app.core.concurrency import run_blocking
from app.deps.certificate import cert_exchange
from app.schemas.exchange import (
    AcknowledgmentRequest,
    ExchangeResponse,
    ReceiptsRequest,
    ResultRequest,
)
from app.services import exchange_service

router = APIRouter(prefix="/exchange", tags=["Intercambio"])


@router.post("/ack", response_model=ExchangeResponse)
async def acknowledgment(
    req: AcknowledgmentRequest, cert: Certificate = Depends(cert_exchange)
) -> ExchangeResponse:
    xml_b64 = await run_blocking(exchange_service.acknowledgment, cert, req.envelope_base64)
    return ExchangeResponse(xml_base64=xml_b64)


@router.post("/result", response_model=ExchangeResponse)
async def result(
    req: ResultRequest, cert: Certificate = Depends(cert_exchange)
) -> ExchangeResponse:
    xml_b64 = await run_blocking(
        exchange_service.result, cert, req.envelope_base64, req.accept, req.rejection_label
    )
    return ExchangeResponse(xml_base64=xml_b64)


@router.post("/receipts", response_model=ExchangeResponse)
async def receipts(
    req: ReceiptsRequest, cert: Certificate = Depends(cert_exchange)
) -> ExchangeResponse:
    xml_b64 = await run_blocking(exchange_service.receipts, cert, req.envelope_base64, req.location)
    return ExchangeResponse(xml_base64=xml_b64)
