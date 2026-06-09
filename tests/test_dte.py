import base64

import pytest
from dte_chile.sii_client import SubmissionResult

from app.security.service_codes import SERVICE_DTE
from app.services import customer_service, dte_service
from tests.conftest import fake_caf_xml, grant, headers, make_customer

_ISSUER = {
    "rut": "76158145-7",
    "business_name": "DEMO SPA",
    "activity": "Venta",
    "economic_activity": 471000,
    "address": "Calle 1",
    "commune": "Santiago",
    "city": "Santiago",
}
_RECEIVER = {
    "rut": "77073851-2",
    "business_name": "CLIENTE SPA",
    "activity": "Compra",
    "address": "Calle 2",
    "commune": "Santiago",
    "city": "Santiago",
}


def _payload(**over):
    base = {
        "type": 33,
        "issue_date": "2026-06-09",
        "issuer": _ISSUER,
        "receiver": _RECEIVER,
        "items": [{"name": "Producto", "quantity": 1, "unit_price": 1000, "exempt": False}],
        "references": [],
        "validate_xsd": False,
    }
    base.update(over)
    return base


@pytest.fixture
def fake_dte_engine(monkeypatch):
    """Reemplaza build/firma/sobre/serialización del motor por stubs."""
    monkeypatch.setattr(dte_service, "build_document", lambda *a: "DOC")
    monkeypatch.setattr(dte_service, "sign_document", lambda *a: "SIGNED")
    monkeypatch.setattr(dte_service, "build_envelope", lambda *a: "ENV")
    monkeypatch.setattr(dte_service, "serialize", lambda env: b"<EnvioDTE/>")


def _setup(db, doc_type=33, folio_from=1, folio_to=5):
    customer = make_customer(db)
    grant(db, customer, SERVICE_DTE)
    customer_service.add_caf(
        db, customer, base64.b64encode(fake_caf_xml(doc_type, folio_from, folio_to)).decode()
    )
    return customer


def test_issue_allocates_folio_without_send(client, db, fake_dte_engine):
    _setup(db)
    r = client.post("/dte/issue", json=_payload(send=False), headers=headers())
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["folio"] == 1
    assert body["type"] == 33
    assert body["submission"] is None
    assert base64.b64decode(body["xml_base64"]) == b"<EnvioDTE/>"


def test_issue_increments_folio_no_duplicates(client, db, fake_dte_engine):
    _setup(db)
    f1 = client.post("/dte/issue", json=_payload(send=False), headers=headers()).json()["folio"]
    f2 = client.post("/dte/issue", json=_payload(send=False), headers=headers()).json()["folio"]
    assert (f1, f2) == (1, 2)


def test_issue_with_send_returns_submission(client, db, fake_dte_engine, monkeypatch):
    _setup(db)

    class _FakeSII:
        def __init__(self, cert, environment, timeout=30):
            pass

        def send_dte(self, xml, issuer_rut, sender_rut):
            return SubmissionResult(track_id="T123", status="OK", detail="recibido")

    monkeypatch.setattr(dte_service, "SIIClient", _FakeSII)

    r = client.post("/dte/issue", json=_payload(send=True), headers=headers())
    assert r.status_code == 200, r.text
    assert r.json()["submission"]["track_id"] == "T123"


def test_issue_requires_dte_service(client, db, fake_dte_engine):
    make_customer(db)  # sin grant de DTE
    r = client.post("/dte/issue", json=_payload(send=False), headers=headers())
    assert r.status_code == 401
