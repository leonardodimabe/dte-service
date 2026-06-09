import base64
import datetime as dt

from app.security.service_codes import SERVICE_RCV
from app.services import certificate_service, rcv_service
from tests.conftest import auth_header, fake_caf_xml, make_customer, make_user
from tests.test_auth_rcv import _FakeRcv

ADMIN = {"X-Admin-Key": "test-admin"}


def _create(client, key="c1", rut="76158145-7"):
    r = client.post(
        "/admin/customers",
        json={"name": "Demo", "key": key, "rut": rut},
        headers=ADMIN,
    )
    assert r.status_code == 200, r.text
    return r.json()["id"]


def test_admin_requires_auth(client):
    r = client.post("/admin/customers", json={"name": "A", "key": "k", "rut": "76158145-7"})
    assert r.status_code == 401  # ni Bearer ni X-Admin-Key


def test_admin_wrong_key(client):
    r = client.post(
        "/admin/customers",
        json={"name": "A", "key": "k", "rut": "76158145-7"},
        headers={"X-Admin-Key": "nope"},
    )
    assert r.status_code == 401


def test_admin_via_operator_jwt(client, db):
    make_user(db, "op@dimabe.cl", "secret", "operator")
    h = auth_header(client, "op@dimabe.cl", "secret")
    r = client.post(
        "/admin/customers", json={"name": "Demo", "key": "jwtc", "rut": "76158145-7"}, headers=h
    )
    assert r.status_code == 200, r.text
    # el cambio quedó auditado con el actor (operador)
    changes = client.get("/audit/changes", headers=h).json()
    assert any(c["action"] == "customer.create" for c in changes)


def test_admin_auditor_cannot_write(client, db):
    make_user(db, "aud@dimabe.cl", "secret", "auditor")
    h = auth_header(client, "aud@dimabe.cl", "secret")
    r = client.post(
        "/admin/customers", json={"name": "A", "key": "k", "rut": "76158145-7"}, headers=h
    )
    assert r.status_code == 403  # auditor no escribe


def test_create_grant_and_caf(client):
    cid = _create(client)

    r = client.post(
        f"/admin/customers/{cid}/services",
        json={"service_code": SERVICE_RCV, "apikey": "k"},
        headers=ADMIN,
    )
    assert r.status_code == 200 and r.json()["granted"] is True

    r = client.post(
        f"/admin/customers/{cid}/caf",
        json={"xml_base64": base64.b64encode(fake_caf_xml(33, 1, 5)).decode()},
        headers=ADMIN,
    )
    assert r.status_code == 200, r.text
    assert r.json()["doc_type"] == 33 and r.json()["folio_to"] == 5


def test_upload_certificate(client, monkeypatch):
    cid = _create(client, key="c2")
    monkeypatch.setattr(certificate_service, "_expiry", lambda pfx, pw: dt.date(2030, 1, 1))

    r = client.post(
        f"/admin/customers/{cid}/certificate",
        json={"file_base64": base64.b64encode(b"dummy-pfx").decode(), "password": "pw"},
        headers=ADMIN,
    )
    assert r.status_code == 200, r.text
    assert r.json()["rut"] == "76158145-7"


def test_operator_rcv(client, db, monkeypatch):
    customer = make_customer(db)  # crea cliente + certificado (fakeado)
    monkeypatch.setattr(rcv_service, "RCVClient", _FakeRcv)

    r = client.post(
        f"/admin/customers/{customer.id}/rcv",
        json={"period": "202505", "operation": "COMPRA"},
        headers=ADMIN,
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["issuer_rut"] == "76158145-7"
    assert body["count"] == 1


def test_operator_rcv_requires_auth(client, db):
    customer = make_customer(db)
    r = client.post(
        f"/admin/customers/{customer.id}/rcv",
        json={"period": "202505", "operation": "COMPRA"},
    )
    assert r.status_code == 401  # ni Bearer ni X-Admin-Key


def test_auditor_can_read_but_not_write(client, db):
    make_user(db, "aud2@dimabe.cl", "secret", "auditor")
    h = auth_header(client, "aud2@dimabe.cl", "secret")
    assert client.get("/admin/customers", headers=h).status_code == 200  # lee
    r = client.post("/admin/customers", json={"name": "X", "key": "z", "rut": "1-9"}, headers=h)
    assert r.status_code == 403  # no escribe


def test_get_customer_and_404(client):
    cid = _create(client)
    assert client.get(f"/admin/customers/{cid}", headers=ADMIN).status_code == 200
    assert client.get("/admin/customers/99999", headers=ADMIN).status_code == 404


def test_duplicate_key_returns_409(client):
    _create(client, key="dup")
    r = client.post(
        "/admin/customers", json={"name": "X", "key": "dup", "rut": "76158145-7"}, headers=ADMIN
    )
    assert r.status_code == 409


def test_grant_rotation_and_revoke(client):
    cid = _create(client, key="gr")
    for _ in range(2):  # habilitar dos veces = rotación, sin 500
        r = client.post(
            f"/admin/customers/{cid}/services",
            json={"service_code": SERVICE_RCV, "apikey": "k"},
            headers=ADMIN,
        )
        assert r.status_code == 200, r.text

    svcs = client.get(f"/admin/customers/{cid}/services", headers=ADMIN).json()
    assert len(svcs) == 1 and svcs[0]["service_code"] == SERVICE_RCV

    assert (
        client.delete(f"/admin/customers/{cid}/services/{SERVICE_RCV}", headers=ADMIN).status_code
        == 200
    )
    assert client.get(f"/admin/customers/{cid}/services", headers=ADMIN).json() == []
    assert (
        client.delete(f"/admin/customers/{cid}/services/{SERVICE_RCV}", headers=ADMIN).status_code
        == 404
    )


def test_customer_cafs_listing(client):
    cid = _create(client, key="cafs")
    client.post(
        f"/admin/customers/{cid}/caf",
        json={"xml_base64": base64.b64encode(fake_caf_xml(33, 1, 5)).decode()},
        headers=ADMIN,
    )
    cafs = client.get(f"/admin/customers/{cid}/cafs", headers=ADMIN).json()
    assert len(cafs) == 1
    assert cafs[0]["doc_type"] == 33 and cafs[0]["folio_to"] == 5


def test_customer_certificates_listing(client, monkeypatch):
    cid = _create(client, key="certs")
    monkeypatch.setattr(certificate_service, "_expiry", lambda pfx, pw: dt.date(2030, 1, 1))
    client.post(
        f"/admin/customers/{cid}/certificate",
        json={"file_base64": base64.b64encode(b"x").decode(), "password": "pw"},
        headers=ADMIN,
    )
    certs = client.get(f"/admin/customers/{cid}/certificates", headers=ADMIN).json()
    assert len(certs) == 1 and certs[0]["expired"] is False
