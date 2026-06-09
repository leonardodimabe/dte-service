"""Puente al threadpool.

El motor ``dte_chile`` es síncrono y bloqueante (red al SII, firma con xmlsec).
Todas las llamadas al motor desde un endpoint async deben pasar por aquí para no
bloquear el event loop de uvicorn.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import TypeVar

from fastapi.concurrency import run_in_threadpool

T = TypeVar("T")


async def run_blocking(fn: Callable[..., T], *args, **kwargs) -> T:
    """Ejecuta ``fn(*args, **kwargs)`` (bloqueante) en el threadpool."""
    return await run_in_threadpool(lambda: fn(*args, **kwargs))
