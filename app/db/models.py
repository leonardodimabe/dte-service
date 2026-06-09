"""Modelos ORM (multi-tenant + certificados + folios en BD + auditoría).

Espejo del servicio .NET, con dos mejoras: secretos cifrados en reposo y el
ambiente SII por cliente. Los folios viven en BD (asignador HA).
"""

from __future__ import annotations

import datetime as dt
import enum

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class SiiEnvironment(enum.StrEnum):
    CERTIFICATION = "CERTIFICATION"  # Maullín
    PRODUCTION = "PRODUCTION"  # Palena


class Customer(Base):
    __tablename__ = "customer"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(200))
    key: Mapped[str] = mapped_column(String(100), unique=True, index=True)  # customerCode
    rut: Mapped[str] = mapped_column(String(20), index=True)
    environment: Mapped[SiiEnvironment] = mapped_column(
        Enum(SiiEnvironment), default=SiiEnvironment.CERTIFICATION
    )
    # Carátula de producción (en certificación va 0); por cliente.
    resolution_number: Mapped[int] = mapped_column(Integer, default=0)
    resolution_date: Mapped[dt.date] = mapped_column(Date, default=dt.date(2014, 8, 22))

    certificates: Mapped[list[CustomerCertificate]] = relationship(
        back_populates="customer", cascade="all, delete-orphan"
    )
    services: Mapped[list[CustomerService]] = relationship(
        back_populates="customer", cascade="all, delete-orphan"
    )


class CustomerCertificate(Base):
    __tablename__ = "customer_certificate"

    id: Mapped[int] = mapped_column(primary_key=True)
    customer_id: Mapped[int] = mapped_column(ForeignKey("customer.id", ondelete="CASCADE"))
    file_base64: Mapped[str] = mapped_column(String)  # .pfx en base64, Fernet-cifrado
    password: Mapped[str] = mapped_column(String)  # Fernet-cifrado
    due_date: Mapped[dt.date] = mapped_column(Date)
    created_at: Mapped[dt.datetime] = mapped_column(DateTime, server_default=func.now())

    customer: Mapped[Customer] = relationship(back_populates="certificates")


class Service(Base):
    __tablename__ = "service"

    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String(36), unique=True, index=True)  # UUID == SERVICE_CODE
    name: Mapped[str] = mapped_column(String(100))


class CustomerService(Base):
    __tablename__ = "customer_service"
    __table_args__ = (UniqueConstraint("customer_id", "service_id"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    customer_id: Mapped[int] = mapped_column(ForeignKey("customer.id", ondelete="CASCADE"))
    service_id: Mapped[int] = mapped_column(ForeignKey("service.id", ondelete="CASCADE"))
    apikey_hash: Mapped[str] = mapped_column(String)  # argon2

    customer: Mapped[Customer] = relationship(back_populates="services")
    service: Mapped[Service] = relationship()


class Caf(Base):
    __tablename__ = "caf"

    id: Mapped[int] = mapped_column(primary_key=True)
    customer_id: Mapped[int] = mapped_column(ForeignKey("customer.id", ondelete="CASCADE"))
    doc_type: Mapped[int] = mapped_column(Integer, index=True)
    folio_from: Mapped[int] = mapped_column(Integer)
    folio_to: Mapped[int] = mapped_column(Integer)
    xml_encrypted: Mapped[str] = mapped_column(String)  # CAF completo (con RSASK), Fernet-cifrado
    exhausted: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[dt.datetime] = mapped_column(DateTime, server_default=func.now())


class FolioPointer(Base):
    """Último folio asignado por (cliente, tipo). Fila bloqueada con FOR UPDATE."""

    __tablename__ = "folio_pointer"

    customer_id: Mapped[int] = mapped_column(
        ForeignKey("customer.id", ondelete="CASCADE"), primary_key=True
    )
    doc_type: Mapped[int] = mapped_column(Integer, primary_key=True)
    last_folio: Mapped[int] = mapped_column(Integer, default=0)


class CustomerRequest(Base):
    __tablename__ = "customer_request"

    id: Mapped[int] = mapped_column(primary_key=True)
    customer_id: Mapped[int] = mapped_column(ForeignKey("customer.id", ondelete="CASCADE"))
    service_code: Mapped[str] = mapped_column(String(36))
    request_id: Mapped[str] = mapped_column(String(64), default="-")
    status: Mapped[str] = mapped_column(String(20), default="ok")
    created_at: Mapped[dt.datetime] = mapped_column(DateTime, server_default=func.now())
