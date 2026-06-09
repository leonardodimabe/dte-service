"""Schemas del RCV (conciliación con Odoo)."""

from __future__ import annotations

import datetime as dt
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

Operation = Literal["COMPRA", "VENTA"]


class RcvDocumentsRequest(BaseModel):
    issuer_rut: str = Field(examples=["76158145-7"])
    period: str = Field(pattern=r"^\d{6}$", examples=["202505"])  # AAAAMM
    operation: Operation = "COMPRA"


class RcvDocumentOut(BaseModel):
    """Espejo de ``dte_chile.RcvDocument`` (clave de match: doc_type+rut+folio)."""

    model_config = ConfigDict(from_attributes=True)

    operation: str
    state: str
    doc_type: int
    folio: int
    counterpart_rut: str
    counterpart_name: str
    date: dt.date
    exempt_amount: int
    net_amount: int
    vat_amount: int
    total_amount: int
    reception_date: dt.datetime | None = None


class RcvDocumentsResponse(BaseModel):
    period: str
    operation: str
    count: int
    documents: list[RcvDocumentOut]
