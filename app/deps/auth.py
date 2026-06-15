"""Dependencias de tenant, una por servicio (instancias únicas → FastAPI las
deduplica dentro de un request, evitando doble auditoría)."""

from app.security.service_codes import (
    SERVICE_BHE,
    SERVICE_BOOK,
    SERVICE_DTE,
    SERVICE_EXCHANGE,
    SERVICE_RCV,
)
from app.security.tenant import tenant_for

require_rcv = tenant_for(SERVICE_RCV)
require_dte = tenant_for(SERVICE_DTE)
require_book = tenant_for(SERVICE_BOOK)
require_exchange = tenant_for(SERVICE_EXCHANGE)
require_bhe = tenant_for(SERVICE_BHE)
