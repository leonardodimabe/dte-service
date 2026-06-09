"""Administración de clientes, servicios habilitados y CAF (operaciones de BD)."""

from __future__ import annotations

import base64

from dte_chile.caf import load_caf_bytes
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core import crypto
from app.db.models import Caf, Customer, CustomerService, Service, SiiEnvironment
from app.security.apikeys import hash_apikey
from app.security.service_codes import ALL_SERVICES
from app.services import folio_service


def list_customers(db: Session) -> list[Customer]:
    return list(db.execute(select(Customer).order_by(Customer.id)).scalars())


def create_customer(db: Session, data) -> Customer:
    customer = Customer(
        name=data.name,
        key=data.key,
        rut=data.rut,
        environment=SiiEnvironment(data.environment),
        resolution_number=data.resolution_number,
        resolution_date=data.resolution_date,
    )
    db.add(customer)
    db.commit()
    db.refresh(customer)
    return customer


def grant_service(db: Session, customer: Customer, service_code: str, apikey: str) -> None:
    if service_code not in ALL_SERVICES:
        raise ValueError(f"service_code desconocido: {service_code}")
    service = db.query(Service).filter(Service.code == service_code).first()
    if service is None:
        service = Service(code=service_code, name=ALL_SERVICES[service_code])
        db.add(service)
        db.flush()
    db.add(
        CustomerService(
            customer_id=customer.id, service_id=service.id, apikey_hash=hash_apikey(apikey)
        )
    )
    db.commit()


def add_caf(db: Session, customer: Customer, xml_base64: str) -> Caf:
    raw = base64.b64decode(xml_base64)
    parsed = load_caf_bytes(raw)  # valida + extrae rango/tipo
    row = Caf(
        customer_id=customer.id,
        doc_type=parsed.doc_type,
        folio_from=parsed.folio_from,
        folio_to=parsed.folio_to,
        xml_encrypted=crypto.encrypt(raw),
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    folio_service.ensure_pointer(db, customer.id, parsed.doc_type)
    return row
