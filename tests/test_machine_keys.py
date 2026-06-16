from tests.conftest import auth_header, make_user


def _su(client, db):
    make_user(db, "su@dimabe.cl", "secret", "superadmin")
    return auth_header(client, "su@dimabe.cl", "secret")


def _create_key(client, h, name="odoo", role="operator"):
    r = client.post("/machine-keys", json={"name": name, "role": role}, headers=h)
    assert r.status_code == 200, r.text
    return r.json()


def test_create_requires_superadmin(client, db):
    make_user(db, "op@dimabe.cl", "secret", "operator")
    h = auth_header(client, "op@dimabe.cl", "secret")
    r = client.post("/machine-keys", json={"name": "x", "role": "operator"}, headers=h)
    assert r.status_code == 403


def test_create_and_use_operator_key(client, db):
    h = _su(client, db)
    key = _create_key(client, h, role="operator")
    assert "." in key["api_key"] and key["key_id"] in key["api_key"]

    # La clave escribe en /admin (crear cliente).
    r = client.post(
        "/admin/customers",
        json={"name": "A", "key": "k1", "rut": "76158145-7"},
        headers={"X-Admin-Key": key["api_key"]},
    )
    assert r.status_code == 200, r.text


def test_auditor_key_reads_but_cannot_write(client, db):
    h = _su(client, db)
    key = _create_key(client, h, name="ro", role="auditor")
    hk = {"X-Admin-Key": key["api_key"]}
    assert client.get("/admin/customers", headers=hk).status_code == 200
    r = client.post(
        "/admin/customers", json={"name": "A", "key": "k2", "rut": "76158145-7"}, headers=hk
    )
    assert r.status_code == 403  # auditor no escribe


def test_invalid_role_rejected(client, db):
    h = _su(client, db)
    r = client.post("/machine-keys", json={"name": "x", "role": "superadmin"}, headers=h)
    assert r.status_code == 400


def test_revoke_disables_key(client, db):
    h = _su(client, db)
    key = _create_key(client, h, name="tmp", role="operator")
    hk = {"X-Admin-Key": key["api_key"]}
    assert client.get("/admin/customers", headers=hk).status_code == 200

    assert client.delete(f"/machine-keys/{key['id']}", headers=h).status_code == 200
    assert client.get("/admin/customers", headers=hk).status_code == 401


def test_revoked_key_excluded_from_list_and_restorable(client, db):
    h = _su(client, db)
    key = _create_key(client, h, name="tmp2", role="operator")
    hk = {"X-Admin-Key": key["api_key"]}
    client.delete(f"/machine-keys/{key['id']}", headers=h)
    assert client.get("/admin/customers", headers=hk).status_code == 401
    # revocada: fuera del listado por defecto, presente con include_deleted
    assert all(k["id"] != key["id"] for k in client.get("/machine-keys", headers=h).json())
    arch = client.get("/machine-keys?include_deleted=true", headers=h).json()
    assert any(k["id"] == key["id"] and k["deleted_at"] for k in arch)
    # restaurar reactiva la clave
    assert client.post(f"/machine-keys/{key['id']}/restore", headers=h).status_code == 200
    assert client.get("/admin/customers", headers=hk).status_code == 200


def test_list_never_exposes_secret(client, db):
    h = _su(client, db)
    _create_key(client, h, name="a", role="operator")
    keys = client.get("/machine-keys", headers=h).json()
    assert any(k["name"] == "a" for k in keys)
    assert all("api_key" not in k and "secret_hash" not in k for k in keys)


def test_bad_machine_key_returns_401(client, db):
    r = client.post(
        "/admin/customers",
        json={"name": "A", "key": "k", "rut": "76158145-7"},
        headers={"X-Admin-Key": "abcd1234.invalido"},
    )
    assert r.status_code == 401


def test_env_admin_key_still_works(client, db):
    # Compat: la X-Admin-Key de entorno (bootstrap) sigue válida.
    r = client.post(
        "/admin/customers",
        json={"name": "Env", "key": "kenv", "rut": "76158145-7"},
        headers={"X-Admin-Key": "test-admin-key-0123456789"},
    )
    assert r.status_code == 200, r.text


def test_machine_key_create_is_audited(client, db):
    h = _su(client, db)
    _create_key(client, h, name="audited", role="operator")
    changes = client.get("/audit/changes", headers=h).json()
    assert any(c["action"] == "machine_key.create" for c in changes)
