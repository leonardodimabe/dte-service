"""Auditoría: escritura del access-log (RequestLog) y del audit de cambios."""

from __future__ import annotations

import datetime as dt

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

import app.db.session as db_session
from app.db.models import AdminAudit, RequestLog


def record_request(
    *,
    principal_type: str,
    principal_id: int | None,
    principal_role: str | None,
    service_code: str | None,
    method: str,
    path: str,
    request_id: str,
    ip: str | None,
    user_agent: str | None,
    status_code: int,
    outcome: str,
    latency_ms: int,
    meta: dict | None,
) -> None:
    """Inserta una línea de access-log (sesión propia, fuera del request)."""
    entry = RequestLog(
        principal_type=principal_type,
        principal_id=principal_id,
        principal_role=principal_role,
        service_code=service_code,
        method=method,
        path=path,
        request_id=request_id,
        ip=ip,
        user_agent=user_agent,
        status_code=status_code,
        outcome=outcome,
        latency_ms=latency_ms,
        meta=meta,
    )
    with db_session.SessionLocal() as db:
        db.add(entry)
        db.commit()


def record_change(
    db: Session,
    actor_user_id: int | None,
    action: str,
    target_type: str,
    target_id: str | None,
    summary: str,
    *,
    commit: bool = True,
) -> None:
    """Registra un cambio de datos maestros.

    Con ``commit=True`` (default) cierra la transacción: los routers llaman la
    mutación con ``commit=False`` y luego este con ``commit=True``, de modo que
    el cambio y su auditoría quedan en la MISMA transacción (atómicos).
    """
    db.add(
        AdminAudit(
            actor_user_id=actor_user_id,
            action=action,
            target_type=target_type,
            target_id=target_id,
            summary=summary,
        )
    )
    if commit:
        db.commit()


def list_requests(
    db: Session,
    *,
    customer_id: int | None = None,
    service_code: str | None = None,
    outcome: str | None = None,
    since: dt.datetime | None = None,
    limit: int = 100,
    offset: int = 0,
) -> list[RequestLog]:
    stmt = select(RequestLog)
    if customer_id is not None:  # scope cliente: solo sus peticiones
        stmt = stmt.where(
            RequestLog.principal_type == "customer", RequestLog.principal_id == customer_id
        )
    if service_code is not None:
        stmt = stmt.where(RequestLog.service_code == service_code)
    if outcome is not None:
        stmt = stmt.where(RequestLog.outcome == outcome)
    if since is not None:
        stmt = stmt.where(RequestLog.created_at >= since)
    stmt = stmt.order_by(RequestLog.id.desc()).limit(limit).offset(offset)
    return list(db.execute(stmt).scalars())


def list_changes(db: Session, *, limit: int = 100, offset: int = 0) -> list[AdminAudit]:
    stmt = select(AdminAudit).order_by(AdminAudit.id.desc()).limit(limit).offset(offset)
    return list(db.execute(stmt).scalars())


def purge_requests(db: Session, *, older_than_days: int) -> int:
    """Borra access-logs anteriores a N días (retención). Devuelve filas borradas.

    Pensado para un job periódico (ver ``scripts/purge_audit.py``): la tabla
    ``request_log`` crece una fila por petición y no debe crecer sin límite.
    """
    cutoff = dt.datetime.now(dt.UTC).replace(tzinfo=None) - dt.timedelta(days=older_than_days)
    result = db.execute(delete(RequestLog).where(RequestLog.created_at < cutoff))
    db.commit()
    return result.rowcount or 0  # type: ignore[attr-defined]
