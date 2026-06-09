"""Cifrado en reposo de secretos (certificados .pfx, passwords, CAF).

Usa ``MultiFernet``: la primera llave cifra, todas descifran (permite rotación
de llaves sin re-cifrar todo de golpe). Las llaves vienen de ``DTE_FERNET_KEYS``.
"""

from __future__ import annotations

from functools import lru_cache

from cryptography.fernet import Fernet, MultiFernet

from .config import get_settings


@lru_cache
def _fernet() -> MultiFernet:
    keys = get_settings().fernet_key_list
    if not keys:
        raise RuntimeError(
            "DTE_FERNET_KEYS no configurado. Genera una con "
            '`python -c "from cryptography.fernet import Fernet; '
            'print(Fernet.generate_key().decode())"`.'
        )
    return MultiFernet([Fernet(k) for k in keys])


def encrypt(data: bytes | str) -> str:
    """Cifra y devuelve un token (str) apto para guardar en BD."""
    if isinstance(data, str):
        data = data.encode("utf-8")
    return _fernet().encrypt(data).decode("ascii")


def decrypt(token: str) -> bytes:
    """Descifra un token guardado en BD."""
    return _fernet().decrypt(token.encode("ascii"))


def decrypt_str(token: str) -> str:
    return decrypt(token).decode("utf-8")
