import datetime as dt

from dte_chile.rcv import RcvDocument

from app.security.service_codes import SERVICE_RCV
from app.services import customer_service, rcv_service
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


def test_cross_tenant_apikey_rejected(client, db, monkeypatch):
    """La apiKey de un cliente NO sirve con el customerCode de otro (BOLA)."""
    a = make_customer(db, rut="76158145-7", key="cust-a")
    grant(db, a, SERVICE_RCV, apikey="key-a")
    b = make_customer(db, rut="11111111-1", key="cust-b")
    grant(db, b, SERVICE_RCV, apikey="key-b")
    monkeypatch.setattr(rcv_service, "RCVClient", _FakeRcv)

    # apiKey de A con el customerCode de B → 401.
    r = client.post(
        "/rcv/documents", json=_PAYLOAD, headers={"customerCode": "cust-b", "apiKey": "key-a"}
    )
    assert r.status_code == 401
    # Cada uno con su propia credencial → 200.
    assert (
        client.post(
            "/rcv/documents", json=_PAYLOAD, headers={"customerCode": "cust-a", "apiKey": "key-a"}
        ).status_code
        == 200
    )


def test_revoked_service_denies_access(client, db, monkeypatch):
    """Revocar el servicio corta el acceso del tenant de inmediato."""
    c = make_customer(db)
    grant(db, c, SERVICE_RCV, apikey="secret")
    monkeypatch.setattr(rcv_service, "RCVClient", _FakeRcv)
    assert client.post("/rcv/documents", json=_PAYLOAD, headers=headers()).status_code == 200

    customer_service.revoke_service(db, c, SERVICE_RCV)
    assert client.post("/rcv/documents", json=_PAYLOAD, headers=headers()).status_code == 401


def test_tenant_auth_failures_rate_limited(client, db):
    """30 fallos de auth desde una IP → la IP queda bloqueada (429), incluso
    para un intento posterior con credenciales formalmente correctas."""
    make_customer(db)
    for _ in range(30):
        r = client.post("/rcv/documents", json=_PAYLOAD, headers=headers(customer_code="nope"))
        assert r.status_code == 401
    r = client.post("/rcv/documents", json=_PAYLOAD, headers=headers())
    assert r.status_code == 429


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
