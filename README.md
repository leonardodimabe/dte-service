# dte-service — API multi-cliente sobre el motor `dte_chile`

Servicio **FastAPI multi-tenant** que expone el motor de facturación electrónica
`dte_chile` (SII Chile) por HTTP: RCV (conciliación con Odoo), emisión de DTE,
libro IECV y acuses de intercambio. Cada cliente tiene su **certificado**, su
**API key** y sus **servicios** habilitados.

## Arquitectura

- **Multi-tenant:** el request trae headers `apiKey` + `customerCode`; cada endpoint
  exige un `service_code`. Se resuelve el cliente y se inyecta su `Certificate`.
- **Certificados/CAF cifrados** en BD (Fernet, `DTE_FERNET_KEYS`).
- **Folios en BD** (`SELECT ... FOR UPDATE`) → asignación segura entre workers/hosts.
- **Ambiente SII por cliente** (Maullín/Palena).
- El motor es síncrono → cada llamada corre en threadpool (`run_blocking`).

## Capas

```
routers/  → HTTP (deps, threadpool)      schemas/  → Pydantic (espejo dataclasses)
services/ → envuelven dte_chile          db/       → modelos + sesión
security/ → auth tenant + apikeys        deps/     → tenant + certificate
core/     → config, crypto, logging      errors/   → DteError → HTTP
```

## Desarrollo (Linux)

```bash
sudo apt-get install -y libxml2-dev libxmlsec1-dev pkg-config   # deps del motor
python -m venv .venv && . .venv/bin/activate
pip install -e ../dte_chile          # el motor (path local) o índice/git privado
pip install -e ".[dev]"
export DTE_FERNET_KEYS=$(python -c "from cryptography.fernet import Fernet;print(Fernet.generate_key().decode())")
ruff check . && ruff format --check . && mypy && pytest -q
```

## Levantar

```bash
bash scripts/vendor_engine.sh                  # vendoriza el motor → vendor/dte_chile
# (en Windows: .\scripts\vendor_engine.ps1)
cp -r ../dte_chile/schemas ./schemas           # XSD del SII (opcional, para validar)
export DTE_FERNET_KEYS=...                      # genera una llave Fernet
docker compose up --build
# OpenAPI en http://localhost:8000/docs
```

## El motor `dte_chile`

Vive en el repo **privado** `github.com/leonardodimabe/cl_dte_lib`, **pineado al
tag `v0.1.0`**. Según el contexto:

- **Dev:** `pip install -e ../dte_chile` (clon local, editable).
- **CI / reproducible:** extra `engine` del `pyproject` → instala
  `dte_chile @ git+…/cl_dte_lib.git@v0.1.0` (requiere acceso al repo privado).
- **Docker:** vendorizado offline (`scripts/vendor_engine.*`), sin token en el build.

Subir de versión = nuevo tag en el motor + bump del `@vX.Y.Z` en el extra `engine`.

## CI

`.github/workflows/ci.yml` corre el gate (ruff + format + mypy + pytest) en Linux.
Instala el motor desde el tag con `pip install -e ".[dev,engine]"`, autenticando
git con el secreto **`ENGINE_TOKEN`** (PAT fine-grained / deploy key con lectura a
`cl_dte_lib`; el `github.token` por defecto no alcanza otro repo privado).

## Endpoints (v1)

| Servicio | Endpoint | Auth |
|---|---|---|
| RCV (per-cliente) | `POST /rcv/documents` | `apiKey` + `customerCode` (servicio RCV) |
| RCV (operador) | `POST /admin/customers/{id}/rcv` | `X-Admin-Key` |
| DTE | `POST /dte/issue`, `GET /dte/status/{track_id}` | `apiKey` + `customerCode` (DTE) |
| IECV | `POST /books` | `apiKey` + `customerCode` (BOOK) |
| Intercambio | `POST /exchange/{ack,result,receipts}` | `apiKey` + `customerCode` (EXCHANGE) |
| Admin | `POST /admin/customers[...]` | `X-Admin-Key` |

Flujo de alta (admin): crear cliente → subir certificado → subir CAF (crea el
puntero de folios) → habilitar servicios (devuelve la apikey una vez).

### Consultar el RCV (compras/ventas) de un cliente

El `issuer_rut` **no se pide**: se toma del cliente resuelto. Body = `{period, operation}`
(`operation` = `COMPRA` o `VENTA` → dos llamadas para ambos libros).

**Per-cliente** (cada empresa con su apiKey):

```bash
curl -X POST http://localhost:8000/rcv/documents \
  -H "customerCode: <key>" -H "apiKey: <apikey_rcv>" \
  -H "Content-Type: application/json" \
  -d '{"period":"202505","operation":"COMPRA"}'
```

**Operador / Odoo** (una sola credencial para cualquier cliente, usa su cert guardado):

```bash
curl -X POST http://localhost:8000/admin/customers/<id>/rcv \
  -H "X-Admin-Key: <DTE_ADMIN_API_KEY>" -H "Content-Type: application/json" \
  -d '{"period":"202505","operation":"VENTA"}'
```

## Migraciones (Alembic)

La migración inicial ya está en `migrations/versions/`. Aplicar el esquema:

```bash
alembic upgrade head
```

Para futuros cambios de esquema (tras editar los modelos ORM):

```bash
alembic revision --autogenerate -m "descripcion" && alembic upgrade head
```

Alembic toma la URL de `DTE_DATABASE_URL` (ver `migrations/env.py`). El atajo
`python -m app.db.init_db` queda solo para pruebas rápidas sin Alembic.
