"""Schemas de usuarios del portal."""

from __future__ import annotations

import datetime as dt

from pydantic import BaseModel, ConfigDict


class UserCreate(BaseModel):
    email: str
    password: str
    role: str  # superadmin | operator | auditor | client
    customer_id: int | None = None  # requerido si role == client


class UserActiveUpdate(BaseModel):
    is_active: bool


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: str
    role: str
    customer_id: int | None = None
    is_active: bool
    created_at: dt.datetime
    last_login: dt.datetime | None = None
