"""Schemas del Libro de Compras y Ventas (IECV)."""

from __future__ import annotations

import datetime as dt
from typing import Literal

from pydantic import BaseModel, Field

from app.schemas.dte import SubmissionResultOut


class NonRecoverableVatIn(BaseModel):
    """IVA sin derecho a crédito (<IVANoRec>), con su motivo.

    1 operaciones no gravadas · 2 fuera de plazo · 3 gastos rechazados
    · 4 entrega gratuita · 9 otros.
    """

    code: Literal[1, 2, 3, 4, 9]
    amount: int = Field(ge=0)


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
    # --- Sólo Libro de Compras ---
    common_use_vat: int = Field(0, ge=0)
    non_recoverable_vat: list[NonRecoverableVatIn] = []
    retained_total_vat: int = Field(0, ge=0)


class BookRequest(BaseModel):
    period: str = Field(pattern=r"^\d{4}-\d{2}$", examples=["2026-05"])  # AAAA-MM
    operation_type: Literal["VENTA", "COMPRA"] = "VENTA"
    # Factor de proporcionalidad del IVA de uso común (sólo Libro de Compras).
    proportionality_factor: float | None = Field(None, ge=0, le=1)
    # MENSUAL declara TODO el período y el SII lo contrasta contra los DTE que
    # tiene registrados. ESPECIAL es el que pide una notificación puntual —el
    # caso del set de certificación—, y ahí FolioNotificacion es su número de
    # atención.
    book_type: Literal["MENSUAL", "ESPECIAL", "RECTIFICA", "AJUSTE"] = "MENSUAL"
    notification_folio: int = Field(1, ge=1)
    lines: list[BookLineIn] = Field(min_length=1)
    send: bool = True  # subir el libro al SII (el set de certificación lo exige)


class BookResponse(BaseModel):
    period: str
    operation_type: str
    xml_base64: str
    submission: SubmissionResultOut | None = None


class GuideBookLineIn(BaseModel):
    """Una guía dentro del Libro de Guías de Despacho."""

    folio: int
    date: dt.date | None = None
    transfer_type: Literal[1, 2, 3, 4, 5, 6, 7, 8, 9] | None = None  # TpoOper
    receiver_rut: str = ""
    receiver_name: str = ""
    net_amount: int = 0
    vat_amount: int = 0
    total_amount: int = 0
    vat_rate: int = 19
    # 1 = anulada antes de enviarla al SII, 2 = después, 3 = recepción parcial.
    voided: Literal[1, 2, 3] | None = None
    # Guía facturada en el período: monto absorbido + referencia a la factura.
    modified_amount: int | None = None
    ref_doc_type: int | None = None
    ref_folio: int | None = None
    ref_date: dt.date | None = None


class GuideBookRequest(BaseModel):
    period: str = Field(pattern=r"^\d{4}-\d{2}$", examples=["2026-11"])  # AAAA-MM
    # Folio de la notificación con que el SII pide el libro; en certificación,
    # el número de atención del set. El XSD exige un entero positivo.
    notification_folio: int = Field(1, ge=1)
    submission_type: Literal["TOTAL", "PARCIAL", "FINAL", "AJUSTE"] = "TOTAL"
    lines: list[GuideBookLineIn] = Field(min_length=1)
    send: bool = True


class GuideBookResponse(BaseModel):
    period: str
    xml_base64: str
    submission: SubmissionResultOut | None = None
