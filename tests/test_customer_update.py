"""Edición de cliente (PATCH /admin/customers/{id})."""

ADMIN = {"X-Admin-Key": "test-admin-key-0123456789"}


def _create(client, name="Demo", rut="76158145-7"):
    r = client.post("/admin/customers", json={"name": name, "rut": rut}, headers=ADMIN)
    assert r.status_code == 200, r.text
    return r.json()


def test_update_customer_name_and_environment(client, db):
    c = _create(client)
    key = c["key"]
    r = client.patch(
        f"/admin/customers/{c['id']}",
        json={"name": "Nuevo Nombre", "environment": "PRODUCTION"},
        headers=ADMIN,
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["name"] == "Nuevo Nombre"
    assert body["environment"] == "PRODUCTION"
    assert body["key"] == key  # el customerCode no cambia


def test_update_customer_partial_keeps_other_fields(client, db):
    c = _create(client, name="Original")
    r = client.patch(f"/admin/customers/{c['id']}", json={"rut": "77073851-2"}, headers=ADMIN)
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["name"] == "Original"  # no se tocó
    assert body["rut"] == "77073851-2"


def test_update_missing_customer_404(client, db):
    r = client.patch("/admin/customers/9999", json={"name": "x"}, headers=ADMIN)
    assert r.status_code == 404
