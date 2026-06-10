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
from app.core.logging import request_id_var
from app.db.models import Customer
from app.errors.exceptions import DomainError


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

    # El emisor es siempre el cliente resuelto por el tenant (mismo criterio que
    # RCV/libros). Validar ANTES de asignar folio: un mismatch no debe quemarlo.
    if req.issuer.rut != customer.rut:
        raise DomainError(
            f"El RUT emisor ({req.issuer.rut}) no corresponde al cliente ({customer.rut})."
        )

    settings = get_settings()
    ts = dt.datetime.now().replace(microsecond=0)

    # Construir los componentes (que validan la entrada) ANTES de asignar el
    # folio: una entrada malformada no debe quemar un folio del CAF.
    issuer = Issuer(**req.issuer.model_dump())
    receiver = Receiver(**req.receiver.model_dump())
    items = [Item(**item.model_dump()) for item in req.items]
    references = [_reference(r) for r in req.references]

    folio, caf = folio_service.next_folio(db, customer.id, req.type, request_id_var.get())
    try:
        dte = DTE(
            type=DTEType(req.type),
            folio=folio,
            issue_date=req.issue_date,
            issuer=issuer,
            receiver=receiver,
            items=items,
            references=references,
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
            submission = client.send_dte(
                xml, dte.issuer.rut.value, cert.rut or dte.issuer.rut.value
            )
    except Exception:
        # El folio ya se consumió; déjalo trazado como quemado sin documento.
        folio_service.mark_assignment(db, customer.id, req.type, folio, "failed")
        raise

    folio_service.mark_assignment(db, customer.id, req.type, folio, "issued")
    return {
        "type": int(dte.type),
        "folio": folio,
        "xml_base64": base64.b64encode(xml).decode("ascii"),
        "submission": submission,
    }
