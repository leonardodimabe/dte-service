"""Schemas de los acuses de intercambio (responder a un EnvioDTE recibido)."""

from __future__ import annotations

from pydantic import BaseModel


class AcknowledgmentRequest(BaseModel):
    envelope_base64: str  # EnvioDTE recibido, en base64


class ResultRequest(BaseModel):
    envelope_base64: str
    accept: bool = True
    rejection_label: str = ""


class ReceiptsRequest(BaseModel):
    envelope_base64: str
    location: str = "Bodega"


class ExchangeResponse(BaseModel):
    xml_base64: str
