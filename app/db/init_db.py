"""Crea las tablas (atajo para dev/compose). En producción usar Alembic."""

from __future__ import annotations

import app.db.models  # noqa: F401  (registra los modelos en el metadata)
from app.db.base import Base
from app.db.session import _engine


def init_db() -> None:
    Base.metadata.create_all(_engine)


if __name__ == "__main__":
    init_db()
    print("Tablas creadas.")
