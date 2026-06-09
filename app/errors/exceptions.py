"""Excepciones propias del servicio (no del motor)."""

from __future__ import annotations


class CertificateUnavailable(Exception):
    """El cliente no tiene un certificado vigente cargado."""

    def __init__(self, customer_id: int):
        self.customer_id = customer_id
        super().__init__(f"El cliente {customer_id} no tiene un certificado vigente.")
