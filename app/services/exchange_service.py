"""Servicio de acuses de intercambio (responder un EnvioDTE recibido)."""

from __future__ import annotations

import base64
import datetime as dt
from zoneinfo import ZoneInfo

from dte_chile.certificate import Certificate
from dte_chile.exchange import (
    build_receipt_acknowledgment,
    build_receipts_envelope,
    build_result_response,
    parse_envelope,
    serialize,
)

_CL_TZ = ZoneInfo("America/Santiago")  # acuses fechados en hora chilena


def _ts() -> dt.datetime:
    return dt.datetime.now(_CL_TZ).replace(microsecond=0, tzinfo=None)


def _b64(xml: bytes) -> str:
    return base64.b64encode(xml).decode("ascii")


def acknowledgment(cert: Certificate, envelope_base64: str) -> str:
    env = parse_envelope(base64.b64decode(envelope_base64))
    return _b64(serialize(build_receipt_acknowledgment(env, cert, _ts())))


def result(cert: Certificate, envelope_base64: str, accept: bool, rejection_label: str) -> str:
    env = parse_envelope(base64.b64decode(envelope_base64))
    return _b64(
        serialize(
            build_result_response(env, cert, _ts(), accept=accept, rejection_label=rejection_label)
        )
    )


def receipts(cert: Certificate, envelope_base64: str, location: str) -> str:
    env = parse_envelope(base64.b64decode(envelope_base64))
    return _b64(serialize(build_receipts_envelope(env, cert, _ts(), location=location)))
