import base64

import pytest
from dte_chile.sii_client import SubmissionResult

from app.security.service_codes import SERVICE_BOOK
from app.services import book_service, sii_upload
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
    # Estos tests arman el libro; el envío al SII tiene los suyos.
    "send": False,
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


# --------------------------------------------------------------------------- #
#  Libro de Guías de Despacho (Res. Ex. N°154 / set 5038174)
# --------------------------------------------------------------------------- #
_GUIDES_PAYLOAD = {
    "period": "2026-11",
    "notification_folio": 5038174,
    "lines": [
        {
            "folio": 1,
            "date": "2026-11-03",
            "transfer_type": 5,
            "receiver_rut": "76158145-7",
            "receiver_name": "EMISOR",
        },
        {
            "folio": 2,
            "date": "2026-11-04",
            "transfer_type": 1,
            "receiver_rut": "77073851-2",
            "receiver_name": "CLIENTE",
            "net_amount": 2586065,
            "vat_amount": 491352,
            "total_amount": 3077417,
            "modified_amount": 3077417,
            "ref_doc_type": 33,
            "ref_folio": 120,
            "ref_date": "2026-11-10",
        },
        {"folio": 3, "voided": 2},
    ],
    # Estos tests arman el libro; el envío al SII tiene los suyos.
    "send": False,
}


@pytest.fixture
def fake_guide_book_engine(monkeypatch):
    monkeypatch.setattr(book_service, "build_guide_book", lambda cover, cert, ts: cover)
    monkeypatch.setattr(book_service, "serialize_guide_book", lambda x: b"<LibroGuia/>")


def test_build_guide_book(client, db, fake_guide_book_engine):
    customer = make_customer(db)
    grant(db, customer, SERVICE_BOOK)

    r = client.post("/books/guides", json=_GUIDES_PAYLOAD, headers=headers())
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["period"] == "2026-11"
    assert base64.b64decode(body["xml_base64"]) == b"<LibroGuia/>"


def test_guide_book_maps_transfer_and_void_codes(client, db, monkeypatch):
    """Los códigos del request llegan al motor como sus enums, no como int."""
    from dte_chile.document_types import TransferType
    from dte_chile.guide_book import VoidStatus

    captured = {}

    def _capture(cover, cert, ts):
        captured["cover"] = cover
        return cover

    monkeypatch.setattr(book_service, "build_guide_book", _capture)
    monkeypatch.setattr(book_service, "serialize_guide_book", lambda x: b"<LibroGuia/>")

    customer = make_customer(db)
    grant(db, customer, SERVICE_BOOK)
    r = client.post("/books/guides", json=_GUIDES_PAYLOAD, headers=headers())
    assert r.status_code == 200, r.text

    cover = captured["cover"]
    assert cover.notification_folio == 5038174
    assert cover.submission_type == "TOTAL"
    assert cover.lines[0].transfer_type is TransferType.INTERNAL
    assert cover.lines[1].ref_folio == 120
    assert cover.lines[2].voided is VoidStatus.AFTER_SENDING


def test_guide_book_requires_book_service(client, db):
    """Sin el servicio BOOK habilitado el cliente no resuelve: 401, como el resto."""
    make_customer(db)  # sin grant
    r = client.post("/books/guides", json=_GUIDES_PAYLOAD, headers=headers())
    assert r.status_code == 401, r.text


# --------------------------------------------------------------------------- #
#  Libro de Compras (set 5038172)
# --------------------------------------------------------------------------- #
_PURCHASE_PAYLOAD = {
    "period": "2026-08",
    "operation_type": "COMPRA",
    "proportionality_factor": 0.60,
    "lines": [
        {
            "doc_type": 30,
            "folio": 781,
            "date": "2026-08-10",
            "rut": "77073851-2",
            "business_name": "PROVEEDOR C",
            "net_amount": 30019,
            "common_use_vat": 5704,
            "total_amount": 35723,
        },
        {
            "doc_type": 33,
            "folio": 67,
            "date": "2026-08-10",
            "rut": "77073851-2",
            "business_name": "PROVEEDOR D",
            "net_amount": 11305,
            "non_recoverable_vat": [{"code": 4, "amount": 2148}],
            "total_amount": 13453,
        },
        {
            "doc_type": 46,
            "folio": 9,
            "date": "2026-08-10",
            "rut": "77073851-2",
            "business_name": "PROVEEDOR E",
            "net_amount": 10215,
            "retained_total_vat": 1941,
            "total_amount": 10215,
        },
    ],
    # Estos tests arman el libro; el envío al SII tiene los suyos.
    "send": False,
}


def test_purchase_book_maps_the_new_fields(client, db, monkeypatch):
    """Los campos de compras deben llegar al motor como sus dataclasses."""
    from dte_chile.book import NonRecoverableVat

    captured = {}
    monkeypatch.setattr(
        book_service, "build_book", lambda cover, cert, ts: captured.setdefault("cover", cover)
    )
    monkeypatch.setattr(book_service, "serialize", lambda x: b"<LibroCompraVenta/>")

    customer = make_customer(db)
    grant(db, customer, SERVICE_BOOK)
    r = client.post("/books", json=_PURCHASE_PAYLOAD, headers=headers())
    assert r.status_code == 200, r.text

    cover = captured["cover"]
    assert cover.operation_type == "COMPRA"
    assert cover.proportionality_factor == 0.60
    assert cover.lines[0].common_use_vat == 5704
    assert cover.lines[1].non_recoverable_vat == [NonRecoverableVat(code=4, amount=2148)]
    assert cover.lines[2].retained_total_vat == 1941


def test_proportionality_factor_must_be_a_fraction(client, db):
    customer = make_customer(db)
    grant(db, customer, SERVICE_BOOK)
    payload = dict(_PURCHASE_PAYLOAD, proportionality_factor=1.5)
    r = client.post("/books", json=payload, headers=headers())
    assert r.status_code == 422, r.text


# --------------------------------------------------------------------------- #
#  Envío al SII
# --------------------------------------------------------------------------- #
class _FakeSession:
    def close(self):
        pass


@pytest.fixture
def fake_sii(monkeypatch):
    """Captura lo que se sube, sin tocar la red."""
    seen: dict = {"uploads": []}

    class _FakeSII:
        def __init__(self, cert, environment, timeout=30):
            self.session = _FakeSession()

        def send_dte(self, xml, issuer_rut, sender_rut):
            seen["uploads"].append({"xml": xml, "issuer_rut": issuer_rut})
            return SubmissionResult(track_id="T555", status="0", detail="recibido")

    monkeypatch.setattr(sii_upload, "SIIClient", _FakeSII)
    return seen


def test_sales_book_is_uploaded_to_the_sii(client, db, fake_book_engine, fake_sii):
    """El set de certificación exige enviar el libro, no sólo construirlo."""
    grant(db, make_customer(db), SERVICE_BOOK)
    payload = {**_PAYLOAD, "send": True}

    r = client.post("/books", json=payload, headers=headers())
    assert r.status_code == 200, r.text
    assert r.json()["submission"]["track_id"] == "T555"
    assert len(fake_sii["uploads"]) == 1
    assert b"LibroCompraVenta" in fake_sii["uploads"][0]["xml"]


def test_guide_book_is_uploaded_to_the_sii(client, db, fake_guide_book_engine, fake_sii):
    grant(db, make_customer(db), SERVICE_BOOK)
    payload = {**_GUIDES_PAYLOAD, "send": True}

    r = client.post("/books/guides", json=payload, headers=headers())
    assert r.status_code == 200, r.text
    assert r.json()["submission"]["track_id"] == "T555"
    assert b"LibroGuia" in fake_sii["uploads"][0]["xml"]


def test_the_book_is_uploaded_under_the_customers_rut(client, db, fake_book_engine, fake_sii):
    customer = make_customer(db)
    grant(db, customer, SERVICE_BOOK)
    client.post("/books", json={**_PAYLOAD, "send": True}, headers=headers())
    assert fake_sii["uploads"][0]["issuer_rut"] == customer.rut


def test_not_sending_leaves_no_submission(client, db, fake_book_engine, fake_sii):
    grant(db, make_customer(db), SERVICE_BOOK)
    r = client.post("/books", json={**_PAYLOAD, "send": False}, headers=headers())
    assert r.json()["submission"] is None
    assert fake_sii["uploads"] == []
