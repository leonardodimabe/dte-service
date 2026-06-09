"""Consulta y export de auditoría (access-log y cambios)."""

from __future__ import annotations

import csv
import io

from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.db.models import RequestLog, User
from app.db.session import get_db
from app.schemas.audit import AdminAuditOut, RequestLogOut
from app.security.auth import get_current_user, require_admin_panel
from app.security.roles import Role
from app.services import audit_service

router = APIRouter(prefix="/audit", tags=["Auditoría"])

_CSV_FIELDS = [
    "id",
    "created_at",
    "principal_type",
    "principal_id",
    "principal_role",
    "service_code",
    "method",
    "path",
    "status_code",
    "outcome",
    "latency_ms",
    "ip",
]


def _csv_response(rows: list[RequestLog]) -> StreamingResponse:
    buffer = io.StringIO()
    writer = csv.DictWriter(buffer, fieldnames=_CSV_FIELDS, extrasaction="ignore")
    writer.writeheader()
    for row in rows:
        writer.writerow({f: getattr(row, f) for f in _CSV_FIELDS})
    buffer.seek(0)
    return StreamingResponse(
        iter([buffer.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=request_log.csv"},
    )


@router.get("/requests", response_model=list[RequestLogOut])
async def requests(
    service_code: str | None = Query(default=None),
    outcome: str | None = Query(default=None),
    limit: int = Query(default=100, le=1000),
    offset: int = Query(default=0, ge=0),
    fmt: str = Query(default="json", alias="format"),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    # Scope: el cliente solo ve SU consumo; los roles internos ven todo.
    customer_id = user.customer_id if user.role == Role.CLIENT else None
    rows = audit_service.list_requests(
        db,
        customer_id=customer_id,
        service_code=service_code,
        outcome=outcome,
        limit=limit,
        offset=offset,
    )
    if fmt == "csv":
        return _csv_response(rows)
    return [RequestLogOut.model_validate(r) for r in rows]


@router.get("/changes", response_model=list[AdminAuditOut])
async def changes(
    limit: int = Query(default=100, le=1000),
    offset: int = Query(default=0, ge=0),
    user: User = Depends(require_admin_panel),
    db: Session = Depends(get_db),
) -> list[AdminAuditOut]:
    rows = audit_service.list_changes(db, limit=limit, offset=offset)
    return [AdminAuditOut.model_validate(r) for r in rows]
