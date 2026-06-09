import base64

import pytest

from app.security.service_codes import SERVICE_BOOK
from app.services import book_service
from tests.conftest import grant, headers, make_customer

_PAYLOAD = {
    "period": "2026-05",
    "operation_type": "VENTA",
    "lines": [
        {
            "doc_type": 33,
            "folio": 1,
            "date": "2026-05-10",
            "rut": "77073851-2",
            "business_name": "CLIENTE",
            "net_amount": 1000,
            "vat_amount": 190,
            "total_amount": 1190,
        }
    ],
}


@pytest.fixture
def fake_book_engine(monkeypatch):
    monkeypatch.setattr(book_service, "build_book", lambda cover, cert, ts: "BOOK")
    monkeypatch.setattr(book_service, "serialize", lambda x: b"<LibroCompraVenta/>")


def test_build_book(client, db, fake_book_engine):
    customer = make_customer(db)
    grant(db, customer, SERVICE_BOOK)

    r = client.post("/books", json=_PAYLOAD, headers=headers())
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["operation_type"] == "VENTA"
    assert base64.b64decode(body["xml_base64"]) == b"<LibroCompraVenta/>"
