"""Tests del almacén de la clave tributaria del SII (cifrado, rotación)."""

import pytest

from app.errors.exceptions import DomainError
from app.services import sii_credential_service
from tests.conftest import make_customer


def test_store_and_resolve_round_trip(db):
    c = make_customer(db)
    sii_credential_service.store_sii_password(db, c, "clave-secreta-123")
    assert sii_credential_service.resolve_sii_password(db, c) == "clave-secreta-123"


def test_resolve_none_when_unset(db):
    c = make_customer(db)
    assert sii_credential_service.resolve_sii_password(db, c) is None


def test_store_rotates_existing(db):
    c = make_customer(db)
    sii_credential_service.store_sii_password(db, c, "vieja")
    sii_credential_service.store_sii_password(db, c, "nueva")
    assert sii_credential_service.resolve_sii_password(db, c) == "nueva"


def test_store_persists_encrypted(db):
    """La clave nunca se guarda en claro en la columna."""
    from app.db.models import CustomerSiiCredential

    c = make_customer(db)
    sii_credential_service.store_sii_password(db, c, "no-en-claro")
    row = db.query(CustomerSiiCredential).filter(CustomerSiiCredential.customer_id == c.id).first()
    assert row is not None
    assert "no-en-claro" not in row.password


def test_empty_password_rejected(db):
    c = make_customer(db)
    with pytest.raises(DomainError):
        sii_credential_service.store_sii_password(db, c, "  ")
