"""Schemas de administración (clientes, certificados, CAF, servicios)."""

from __future__ import annotations

import datetime as dt
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.schemas.validators import normalize_rut


class CustomerCreate(BaseModel):
    name: str = Field(min_length=1)
    key: str = Field(min_length=1)  # customerCode (opaco)
    rut: str
    environment: Literal["CERTIFICATION", "PRODUCTION"] = "CERTIFICATION"
    resolution_number: int = 0
    resolution_date: dt.date = dt.date(2014, 8, 22)

    @field_validator("rut")
    @classmethod
    def _rut(cls, v: str) -> str:
        return normalize_rut(v)


class CustomerOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    key: str
    rut: str
    environment: str


class CertificateUpload(BaseModel):
    file_base64: str  # .pfx en base64
    password: str


class CertificateOut(BaseModel):
    id: int
    rut: str | None
    due_date: dt.date


class CafUpload(BaseModel):
    xml_base64: str  # archivo CAF (AUTORIZACION) en base64


class CafOut(BaseModel):
    id: int
    doc_type: int
    folio_from: int
    folio_to: int


class ServiceInfo(BaseModel):
    code: str
    name: str


class ServiceGrant(BaseModel):
    service_code: str
    apikey: str  # se devuelve UNA vez; en BD se guarda hasheada


class ServiceGrantOut(BaseModel):
    service_code: str
    granted: bool


class GrantedServiceOut(BaseModel):
    service_code: str
    name: str


class CertificateInfo(BaseModel):
    id: int
    due_date: dt.date
    created_at: dt.datetime
    expired: bool


class CafInfo(BaseModel):
    id: int
    doc_type: int
    folio_from: int
    folio_to: int
    exhausted: bool
    last_folio: int
