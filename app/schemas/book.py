"""Schemas del Libro de Compras y Ventas (IECV)."""

from __future__ import annotations

import datetime as dt
from typing import Literal

from pydantic import BaseModel, Field


class BookLineIn(BaseModel):
    doc_type: int
    folio: int
    date: dt.date
    rut: str
    business_name: str
    exempt_amount: int = 0
    net_amount: int = 0
    vat_amount: int = 0
    total_amount: int = 0
    voided: bool = False


class BookRequest(BaseModel):
    period: str = Field(pattern=r"^\d{4}-\d{2}$", examples=["2026-05"])  # AAAA-MM
    operation_type: Literal["VENTA", "COMPRA"] = "VENTA"
    lines: list[BookLineIn] = Field(min_length=1)


class BookResponse(BaseModel):
    period: str
    operation_type: str
    xml_base64: str
