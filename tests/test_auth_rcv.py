import datetime as dt

from dte_chile.rcv import RcvDocument

from app.security.service_codes import SERVICE_RCV
from app.services import rcv_service
from tests.conftest import grant, headers, make_customer

_PAYLOAD = {"period": "202505", "operation": "COMPRA"}


class _FakeRcv:
    def __init__(self, cert):
        pass

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def documents(self, rut, period, operation):
        return [
            RcvDocument(
                operation=operation,
                state="REGISTRO",
                doc_type=33,
                folio=1,
                counterpart_rut="77073851-2",
                counterpart_name="STARLINK CHILE SPA",
                date=dt.date(2025, 5, 15),
                exempt_amount=0,
                net_amount=197479,
                vat_amount=37521,
                total_amount=235000,
                reception_date=None,
            )
        ]


def test_missing_headers_returns_422(client, db):
    make_customer(db)
    r = client.post("/rcv/documents", json=_PAYLOAD)
    assert r.status_code == 422


def test_bad_apikey_returns_401(client, db):
    c = make_customer(db)
    grant(db, c, SERVICE_RCV, apikey="secret")
    r = client.post("/rcv/documents", json=_PAYLOAD, headers=headers(apikey="wrong"))
    assert r.status_code == 401


def test_customer_without_service_returns_401(client, db):
    make_customer(db)  # sin grant de RCV
    r = client.post("/rcv/documents", json=_PAYLOAD, headers=headers())
    assert r.status_code == 401


def test_rcv_documents_ok(client, db, monkeypatch):
    c = make_customer(db)
    grant(db, c, SERVICE_RCV, apikey="secret")
    monkeypatch.setattr(rcv_service, "RCVClient", _FakeRcv)

    r = client.post("/rcv/documents", json=_PAYLOAD, headers=headers())
    assert r.status_code == 200
    body = r.json()
    assert body["count"] == 1
    assert body["issuer_rut"] == "76158145-7"  # tomado del cliente, no del body
    doc = body["documents"][0]
    assert doc["doc_type"] == 33 and doc["total_amount"] == 235000
    assert doc["counterpart_rut"] == "77073851-2"
