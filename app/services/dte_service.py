"""Servicio de emisión de DTE: folio → build → firma → sobre → validar → enviar."""

from __future__ import annotations

import base64
import datetime as dt

from dte_chile.document_types import DTEType, ReferenceCode
from dte_chile.envelope import Cover, build_envelope, serialize
from dte_chile.models import DTE, Issuer, Item, Receiver, Reference
from dte_chile.signer import sign_document
from dte_chile.sii_client import Environment, SIIClient
from dte_chile.validation import Validator
from dte_chile.xml_builder import build_document
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db.models import Customer


def _reference(ref) -> Reference:
    return Reference(
        doc_type=ref.doc_type,
        folio=ref.folio,
        date=ref.date,
        code=ReferenceCode(ref.code) if ref.code is not None else None,
        reason=ref.reason,
    )


def issue(db: Session, customer: Customer, cert, req) -> dict:
    from app.services import folio_service

    settings = get_settings()
    folio, caf = folio_service.next_folio(db, customer.id, req.type)
    ts = dt.datetime.now().replace(microsecond=0)

    dte = DTE(
        type=DTEType(req.type),
        folio=folio,
        issue_date=req.issue_date,
        issuer=Issuer(**req.issuer.model_dump()),
        receiver=Receiver(**req.receiver.model_dump()),
        items=[Item(**item.model_dump()) for item in req.items],
        references=[_reference(r) for r in req.references],
    )

    signed = sign_document(build_document(dte, caf, ts), cert)
    cover = Cover(
        issuer_rut=dte.issuer.rut.value,
        sender_rut=cert.rut or dte.issuer.rut.value,
        resolution_date=customer.resolution_date,
        resolution_number=customer.resolution_number,
        subtotals=[(int(dte.type), 1)],
    )
    xml = serialize(build_envelope([signed], cover, cert, ts))

    if req.validate_xsd:
        Validator(settings.schemas_dir).validate(xml)

    submission = None
    if req.send:
        client = SIIClient(
            cert, Environment[customer.environment.name], timeout=settings.request_timeout_s
        )
        submission = client.send_dte(xml, dte.issuer.rut.value, cert.rut or dte.issuer.rut.value)

    return {
        "type": int(dte.type),
        "folio": folio,
        "xml_base64": base64.b64encode(xml).decode("ascii"),
        "submission": submission,
    }
