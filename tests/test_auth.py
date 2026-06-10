import datetime as dt

import jwt

from app.core.config import get_settings
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


def test_login_sets_httponly_cookie(client, db):
    make_user(db, "ck@dimabe.cl", "secret", "superadmin")
    r = client.post("/auth/login", json={"email": "ck@dimabe.cl", "password": "secret"})
    assert r.status_code == 200
    set_cookie = r.headers.get("set-cookie", "")
    assert "access_token=" in set_cookie
    assert "httponly" in set_cookie.lower()
    assert "samesite=strict" in set_cookie.lower()


def test_cookie_authenticates_without_bearer(client, db):
    """Tras el login, la cookie (en el jar del cliente) basta para /auth/me."""
    make_user(db, "ck2@dimabe.cl", "secret", "operator")
    client.post("/auth/login", json={"email": "ck2@dimabe.cl", "password": "secret"})
    r = client.get("/auth/me")  # sin header Authorization → usa la cookie
    assert r.status_code == 200
    assert r.json()["email"] == "ck2@dimabe.cl"


def test_logout_clears_cookie_and_revokes_access(client, db):
    make_user(db, "ck3@dimabe.cl", "secret", "superadmin")
    client.post("/auth/login", json={"email": "ck3@dimabe.cl", "password": "secret"})
    assert client.get("/auth/me").status_code == 200

    r = client.post("/auth/logout")
    assert r.status_code == 204
    client.cookies.clear()  # el navegador descartaría la cookie borrada
    assert client.get("/auth/me").status_code == 401


def test_login_unknown_email_401(client, db):
    """Email inexistente → 401 (ejercita la verificación señuelo de tiempo constante)."""
    r = client.post("/auth/login", json={"email": "ghost@nope.cl", "password": "whatever"})
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


def test_expired_token_rejected(client, db):
    """Un JWT con exp en el pasado debe rechazarse con 401."""
    make_user(db, "exp@dimabe.cl", "secret", "superadmin")
    secret = get_settings().jwt_secret
    now = dt.datetime.now(dt.UTC)
    token = jwt.encode(
        {
            "sub": "1",
            "role": "superadmin",
            "cid": None,
            "iat": now - dt.timedelta(hours=2),
            "exp": now - dt.timedelta(hours=1),
        },
        secret,
        algorithm="HS256",
    )
    r = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 401


def test_login_rate_limited_after_10_attempts(client, db):
    """Fuerza bruta: el intento 11 desde la misma IP en la ventana es 429,
    incluso con la password correcta."""
    make_user(db, "rl@dimabe.cl", "secret", "operator")
    for _ in range(10):
        r = client.post("/auth/login", json={"email": "rl@dimabe.cl", "password": "wrong"})
        assert r.status_code == 401
    r = client.post("/auth/login", json={"email": "rl@dimabe.cl", "password": "secret"})
    assert r.status_code == 429
