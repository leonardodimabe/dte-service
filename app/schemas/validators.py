"""Validadores reutilizables para los schemas de entrada.

El email se valida por regex (formato básico) en vez de ``EmailStr`` para no
arrastrar la dependencia ``email-validator`` ni hacer resolución DNS: aquí solo
interesa rechazar entradas evidentemente mal formadas.
"""

from __future__ import annotations

import re

from dte_chile.rut import format_rut

# Política de password de usuarios del portal (creados por superadmin).
MIN_PASSWORD_LENGTH = 12

_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def normalize_email(value: str) -> str:
    v = value.strip().lower()
    if not _EMAIL_RE.match(v):
        raise ValueError("email con formato inválido")
    return v


def normalize_rut(value: str) -> str:
    """Normaliza al formato SII ``99999999-D`` validando el dígito verificador."""
    try:
        return format_rut(value)
    except ValueError as ex:
        raise ValueError("RUT inválido (revisa el dígito verificador)") from ex
