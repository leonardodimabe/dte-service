"""Schemas de emisión de DTE."""

from __future__ import annotations

import datetime as dt
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class IssuerIn(BaseModel):
    rut: str
    business_name: str
    activity: str
    economic_activity: int
    address: str
    commune: str
    city: str = ""


class ReceiverIn(BaseModel):
    rut: str
    business_name: str
    activity: str
    address: str
    commune: str
    city: str = ""


class ItemIn(BaseModel):
    name: str
    quantity: float
    unit_price: int
    exempt: bool = False
    description: str = ""
    unit: str = ""


class ReferenceIn(BaseModel):
    doc_type: int
    folio: str
    date: dt.date
    code: int | None = None
    reason: str = ""


class DteIssueRequest(BaseModel):
    type: Literal[33, 34, 56, 61]
    issue_date: dt.date
    issuer: IssuerIn
    receiver: ReceiverIn
    items: list[ItemIn] = Field(min_length=1)
    references: list[ReferenceIn] = []
    send: bool = True  # subir a Maullín/Palena (según ambiente del cliente)
    validate_xsd: bool = True  # validar contra el XSD antes de enviar


class SubmissionResultOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    track_id: str | None = None
    status: str
    detail: str = ""


class DteIssueResponse(BaseModel):
    type: int
    folio: int
    xml_base64: str
    submission: SubmissionResultOut | None = None
