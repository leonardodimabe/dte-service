"""Soft delete de maestros: clientes y usuarios (enforcement + restore + guardas)."""

from app.security.service_codes import SERVICE_RCV
from app.services import rcv_service
from tests.conftest import auth_header, grant, headers, make_customer, make_user
from tests.test_auth_rcv import _FakeRcv

ADMIN = {"X-Admin-Key": "test-admin-key-0123456789"}
RCV = {"period": "202505", "operation": "COMPRA"}


def _login(client, email, password="secret"):
    return client.post("/auth/login", json={"email": email, "password": password}).status_code


# ----- Clientes -----
def test_deleted_customer_excluded_from_default_list(client, db):
    c = make_customer(db)
    client.delete(f"/admin/customers/{c.id}", headers=ADMIN)
    listed = client.get("/admin/customers", headers=ADMIN).json()
    assert all(x["id"] != c.id for x in listed)
    archived = client.get("/admin/customers?include_deleted=true", headers=ADMIN).json()
    row = next(x for x in archived if x["id"] == c.id)
    assert row["deleted_at"] is not None


def test_deleted_customer_cannot_authenticate(client, db, monkeypatch):
    c = make_customer(db)
    grant(db, c, SERVICE_RCV, apikey="secret")
    monkeypatch.setattr(rcv_service, "RCVClient", _FakeRcv)
    assert client.post("/rcv/documents", json=RCV, headers=headers()).status_code == 200
    client.delete(f"/admin/customers/{c.id}", headers=ADMIN)
    assert client.post("/rcv/documents", json=RCV, headers=headers()).status_code == 401


def test_restore_customer_reactivates(client, db, monkeypatch):
    c = make_customer(db)
    grant(db, c, SERVICE_RCV, apikey="secret")
    monkeypatch.setattr(rcv_service, "RCVClient", _FakeRcv)
    client.delete(f"/admin/customers/{c.id}", headers=ADMIN)
    assert client.post("/rcv/documents", json=RCV, headers=headers()).status_code == 401
    r = client.post(f"/admin/customers/{c.id}/restore", headers=ADMIN)
    assert r.status_code == 200 and r.json()["deleted_at"] is None
    assert client.post("/rcv/documents", json=RCV, headers=headers()).status_code == 200


# ----- Usuarios -----
def test_deleted_user_cannot_login_and_restore(client, db):
    make_user(db, "sa@dimabe.cl", "secret", "superadmin")
    op = make_user(db, "op2@dimabe.cl", "secret", "operator")
    h = auth_header(client, "sa@dimabe.cl", "secret")
    assert _login(client, "op2@dimabe.cl") == 200
    assert client.delete(f"/users/{op.id}", headers=h).status_code == 200
    assert _login(client, "op2@dimabe.cl") == 401  # archivado no inicia sesión
    assert all(u["id"] != op.id for u in client.get("/users", headers=h).json())
    assert client.post(f"/users/{op.id}/restore", headers=h).status_code == 200
    assert _login(client, "op2@dimabe.cl") == 200


def test_cannot_delete_last_superadmin(client, db):
    sa = make_user(db, "only@dimabe.cl", "secret", "superadmin")
    h = auth_header(client, "only@dimabe.cl", "secret")
    assert client.delete(f"/users/{sa.id}", headers=h).status_code == 400
