"""Rate limiting en memoria por ventana deslizante (anti fuerza bruta).

Estado por proceso: con N workers el límite efectivo es ~N x límite, suficiente
como freno de fuerza bruta. Para límites exactos multi-instancia, aplicarlos
además en el reverse proxy (o mover el estado a Redis).

Nota: la llave es la IP del peer directo (``request.client.host``). Detrás de
un proxy, arrancar uvicorn con ``--proxy-headers`` para que sea la IP real.
"""

from __future__ import annotations

import threading
import time
from collections import deque

# Cota de llaves retenidas (IPs); al superarla se purgan las colas vacías.
_MAX_KEYS = 10_000


class SlidingWindowLimiter:
    def __init__(self, max_events: int, window_s: float) -> None:
        self.max_events = max_events
        self.window_s = window_s
        self._events: dict[str, deque[float]] = {}
        self._lock = threading.Lock()

    def _prune(self, key: str, now: float) -> deque[float]:
        q = self._events.setdefault(key, deque())
        cutoff = now - self.window_s
        while q and q[0] < cutoff:
            q.popleft()
        return q

    def hit(self, key: str) -> bool:
        """Registra un intento y devuelve True si el límite ya estaba excedido."""
        now = time.monotonic()
        with self._lock:
            q = self._prune(key, now)
            if len(q) >= self.max_events:
                return True
            q.append(now)
            return False

    def is_limited(self, key: str) -> bool:
        """Consulta sin registrar (para bloquear antes de hacer trabajo)."""
        with self._lock:
            return len(self._prune(key, time.monotonic())) >= self.max_events

    def record(self, key: str) -> None:
        """Registra un evento (p. ej. un fallo de autenticación)."""
        now = time.monotonic()
        with self._lock:
            self._prune(key, now).append(now)
            if len(self._events) > _MAX_KEYS:
                self._events = {k: q for k, q in self._events.items() if q}

    def reset(self) -> None:
        with self._lock:
            self._events.clear()
