"""Purga de access-logs antiguos (retención de ``request_log``).

Uso (cron diario, p. ej.):
    python -m scripts.purge_audit --days 180
"""

from __future__ import annotations

import argparse

import app.db.session as db_session
from app.services import audit_service


def main() -> None:
    parser = argparse.ArgumentParser(description="Purga request_log anterior a N días.")
    parser.add_argument("--days", type=int, default=180, help="retención en días (default: 180)")
    args = parser.parse_args()

    with db_session.SessionLocal() as db:
        deleted = audit_service.purge_requests(db, older_than_days=args.days)
    print(f"request_log: {deleted} filas borradas (anteriores a {args.days} días).")


if __name__ == "__main__":
    main()
