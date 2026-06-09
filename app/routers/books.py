"""Endpoint del Libro de Compras y Ventas (IECV)."""

from __future__ import annotations

from dte_chile.certificate import Certificate
from fastapi import APIRouter, Depends

from app.core.concurrency import run_blocking
from app.db.models import Customer
from app.deps.auth import require_book
from app.deps.certificate import cert_book
from app.schemas.book import BookRequest, BookResponse
from app.services import book_service

router = APIRouter(prefix="/books", tags=["IECV"])


@router.post("", response_model=BookResponse)
async def build_book(
    req: BookRequest,
    customer: Customer = Depends(require_book),
    cert: Certificate = Depends(cert_book),
) -> BookResponse:
    result = await run_blocking(book_service.build, customer, cert, req)
    return BookResponse(**result)
