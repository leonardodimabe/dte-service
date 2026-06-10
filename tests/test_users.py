from tests.conftest import auth_header, make_customer, make_user


def _superadmin(client, db):
    make_user(db, "su@dimabe.cl", "secret", "superadmin")
    return auth_header(client, "su@dimabe.cl", "secret")


def test_create_user_requires_superadmin(client, db):
    make_user(db, "op@dimabe.cl", "secret", "operator")
    h = auth_header(client, "op@dimabe.cl", "secret")
    r = client.post(
        "/users",
        json={"email": "new@dimabe.cl", "password": "Secret-Pass-123", "role": "auditor"},
        headers=h,
    )
    assert r.status_code == 403


def test_create_and_list_users(client, db):
    h = _superadmin(client, db)
    r = client.post(
        "/users",
        json={"email": "aud@dimabe.cl", "password": "Secret-Pass-123", "role": "auditor"},
        headers=h,
    )
    assert r.status_code == 200, r.text
    emails = [u["email"] for u in client.get("/users", headers=h).json()]
    assert "aud@dimabe.cl" in emails


def test_client_user_requires_customer_id(client, db):
    h = _superadmin(client, db)
    r = client.post(
        "/users",
        json={"email": "c@dimabe.cl", "password": "Secret-Pass-123", "role": "client"},
        headers=h,
    )
    assert r.status_code == 400  # falta customer_id


def test_short_password_rejected(client, db):
    h = _superadmin(client, db)
    r = client.post(
        "/users", json={"email": "short@dimabe.cl", "password": "x", "role": "auditor"}, headers=h
    )
    assert r.status_code == 422  # política de longitud mínima


def test_invalid_email_rejected(client, db):
    h = _superadmin(client, db)
    r = client.post(
        "/users",
        json={"email": "no-es-email", "password": "Secret-Pass-123", "role": "auditor"},
        headers=h,
    )
    assert r.status_code == 422


def test_client_user_cannot_access_admin_or_users(client, db):
    """Escalamiento horizontal→vertical: un usuario 'client' no entra al panel."""
    c = make_customer(db)
    make_user(db, "cli@dimabe.cl", "secret", "client", customer_id=c.id)
    h = auth_header(client, "cli@dimabe.cl", "secret")
    assert client.get("/admin/customers", headers=h).status_code == 403
    assert client.get("/users", headers=h).status_code == 403


def test_cannot_deactivate_last_superadmin(client, db):
    su = make_user(db, "su@dimabe.cl", "secret", "superadmin")
    h = auth_header(client, "su@dimabe.cl", "secret")
    r = client.patch(f"/users/{su.id}/active", json={"is_active": False}, headers=h)
    assert r.status_code == 400
