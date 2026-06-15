"""Excepciones propias del servicio (no del motor)."""

from __future__ import annotations


class DomainError(Exception):
    """Regla de negocio violada por la entrada del cliente (se mapea a 400)."""


class CertificateUnavailable(Exception):
    """El cliente no tiene un certificado vigente cargado."""

    def __init__(self, customer_id: int):
        self.customer_id = customer_id
        super().__init__(f"El cliente {customer_id} no tiene un certificado vigente.")


class SiiCredentialUnavailable(Exception):
    """El cliente no tiene una clave tributaria del SII configurada (BHE)."""

    def __init__(self, customer_id: int):
        self.customer_id = customer_id
        super().__init__(
            f"El cliente {customer_id} no tiene una clave tributaria del SII configurada."
        )
