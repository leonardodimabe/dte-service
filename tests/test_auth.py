from tests.conftest import auth_header, make_user


def test_login_and_me(client, db):
    make_user(db, "admin@dimabe.cl", "secret", "superadmin")
    h = auth_header(client, "admin@dimabe.cl", "secret")
    r = client.get("/auth/me", headers=h)
    assert r.status_code == 200
    body = r.json()
    assert body["email"] == "admin@dimabe.cl"
    assert body["role"] == "superadmin"


def test_login_bad_password(client, db):
    make_user(db, "admin@dimabe.cl", "secret", "superadmin")
    r = client.post("/auth/login", json={"email": "admin@dimabe.cl", "password": "wrong"})
    assert r.status_code == 401


def test_me_requires_token(client):
    assert client.get("/auth/me").status_code == 401
    assert client.get("/auth/me", headers={"Authorization": "Bearer garbage"}).status_code == 401


def test_inactive_user_cannot_login(client, db):
    user = make_user(db, "x@dimabe.cl", "secret", "operator")
    user.is_active = False
    db.commit()
    r = client.post("/auth/login", json={"email": "x@dimabe.cl", "password": "secret"})
    assert r.status_code == 401
