import base64

import pytest

from app.security.service_codes import SERVICE_EXCHANGE
from app.services import exchange_service
from tests.conftest import grant, headers, make_customer


@pytest.fixture
def fake_exchange_engine(monkeypatch):
    monkeypatch.setattr(exchange_service, "parse_envelope", lambda data: "ENV")
    monkeypatch.setattr(exchange_service, "build_receipt_acknowledgment", lambda env, cert, ts: "X")
    monkeypatch.setattr(exchange_service, "build_result_response", lambda *a, **k: "X")
    monkeypatch.setattr(exchange_service, "serialize", lambda x: b"<RespuestaDTE/>")


def _setup(db):
    customer = make_customer(db)
    grant(db, customer, SERVICE_EXCHANGE)


def test_acknowledgment(client, db, fake_exchange_engine):
    _setup(db)
    payload = {"envelope_base64": base64.b64encode(b"<EnvioDTE/>").decode()}
    r = client.post("/exchange/ack", json=payload, headers=headers())
    assert r.status_code == 200, r.text
    assert base64.b64decode(r.json()["xml_base64"]) == b"<RespuestaDTE/>"


def test_result_rejection(client, db, fake_exchange_engine):
    _setup(db)
    payload = {
        "envelope_base64": base64.b64encode(b"<EnvioDTE/>").decode(),
        "accept": False,
        "rejection_label": "monto incorrecto",
    }
    r = client.post("/exchange/result", json=payload, headers=headers())
    assert r.status_code == 200, r.text
    assert base64.b64decode(r.json()["xml_base64"]) == b"<RespuestaDTE/>"
