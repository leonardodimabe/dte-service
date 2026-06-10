"""Test de integración: asignación concurrente de folios sin duplicados.

Requiere Postgres real (el ``SELECT ... FOR UPDATE`` no se ejercita en sqlite).
Se salta salvo que se defina ``DTE_TEST_POSTGRES_URL`` apuntando a una BD de
pruebas desechable, p. ej.:

    DTE_TEST_POSTGRES_URL=postgresql+psycopg://dte:dte@localhost:5432/dte_test \
        pytest tests/test_folios_concurrency.py
"""

from __future__ import annotations

import os
from concurrent.futures import ThreadPoolExecutor

import pytest

POSTGRES_URL = os.environ.get("DTE_TEST_POSTGRES_URL")

pytestmark = pytest.mark.skipif(
    not POSTGRES_URL, reason="define DTE_TEST_POSTGRES_URL para el test de concurrencia"
)


def test_concurrent_folio_allocation_no_duplicates():
    import base64

    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker

    from app.db.base import Base
    from app.services import customer_service, folio_service
    from tests.conftest import fake_caf_xml

    engine = create_engine(POSTGRES_URL, future=True)
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)

    n = 50
    with Session() as db:
        customer = customer_service.create_customer(
            db,
            type(
                "D",
                (),
                {
                    "name": "Demo",
                    "key": "conc-1",
                    "rut": "76158145-7",
                    "environment": "CERTIFICATION",
                    "resolution_number": 0,
                    "resolution_date": __import__("datetime").date(2014, 8, 22),
                },
            )(),
        )
        customer_service.add_caf(db, customer, base64.b64encode(fake_caf_xml(33, 1, n)).decode())
        customer_id = customer.id

    def allocate() -> int:
        with Session() as db:
            folio, _ = folio_service.next_folio(db, customer_id, 33)
            return folio

    with ThreadPoolExecutor(max_workers=10) as pool:
        folios = list(pool.map(lambda _: allocate(), range(n)))

    assert len(folios) == len(set(folios)), "se entregaron folios duplicados"
    assert sorted(folios) == list(range(1, n + 1))

    Base.metadata.drop_all(engine)
