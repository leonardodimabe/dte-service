"""Endpoints de emisión de DTE."""

from __future__ import annotations

from dte_chile.certificate import Certificate
from dte_chile.sii_client import Environment, SIIClient
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.concurrency import run_blocking
from app.db.models import Customer
from app.db.session import get_db
from app.deps.auth import require_dte
from app.deps.certificate import cert_dte
from app.schemas.dte import DteIssueRequest, DteIssueResponse, SubmissionResultOut
from app.services import dte_service

router = APIRouter(prefix="/dte", tags=["DTE"])


@router.post("/issue", response_model=DteIssueResponse)
async def issue(
    req: DteIssueRequest,
    customer: Customer = Depends(require_dte),
    cert: Certificate = Depends(cert_dte),
    db: Session = Depends(get_db),
) -> DteIssueResponse:
    result = await run_blocking(dte_service.issue, db, customer, cert, req)
    submission = result["submission"]
    return DteIssueResponse(
        type=result["type"],
        folio=result["folio"],
        xml_base64=result["xml_base64"],
        submission=SubmissionResultOut.model_validate(submission) if submission else None,
    )


@router.get("/status/{track_id}", response_model=SubmissionResultOut)
async def status(
    track_id: str,
    customer: Customer = Depends(require_dte),
    cert: Certificate = Depends(cert_dte),
) -> SubmissionResultOut:
    client = SIIClient(cert, Environment[customer.environment.name])
    res = await run_blocking(client.query_status, track_id, customer.rut)
    return SubmissionResultOut.model_validate(res)
