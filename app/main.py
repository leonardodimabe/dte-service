"""Punto de entrada de la aplicación FastAPI."""

from __future__ import annotations

import logging
import time
import uuid
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.concurrency import run_in_threadpool
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response

import app.db.session as db_session
from app.core.config import get_settings
from app.core.logging import request_id_var, setup_logging
from app.errors.handlers import register_handlers
from app.routers import admin, audit, auth, books, dte, exchange, health, rcv, users
from app.services import audit_service, user_service

logger = logging.getLogger(__name__)

# Rutas que NO se auditan (ruido / sin valor de trazabilidad).
_SKIP_PREFIXES = ("/docs", "/redoc", "/openapi", "/health", "/favicon")


def _outcome(status_code: int) -> str:
    if status_code < 400:
        return "ok"
    if status_code in (401, 403):
        return "denied"
    return "error"


def _clip(value: str | None, limit: int) -> str | None:
    """Trunca valores de origen externo al largo de su columna.

    Sin esto, un header sobredimensionado (User-Agent, X-Request-ID) o un path
    largo hacen fallar el INSERT y el request queda SIN access-log (evasión de
    auditoría controlada por el cliente).
    """
    return value[:limit] if value else value


def _log_request(request: Request, status_code: int, latency_ms: int, request_id: str) -> None:
    path = request.url.path
    if path.startswith(_SKIP_PREFIXES):
        return
    principal = getattr(request.state, "principal", None)  # (type, id, role) | None
    ptype, pid, prole = principal if principal else ("anon", None, None)
    try:
        audit_service.record_request(
            principal_type=ptype,
            principal_id=pid,
            principal_role=prole,
            service_code=getattr(request.state, "service_code", None),
            method=request.method,
            path=path[:300],
            request_id=request_id[:64],
            ip=_clip(request.client.host if request.client else None, 64),
            user_agent=_clip(request.headers.get("user-agent"), 300),
            status_code=status_code,
            outcome=_outcome(status_code),
            latency_ms=latency_ms,
            meta=getattr(request.state, "audit_meta", None),
        )
    except Exception:
        logger.exception("no se pudo escribir RequestLog")


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    if settings.superadmin_email and settings.superadmin_password:
        with db_session.SessionLocal() as db:
            user_service.seed_superadmin(
                db, settings.superadmin_email, settings.superadmin_password
            )
    yield


def create_app() -> FastAPI:
    settings = get_settings()
    setup_logging(settings.log_level)

    app = FastAPI(
        title="DTE Service",
        version="0.1.0",
        description="Motor dte_chile vía API multi-cliente",
        lifespan=lifespan,
    )

    @app.middleware("http")
    async def observability(request: Request, call_next) -> Response:
        rid = (request.headers.get("X-Request-ID") or uuid.uuid4().hex)[:64]
        token = request_id_var.set(rid)
        start = time.perf_counter()
        try:
            try:
                response = await call_next(request)
            except Exception:
                # Excepción no controlada → 500: dejarla en el access-log igual.
                await run_in_threadpool(
                    _log_request, request, 500, int((time.perf_counter() - start) * 1000), rid
                )
                raise
            response.headers["X-Request-ID"] = rid
            # En threadpool: el INSERT del access-log no debe bloquear el event loop.
            await run_in_threadpool(
                _log_request,
                request,
                response.status_code,
                int((time.perf_counter() - start) * 1000),
                rid,
            )
            return response
        finally:
            request_id_var.reset(token)

    for router in (
        health.router,
        auth.router,
        users.router,
        audit.router,
        rcv.router,
        dte.router,
        books.router,
        exchange.router,
        admin.router,
    ):
        app.include_router(router)

    register_handlers(app)

    # CORS para la SPA (otro origen). En dev se usa el proxy de Vite → puede ir vacío.
    if settings.cors_origin_list:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=settings.cors_origin_list,
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

    return app


app = create_app()
