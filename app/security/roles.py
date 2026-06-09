"""Roles del portal (RBAC fijo en código; migrable a BD si crece)."""

from __future__ import annotations

from enum import StrEnum


class Role(StrEnum):
    SUPERADMIN = "superadmin"  # todo, incl. gestionar usuarios admin
    OPERATOR = "operator"  # datos maestros (clientes/servicios/certs/CAF) + RCV operador
    AUDITOR = "auditor"  # solo lectura (auditoría + clientes)
    CLIENT = "client"  # scoped a su customer_id (ve sus servicios/consumo)


# Roles internos (ven el portal de administración).
ADMIN_ROLES = (Role.SUPERADMIN, Role.OPERATOR, Role.AUDITOR)
# Roles que pueden gestionar datos maestros (escritura).
WRITE_ROLES = (Role.SUPERADMIN, Role.OPERATOR)
