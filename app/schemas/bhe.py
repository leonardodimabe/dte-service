"""Schemas de BHE (Boletas de Honorarios Electrónicas recibidas)."""

from __future__ import annotations

import datetime as dt

from pydantic import BaseModel, ConfigDict, Field


class BheReceivedRequest(BaseModel):
    # El RUT receptor se toma del cliente resuelto (tenant), no se pide.
    period: str = Field(pattern=r"^\d{6}$", examples=["202505"])  # AAAAMM


class BheReceivedOut(BaseModel):
    """Espejo de ``dte_chile.BheDocument``."""

    model_config = ConfigDict(from_attributes=True)

    issuer_rut: str
    issuer_name: str
    folio: int
    issue_date: dt.date | None = None
    gross_amount: int
    retention_amount: int
    net_amount: int
    status: str  # "vigente" | "anulada"
    cancel_date: dt.date | None = None


class BheReceivedResponse(BaseModel):
    receiver_rut: str
    period: str
    count: int
    documents: list[BheReceivedOut]
