"""Engine, fábrica de sesiones y dependencia ``get_db``."""

from __future__ import annotations

from collections.abc import Iterator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import get_settings

_settings = get_settings()
# El pool dimensionable solo aplica a engines con QueuePool (Postgres); sqlite
# (tests) usa SingletonThreadPool y rechaza estos kwargs.
_engine_kwargs: dict = {"pool_pre_ping": True, "future": True}
if not _settings.database_url.startswith("sqlite"):
    _engine_kwargs["pool_size"] = _settings.db_pool_size
    _engine_kwargs["max_overflow"] = _settings.db_max_overflow

_engine = create_engine(_settings.database_url, **_engine_kwargs)
SessionLocal = sessionmaker(bind=_engine, autoflush=False, expire_on_commit=False)


def get_db() -> Iterator[Session]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
