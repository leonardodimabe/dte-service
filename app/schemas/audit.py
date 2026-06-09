"""Schemas de auditoría (access-log y cambios)."""

from __future__ import annotations

import datetime as dt

from pydantic import BaseModel, ConfigDict


class RequestLogOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    principal_type: str
    principal_id: int | None = None
    principal_role: str | None = None
    service_code: str | None = None
    method: str
    path: str
    request_id: str
    ip: str | None = None
    status_code: int
    outcome: str
    latency_ms: int
    meta: dict | None = None
    created_at: dt.datetime


class AdminAuditOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    actor_user_id: int | None = None
    action: str
    target_type: str
    target_id: str | None = None
    summary: str
    created_at: dt.datetime
