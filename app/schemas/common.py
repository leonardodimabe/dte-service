"""Schemas comunes (cuerpo de error estándar)."""

from __future__ import annotations

from pydantic import BaseModel


class ErrorBody(BaseModel):
    type: str
    message: str
    details: list[str] = []
    request_id: str = "-"


class ErrorResponse(BaseModel):
    error: ErrorBody
