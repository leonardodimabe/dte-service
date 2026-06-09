"""Modelos ORM (multi-tenant + certificados + folios en BD + auditoría).

Espejo del servicio .NET, con dos mejoras: secretos cifrados en reposo y el
ambiente SII por cliente. Los folios viven en BD (asignador HA).
"""

from __future__ import annotations

import datetime as dt
import enum

from sqlalchemy import (
    JSON,
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


class User(Base):
    """Usuario del portal: interno (customer_id NULL) o de cliente (customer_id set)."""

    __tablename__ = "app_user"  # 'user' es palabra reservada en Postgres

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(200), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String)
    role: Mapped[str] = mapped_column(String(20))  # ver security.roles.Role
    customer_id: Mapped[int | None] = mapped_column(
        ForeignKey("customer.id", ondelete="CASCADE"), nullable=True
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[dt.datetime] = mapped_column(DateTime, server_default=func.now())
    last_login: Mapped[dt.datetime | None] = mapped_column(DateTime, nullable=True)


class RequestLog(Base):
    """Access-log de TODA petición (lo escribe el middleware). Sin secretos."""

    __tablename__ = "request_log"

    id: Mapped[int] = mapped_column(primary_key=True)
    principal_type: Mapped[str] = mapped_column(String(20))  # user|customer|system|anon
    principal_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    principal_role: Mapped[str | None] = mapped_column(String(20), nullable=True)
    service_code: Mapped[str | None] = mapped_column(String(36), nullable=True)
    method: Mapped[str] = mapped_column(String(10))
    path: Mapped[str] = mapped_column(String(300))
    request_id: Mapped[str] = mapped_column(String(64), default="-")
    ip: Mapped[str | None] = mapped_column(String(64), nullable=True)
    user_agent: Mapped[str | None] = mapped_column(String(300), nullable=True)
    status_code: Mapped[int] = mapped_column(Integer)
    outcome: Mapped[str] = mapped_column(String(10))  # ok|denied|error
    latency_ms: Mapped[int] = mapped_column(Integer)
    meta: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[dt.datetime] = mapped_column(DateTime, server_default=func.now(), index=True)


class AdminAudit(Base):
    """Auditoría de cambios de datos maestros (quién modificó qué)."""

    __tablename__ = "admin_audit"

    id: Mapped[int] = mapped_column(primary_key=True)
    actor_user_id: Mapped[int | None] = mapped_column(
        ForeignKey("app_user.id", ondelete="SET NULL"), nullable=True
    )
    action: Mapped[str] = mapped_column(String(50))
    target_type: Mapped[str] = mapped_column(String(50))
    target_id: Mapped[str | None] = mapped_column(String(50), nullable=True)
    summary: Mapped[str] = mapped_column(String(500))
    created_at: Mapped[dt.datetime] = mapped_column(DateTime, server_default=func.now(), index=True)
