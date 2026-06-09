"""Mapeo de la jerarquía ``DteError`` del motor → códigos HTTP + body uniforme."""

from __future__ import annotations

from dte_chile import FolioError, FoliosExhausted
from dte_chile.errors import (
    DteError,
    RcvError,
    SiiAuthError,
    SiiError,
    SiiUploadError,
)
from dte_chile.validation import ValidationError, XSDNotAvailable
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.core.logging import request_id_var
from app.schemas.common import ErrorBody, ErrorResponse

# Orden importa: del más específico al más general (se evalúa con isinstance).
_STATUS: list[tuple[type[Exception], int]] = [
    (ValidationError, 422),
    (XSDNotAvailable, 503),
    (FoliosExhausted, 409),
    (FolioError, 409),
    (SiiAuthError, 502),
    (SiiUploadError, 502),
    (RcvError, 502),
    (SiiError, 502),
    (DteError, 500),
]


def _status_for(exc: Exception) -> int:
    for typ, status in _STATUS:
        if isinstance(exc, typ):
            return status
    return 500


def _body(exc: Exception, details: list[str]) -> dict:
    return ErrorResponse(
        error=ErrorBody(
            type=type(exc).__name__,
            message=str(exc),
            details=details,
            request_id=request_id_var.get(),
        )
    ).model_dump()


async def _dte_error_handler(request: Request, exc: Exception) -> JSONResponse:
    details = list(getattr(exc, "errors", []) or [])
    return JSONResponse(status_code=_status_for(exc), content=_body(exc, details))


async def _validation_handler(request: Request, exc: Exception) -> JSONResponse:
    details = [f"{'.'.join(map(str, e['loc']))}: {e['msg']}" for e in exc.errors()]  # type: ignore[attr-defined]
    return JSONResponse(status_code=422, content=_body(exc, details))


def register_handlers(app: FastAPI) -> None:
    app.add_exception_handler(DteError, _dte_error_handler)
    app.add_exception_handler(RequestValidationError, _validation_handler)
