"""Schemas de claves de máquina (consumidores /admin tipo Odoo)."""

from __future__ import annotations

import datetime as dt

from pydantic import BaseModel, ConfigDict, Field


class MachineKeyCreate(BaseModel):
    name: str = Field(min_length=1)
    role: str  # operator | auditor


class MachineKeyOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    key_id: str  # prefijo público (no es secreto)
    role: str
    is_active: bool
    created_at: dt.datetime


class MachineKeyCreated(MachineKeyOut):
    api_key: str  # ``key_id.secret`` completo; se devuelve UNA sola vez
