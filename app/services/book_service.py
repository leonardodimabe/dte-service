"""Servicio del Libro de Compras y Ventas (IECV)."""

from __future__ import annotations

import base64
import datetime as dt

from dte_chile.book import BookCover, BookLine, build_book, serialize
from dte_chile.certificate import Certificate

from app.db.models import Customer


def build(customer: Customer, cert: Certificate, req) -> dict:
    cover = BookCover(
        issuer_rut=customer.rut,
        sender_rut=cert.rut or customer.rut,
        period=req.period,
        operation_type=req.operation_type,
        resolution_number=customer.resolution_number,
        resolution_date=customer.resolution_date,
        lines=[BookLine(**line.model_dump()) for line in req.lines],
    )
    ts = dt.datetime.now().replace(microsecond=0)
    xml = serialize(build_book(cover, cert, ts))
    return {
        "period": req.period,
        "operation_type": req.operation_type,
        "xml_base64": base64.b64encode(xml).decode("ascii"),
    }
