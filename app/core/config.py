"""Configuración del servicio (variables de entorno con prefijo ``DTE_``)."""

from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="DTE_", env_file=".env", extra="ignore")

    database_url: str = "postgresql+psycopg://dte:dte@localhost:5432/dte_service"
    # Llaves Fernet coma-separadas (la primera cifra; todas descifran → rotación).
    fernet_keys: str = ""
    schemas_dir: str = "schemas"
    admin_api_key: str = "change-me"
    request_timeout_s: int = 60
    log_level: str = "INFO"

    @property
    def fernet_key_list(self) -> list[str]:
        return [k.strip() for k in self.fernet_keys.split(",") if k.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
