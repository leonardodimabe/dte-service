"""Punto de entrada de la aplicación FastAPI."""

from __future__ import annotations

import uuid

from fastapi import FastAPI, Request
from fastapi.responses import Response

from app.core.config import get_settings
from app.core.logging import request_id_var, setup_logging
from app.errors.handlers import register_handlers
from app.routers import admin, books, dte, exchange, health, rcv


def create_app() -> FastAPI:
    settings = get_settings()
    setup_logging(settings.log_level)

    app = FastAPI(
        title="DTE Service", version="0.1.0", description="Motor dte_chile vía API multi-cliente"
    )

    @app.middleware("http")
    async def add_request_id(request: Request, call_next) -> Response:
        rid = request.headers.get("X-Request-ID") or uuid.uuid4().hex
        token = request_id_var.set(rid)
        try:
            response = await call_next(request)
        finally:
            request_id_var.reset(token)
        response.headers["X-Request-ID"] = rid
        return response

    for router in (
        health.router,
        rcv.router,
        dte.router,
        books.router,
        exchange.router,
        admin.router,
    ):
        app.include_router(router)

    register_handlers(app)
    return app


app = create_app()
