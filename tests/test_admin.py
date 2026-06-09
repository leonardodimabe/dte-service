import base64
import datetime as dt

from app.security.service_codes import SERVICE_RCV
from app.services import certificate_service
from tests.conftest import fake_caf_xml

ADMIN = {"X-Admin-Key": "test-admin"}


def _create(client, key="c1", rut="76158145-7"):
    r = client.post(
        "/admin/customers",
        json={"name": "Demo", "key": key, "rut": rut},
        headers=ADMIN,
    )
    assert r.status_code == 200, r.text
    return r.json()["id"]


def test_admin_requires_key(client):
    r = client.post("/admin/customers", json={"name": "A", "key": "k", "rut": "76158145-7"})
    assert r.status_code == 422  # falta header X-Admin-Key


def test_admin_wrong_key(client):
    r = client.post(
        "/admin/customers",
        json={"name": "A", "key": "k", "rut": "76158145-7"},
        headers={"X-Admin-Key": "nope"},
    )
    assert r.status_code == 401


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
