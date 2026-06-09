import base64

import pytest
from dte_chile import FoliosExhausted

from app.services import customer_service, folio_service
from tests.conftest import fake_caf_xml, make_customer


def _add_caf(db, customer, doc_type, folio_from, folio_to):
    xml_b64 = base64.b64encode(fake_caf_xml(doc_type, folio_from, folio_to)).decode()
    customer_service.add_caf(db, customer, xml_b64)


def test_next_folio_sequential_and_exhaustion(db):
    customer = make_customer(db)
    _add_caf(db, customer, 33, 1, 3)

    folios = [folio_service.next_folio(db, customer.id, 33)[0] for _ in range(3)]
    assert folios == [1, 2, 3]

    with pytest.raises(FoliosExhausted):
        folio_service.next_folio(db, customer.id, 33)


def test_next_folio_jumps_gap_between_cafs(db):
    customer = make_customer(db)
    _add_caf(db, customer, 33, 1, 2)
    _add_caf(db, customer, 33, 100, 101)

    assigned = [folio_service.next_folio(db, customer.id, 33)[0] for _ in range(4)]
    assert assigned == [1, 2, 100, 101]


def test_no_caf_raises(db):
    customer = make_customer(db)
    from dte_chile import FolioError

    with pytest.raises(FolioError):
        folio_service.next_folio(db, customer.id, 33)
