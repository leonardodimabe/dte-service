from app.security.service_codes import SERVICE_RCV
from app.services import rcv_service
from tests.conftest import auth_header, grant, headers, make_customer, make_user
from tests.test_auth_rcv import _FakeRcv


def _superadmin(client, db):
    make_user(db, "su@dimabe.cl", "secret", "superadmin")
    return auth_header(client, "su@dimabe.cl", "secret")


def test_requests_are_logged(client, db):
    h = _superadmin(client, db)
    client.get("/auth/me", headers=h)  # genera tráfico auditable

    r = client.get("/audit/requests", headers=h)
    assert r.status_code == 200
    paths = [x["path"] for x in r.json()]
    assert "/auth/me" in paths
    assert "/auth/login" in paths


def test_requests_csv_export(client, db):
    h = _superadmin(client, db)
    r = client.get("/audit/requests?format=csv", headers=h)
    assert r.status_code == 200
    assert "text/csv" in r.headers["content-type"]
    assert "principal_type" in r.text


def test_client_sees_only_own_consumption(client, db, monkeypatch):
    customer = make_customer(db)  # rut 76158145-7, key cust-1
    grant(db, customer, SERVICE_RCV)
    monkeypatch.setattr(rcv_service, "RCVClient", _FakeRcv)
    client.post(
        "/rcv/documents", json={"period": "202505", "operation": "COMPRA"}, headers=headers()
    )

    make_user(db, "cliente@x.cl", "secret", "client", customer_id=customer.id)
    h = auth_header(client, "cliente@x.cl", "secret")
    rows = client.get("/audit/requests", headers=h).json()

    # Solo ve filas de SU cliente (no las de otros ni las suyas de tipo 'user').
    assert rows  # hay al menos el consumo
    assert all(x["principal_type"] == "customer" and x["principal_id"] == customer.id for x in rows)
    assert any(x["path"] == "/rcv/documents" for x in rows)


def test_admin_changes_audited(client, db):
    h = _superadmin(client, db)
    client.post(
        "/users", json={"email": "aud@dimabe.cl", "password": "x", "role": "auditor"}, headers=h
    )
    r = client.get("/audit/changes", headers=h)
    assert r.status_code == 200
    assert "user.create" in [c["action"] for c in r.json()]
