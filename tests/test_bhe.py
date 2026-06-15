"""Tests del endpoint BHE (auth de tenant, clave requerida, shape del response)."""

import datetime as dt

from dte_chile.bhe import BheDocument

from app.security.service_codes import SERVICE_BHE
from app.services import bhe_service, sii_credential_service
from tests.conftest import grant, headers, make_customer

_PAYLOAD = {"period": "202605"}


class _FakeBhe:
    def __init__(self, rut, password):
        assert rut and password  # se resuelven del tenant + clave guardada

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def fetch_received(self, year, month):
        return [
            BheDocument(
                issuer_rut="12345678-5",
                issuer_name="Juan Perez Consultor",
                folio=1001,
                issue_date=dt.date(year, month, 1),
                gross_amount=1_000_000,
                retention_amount=152_500,
                net_amount=847_500,
                status="vigente",
                period=f"{year:04d}-{month:02d}",
            )
        ]


def _set_key(db, customer, password="clave-sii"):
    sii_credential_service.store_sii_password(db, customer, password)


def test_missing_headers_returns_422(client, db):
    make_customer(db)
    r = client.post("/bhe/received", json=_PAYLOAD)
    assert r.status_code == 422


def test_bad_apikey_returns_401(client, db):
    c = make_customer(db)
    grant(db, c, SERVICE_BHE, apikey="secret")
    r = client.post("/bhe/received", json=_PAYLOAD, headers=headers(apikey="wrong"))
    assert r.status_code == 401


def test_customer_without_service_returns_401(client, db):
    make_customer(db)  # sin grant de BHE
    r = client.post("/bhe/received", json=_PAYLOAD, headers=headers())
    assert r.status_code == 401


def test_without_sii_key_returns_409(client, db):
    c = make_customer(db)
    grant(db, c, SERVICE_BHE, apikey="secret")  # servicio ok, pero sin clave tributaria
    r = client.post("/bhe/received", json=_PAYLOAD, headers=headers())
    assert r.status_code == 409


def test_bhe_received_ok(client, db, monkeypatch):
    c = make_customer(db)
    grant(db, c, SERVICE_BHE, apikey="secret")
    _set_key(db, c)
    monkeypatch.setattr(bhe_service, "BheClient", _FakeBhe)

    r = client.post("/bhe/received", json=_PAYLOAD, headers=headers())
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["count"] == 1
    assert body["receiver_rut"] == "76158145-7"  # del cliente, no del body
    doc = body["documents"][0]
    assert doc["folio"] == 1001
    assert doc["gross_amount"] == 1_000_000
    assert doc["net_amount"] == 847_500
    assert doc["status"] == "vigente"


def test_cross_tenant_apikey_rejected(client, db, monkeypatch):
    """La apiKey de un cliente NO sirve con el customerCode de otro (BOLA)."""
    a = make_customer(db, rut="76158145-7", key="cust-a")
    grant(db, a, SERVICE_BHE, apikey="key-a")
    _set_key(db, a)
    b = make_customer(db, rut="11111111-1", key="cust-b")
    grant(db, b, SERVICE_BHE, apikey="key-b")
    _set_key(db, b)
    monkeypatch.setattr(bhe_service, "BheClient", _FakeBhe)

    r = client.post(
        "/bhe/received", json=_PAYLOAD, headers={"customerCode": "cust-b", "apiKey": "key-a"}
    )
    assert r.status_code == 401
    assert (
        client.post(
            "/bhe/received", json=_PAYLOAD, headers={"customerCode": "cust-a", "apiKey": "key-a"}
        ).status_code
        == 200
    )
