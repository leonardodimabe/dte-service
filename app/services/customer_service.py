"""Administración de clientes, servicios habilitados y CAF (operaciones de BD)."""

from __future__ import annotations

import base64
import binascii
import secrets

from dte_chile.caf import load_caf_bytes
from dte_chile.rut import format_rut
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core import crypto
from app.db.models import (
    Caf,
    Customer,
    CustomerCertificate,
    CustomerService,
    FolioPointer,
    Service,
    SiiEnvironment,
)
from app.errors.exceptions import DomainError
from app.security.apikeys import generate_apikey, hash_apikey
from app.security.service_codes import ALL_SERVICES
from app.services import folio_service


def generate_customer_key(db: Session) -> str:
    """customerCode opaco: token aleatorio URL-safe único (no revela el nombre)."""
    for _ in range(10):
        candidate = secrets.token_urlsafe(8)  # ~11 caracteres
        if db.query(Customer).filter(Customer.key == candidate).first() is None:
            return candidate
    return secrets.token_urlsafe(16)  # improbable: 10 colisiones seguidas


def list_customers(db: Session, *, limit: int = 100, offset: int = 0) -> list[Customer]:
    return list(
        db.execute(select(Customer).order_by(Customer.id).limit(limit).offset(offset)).scalars()
    )


def get_customer(db: Session, customer_id: int) -> Customer | None:
    return db.get(Customer, customer_id)


def list_services_for(db: Session, customer: Customer) -> list[Service]:
    return list(
        db.execute(
            select(Service)
            .join(CustomerService, CustomerService.service_id == Service.id)
            .where(CustomerService.customer_id == customer.id)
            .order_by(Service.name)
        ).scalars()
    )


def list_certificates(db: Session, customer: Customer) -> list[CustomerCertificate]:
    return list(
        db.execute(
            select(CustomerCertificate)
            .where(CustomerCertificate.customer_id == customer.id)
            .order_by(CustomerCertificate.created_at.desc())
        ).scalars()
    )


def list_cafs(db: Session, customer: Customer) -> list[Caf]:
    return list(
        db.execute(
            select(Caf).where(Caf.customer_id == customer.id).order_by(Caf.doc_type, Caf.folio_from)
        ).scalars()
    )


def folio_pointers(db: Session, customer_id: int) -> dict[int, int]:
    rows = db.execute(select(FolioPointer).where(FolioPointer.customer_id == customer_id)).scalars()
    return {r.doc_type: r.last_folio for r in rows}


def create_customer(db: Session, data, *, commit: bool = True) -> Customer:
    key = data.key or generate_customer_key(db)
    customer = Customer(
        name=data.name,
        key=key,
        rut=data.rut,
        environment=SiiEnvironment(data.environment),
        resolution_number=data.resolution_number,
        resolution_date=data.resolution_date,
    )
    db.add(customer)
    db.flush()
    db.refresh(customer)
    if commit:
        db.commit()
    return customer


def update_customer(db: Session, customer: Customer, data, *, commit: bool = True) -> Customer:
    """Edición parcial: solo aplica los campos enviados (no nulos)."""
    if data.name is not None:
        customer.name = data.name
    if data.rut is not None:
        customer.rut = data.rut
    if data.environment is not None:
        customer.environment = SiiEnvironment(data.environment)
    if data.resolution_number is not None:
        customer.resolution_number = data.resolution_number
    if data.resolution_date is not None:
        customer.resolution_date = data.resolution_date
    db.flush()
    db.refresh(customer)
    if commit:
        db.commit()
    return customer


def grant_service(
    db: Session,
    customer: Customer,
    service_code: str,
    apikey: str | None = None,
    *,
    commit: bool = True,
) -> str:
    """Habilita el servicio o, si ya estaba, **rota** su apiKey (idempotente).

    Si ``apikey`` es ``None``, se genera una aleatoria. Devuelve la apiKey en
    claro (el llamador la muestra UNA vez; en BD solo va el hash).
    """
    if service_code not in ALL_SERVICES:
        raise DomainError(f"service_code desconocido: {service_code}")
    raw_key = apikey or generate_apikey()
    service = db.query(Service).filter(Service.code == service_code).first()
    if service is None:
        service = Service(code=service_code, name=ALL_SERVICES[service_code])
        db.add(service)
        db.flush()
    existing = (
        db.query(CustomerService).filter_by(customer_id=customer.id, service_id=service.id).first()
    )
    if existing is not None:
        existing.apikey_hash = hash_apikey(raw_key)  # rotación
    else:
        db.add(
            CustomerService(
                customer_id=customer.id, service_id=service.id, apikey_hash=hash_apikey(raw_key)
            )
        )
    if commit:
        db.commit()
    return raw_key


def revoke_service(
    db: Session, customer: Customer, service_code: str, *, commit: bool = True
) -> bool:
    service = db.query(Service).filter(Service.code == service_code).first()
    if service is None:
        return False
    cs = db.query(CustomerService).filter_by(customer_id=customer.id, service_id=service.id).first()
    if cs is None:
        return False
    db.delete(cs)
    if commit:
        db.commit()
    return True


def _same_rut(a: str | None, b: str | None) -> bool:
    if not a or not b:
        return True  # sin RUT en el CAF: no se puede comparar, no se bloquea
    try:
        return format_rut(a) == format_rut(b)
    except ValueError:
        return a.strip() == b.strip()


def add_caf(db: Session, customer: Customer, xml_base64: str, *, commit: bool = True) -> Caf:
    try:
        raw = base64.b64decode(xml_base64, validate=True)
    except (binascii.Error, ValueError) as ex:
        raise DomainError("xml_base64 no es base64 válido") from ex
    parsed = load_caf_bytes(raw)  # valida + extrae rango/tipo

    # El CAF pertenece al cliente: su RUT emisor (<RE>) debe ser el del cliente.
    if not _same_rut(parsed.issuer_rut, customer.rut):
        raise DomainError(
            f"El RUT del CAF ({parsed.issuer_rut}) no coincide con el del cliente ({customer.rut})."
        )

    # Rechazar rangos solapados con un CAF ya cargado del mismo tipo.
    overlap = (
        db.query(Caf)
        .filter(
            Caf.customer_id == customer.id,
            Caf.doc_type == parsed.doc_type,
            Caf.folio_from <= parsed.folio_to,
            Caf.folio_to >= parsed.folio_from,
        )
        .first()
    )
    if overlap is not None:
        raise DomainError(
            f"El rango {parsed.folio_from}-{parsed.folio_to} (tipo {parsed.doc_type}) se solapa "
            f"con un CAF ya cargado ({overlap.folio_from}-{overlap.folio_to})."
        )

    row = Caf(
        customer_id=customer.id,
        doc_type=parsed.doc_type,
        folio_from=parsed.folio_from,
        folio_to=parsed.folio_to,
        xml_encrypted=crypto.encrypt(raw),
    )
    db.add(row)
    db.flush()
    db.refresh(row)
    # CAF y puntero en la misma transacción (atómicos con la auditoría del router).
    folio_service.ensure_pointer(db, customer.id, parsed.doc_type, commit=False)
    if commit:
        db.commit()
    return row
