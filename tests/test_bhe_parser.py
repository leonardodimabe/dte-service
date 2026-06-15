"""Tests del parser BHE del motor (formato ``arr_informe_mensual`` del SII).

El parser es la pieza frágil (depende del HTML del SII); se ejercita contra un
fixture fiel al formato real del informe mensual de boletas recibidas.
"""

import datetime as dt

import pytest
from dte_chile.bhe import (
    BheClient,
    _extract_total,
    _normalize_row,
    _parse_date,
    _parse_report,
    _to_int,
)
from dte_chile.errors import BheError, SiiAuthError

# Fixture: informe mensual con 2 boletas (una vigente, una anulada). Reproduce el
# array JS que emite el CGI TMBCOC_InformeMensualBheRec.cgi del SII.
_HTML = """
<html><script>
xml_values['total_boletas'] = "2";
arr_informe_mensual['rutemisor_0'] = "12345678";
arr_informe_mensual['dvemisor_0'] = "5";
arr_informe_mensual['nombre_emisor_0'] = "JUAN PEREZ CONSULTOR";
arr_informe_mensual['nroboleta_0'] = "1001";
arr_informe_mensual['fecha_boleta_0'] = "01/05/2026";
arr_informe_mensual['totalhonorarios_0'] = formatMiles("1.000.000");
arr_informe_mensual['retencion_receptor_0'] = formatMiles("152.500");
arr_informe_mensual['honorariosliquidos_0'] = formatMiles("847.500");
arr_informe_mensual['rutemisor_1'] = "11111111";
arr_informe_mensual['dvemisor_1'] = "1";
arr_informe_mensual['nombre_emisor_1'] = "MARIA GONZALEZ ASESORIAS";
arr_informe_mensual['nroboleta_1'] = "2002";
arr_informe_mensual['fecha_boleta_1'] = "15/05/2026";
arr_informe_mensual['totalhonorarios_1'] = formatMiles("500.000");
arr_informe_mensual['retencion_receptor_1'] = formatMiles("76.250");
arr_informe_mensual['honorariosliquidos_1'] = formatMiles("423.750");
arr_informe_mensual['fechaanulacion_1'] = "20/05/2026";
</script></html>
"""

# Mes sin boletas: el informe se rendea pero con total 0 (no es sesión inválida).
_EMPTY_HTML = """<html><body>INFORME MENSUAL
<script>xml_values['total_boletas'] = "0";</script></body></html>"""

# Sesión expirada/rechazada: el SII devuelve la pantalla de login.
_LOGIN_HTML = "<html><body>CAutInicio - reingrese su clave</body></html>"

# HTML irreconocible (markup cambiado): ni informe, ni login.
_GARBAGE_HTML = "<html><body>mantencion programada</body></html>"


def test_extract_total():
    assert _extract_total(_HTML) == 2
    assert _extract_total("<html></html>") is None


def test_parse_report_rows():
    rows = _parse_report(_HTML)
    assert len(rows) == 2
    assert rows[0]["nroboleta"] == "1001"
    assert rows[0]["totalhonorarios"] == "1.000.000"
    assert rows[1]["fechaanulacion"] == "20/05/2026"


def test_normalize_row_vigente():
    row = _parse_report(_HTML)[0]
    doc = _normalize_row(row, "2026-05")
    assert doc.issuer_rut == "12345678-5"
    assert doc.issuer_name == "JUAN PEREZ CONSULTOR"
    assert doc.folio == 1001  # int
    assert doc.issue_date == dt.date(2026, 5, 1)
    assert doc.gross_amount == 1_000_000  # int, separador de miles eliminado
    assert doc.retention_amount == 152_500
    assert doc.net_amount == 847_500
    assert doc.status == "vigente"
    assert doc.period == "2026-05"


def test_normalize_row_anulada():
    row = _parse_report(_HTML)[1]
    doc = _normalize_row(row, "2026-05")
    assert doc.status == "anulada"  # tiene fechaanulacion
    assert doc.cancel_date == dt.date(2026, 5, 20)


def test_parse_date():
    assert _parse_date("01/05/2026") == dt.date(2026, 5, 1)
    assert _parse_date("") is None
    assert _parse_date("malo") is None
    assert _parse_date("32/13/2026") is None


def test_to_int():
    assert _to_int("1.000.000") == 1_000_000
    assert _to_int("847.500") == 847_500
    assert _to_int("") == 0
    assert _to_int(None) == 0
    assert _to_int(1500) == 1500


def _client_no_auth(monkeypatch, html):
    cli = BheClient("76158145-7", "clave")
    cli._authenticated = True  # evita el login de red
    monkeypatch.setattr(cli, "_request_page", lambda year, month, page: html)
    return cli


def test_fetch_received_single_page(monkeypatch):
    cli = _client_no_auth(monkeypatch, _HTML)
    docs = cli.fetch_received(2026, 5)
    assert len(docs) == 2
    assert {d.status for d in docs} == {"vigente", "anulada"}


def test_fetch_received_empty_month(monkeypatch):
    cli = _client_no_auth(monkeypatch, _EMPTY_HTML)
    assert cli.fetch_received(2026, 5) == []


def test_fetch_received_invalid_session_raises(monkeypatch):
    cli = _client_no_auth(monkeypatch, _LOGIN_HTML)
    with pytest.raises(SiiAuthError):
        cli.fetch_received(2026, 5)


def test_fetch_received_garbage_raises(monkeypatch):
    cli = _client_no_auth(monkeypatch, _GARBAGE_HTML)
    with pytest.raises(BheError):
        cli.fetch_received(2026, 5)
