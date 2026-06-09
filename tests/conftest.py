"""Fixtures de test: BD sqlite en memoria + motor dte_chile faked.

Se configuran las env vars ANTES de importar la app (settings está cacheado).
"""

from __future__ import annotations

import datetime as dt
import os

from cryptography.fernet import Fernet

os.environ.setdefault("DTE_FERNET_KEYS", Fernet.generate_key().decode())
os.environ.setdefault("DTE_ADMIN_API_KEY", "test-admin")
os.environ.setdefault("DTE_DATABASE_URL", "sqlite://")

import pytest  # noqa: E402
from dte_chile.certificate import Certificate  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy import create_engine  # noqa: E402
from sqlalchemy.orm import sessionmaker  # noqa: E402
from sqlalchemy.pool import StaticPool  # noqa: E402

import app.db.models  # noqa: E402,F401
from app.core import crypto  # noqa: E402
from app.db.base import Base  # noqa: E402
from app.db.models import Customer, CustomerCertificate  # noqa: E402
from app.db.session import get_db  # noqa: E402
from app.main import app  # noqa: E402
from app.security.apikeys import hash_apikey  # noqa: E402
from app.services import customer_service  # noqa: E402

_engine = create_engine(
    "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
)
TestingSessionLocal = sessionmaker(bind=_engine, autoflush=False, expire_on_commit=False)
Base.metadata.create_all(_engine)


def _override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = _override_get_db


@pytest.fixture
def db():
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def client():
    return TestClient(app, raise_server_exceptions=False)


@pytest.fixture(autouse=True)
def _clean_db():
    yield
    with _engine.begin() as conn:
        for table in reversed(Base.metadata.sorted_tables):
            conn.execute(table.delete())


@pytest.fixture(autouse=True)
def fake_certificate(monkeypatch):
    """El certificado real se reemplaza por un stub (no se parsea un .pfx real)."""

    def _stub(data: bytes, password: str) -> Certificate:
        return Certificate(private_key_pem=b"x", cert_pem=b"x", rut="76158145-7")

    monkeypatch.setattr(Certificate, "from_pfx_bytes", classmethod(lambda cls, d, p: _stub(d, p)))
    yield


def make_customer(db, rut="76158145-7", key="cust-1") -> Customer:
    c = customer_service.create_customer(
        db,
        type(
            "D",
            (),
            {
                "name": "Demo",
                "key": key,
                "rut": rut,
                "environment": "CERTIFICATION",
                "resolution_number": 0,
                "resolution_date": dt.date(2014, 8, 22),
            },
        )(),
    )
    # Certificado dummy (cifrado); from_pfx_bytes está fakeado.
    db.add(
        CustomerCertificate(
            customer_id=c.id,
            file_base64=crypto.encrypt(b"dummy-pfx"),
            password=crypto.encrypt("pw"),
            due_date=dt.date.today() + dt.timedelta(days=365),
        )
    )
    db.commit()
    return c


def grant(db, customer, service_code, apikey="secret"):
    customer_service.grant_service(db, customer, service_code, apikey)


def headers(customer_code="cust-1", apikey="secret"):
    return {"customerCode": customer_code, "apiKey": apikey}


# CAF de juguete (sin llave real; load_caf_bytes solo parsea estructura).
def fake_caf_xml(doc_type=33, folio_from=1, folio_to=5, rut="76158145-7") -> bytes:
    return (
        f'<AUTORIZACION><CAF version="1.0"><DA>'
        f"<RE>{rut}</RE><RS>DEMO</RS><TD>{doc_type}</TD>"
        f"<RNG><D>{folio_from}</D><H>{folio_to}</H></RNG><FA>2026-01-01</FA>"
        f"<RSAPK><M>eA==</M><E>Aw==</E></RSAPK><IDK>100</IDK></DA>"
        f'<FRMA algoritmo="SHA1withRSA">eA==</FRMA></CAF>'
        f"<RSASK>-----BEGIN RSA PRIVATE KEY-----\nZHVtbXk=\n-----END RSA PRIVATE KEY-----</RSASK>"
        f"</AUTORIZACION>"
    ).encode()


__all__ = ["make_customer", "grant", "headers", "fake_caf_xml", "hash_apikey"]
