# Esquemas XSD del SII

Los XSD son **archivos oficiales del SII** y NO se versionan (ver `.gitignore`).
Sirven para que la API valide los documentos **antes** de enviarlos
(`validate_xsd=true`); sin ellos, esa validación responde `503 XSDNotAvailable`
y igual puedes emitir con `validate_xsd=false`.

## De dónde sacarlos

Descárgalos del SII (sii.cl → documentación de Factura Electrónica, "Formato XML
de los Documentos Tributarios Electrónicos" / esquemas de envío y libros). Vienen
en varios ZIP; **cada familia comparte nombres de archivo con contenido distinto**,
por eso cada una vive en su propia subcarpeta.

## Estructura esperada

El `Validator` mapea el elemento raíz → archivo (ver `dte_chile/validation.py`):

| Documento            | Archivo requerido                       |
| -------------------- | --------------------------------------- |
| `DTE`                | `schemas/dte/DTE_v10.xsd`               |
| `EnvioDTE`           | `schemas/dte/EnvioDTE_v10.xsd`          |
| `RespuestaDTE`       | `schemas/response/RespuestaEnvioDTE_v10.xsd` |
| `EnvioRecibos`       | `schemas/receipts/EnvioRecibos_v10.xsd` |
| `LibroCompraVenta`   | `schemas/iecv/LibroCV_v10.xsd`          |

**Importante:** cada subcarpeta debe contener además los XSD que el principal
`incluye`/`importa` (los `xsd:include` / `xsd:import` del archivo), copiados desde
el **mismo ZIP** de esa familia. Típicamente:

- `SiiTypes_v10.xsd`
- `xmldsignature_v10.xsd`
- y, según la familia, `Recibos_v10.xsd` (recibos), etc.

Quedando, por ejemplo:

```
schemas/
├── dte/        DTE_v10.xsd  EnvioDTE_v10.xsd  SiiTypes_v10.xsd  xmldsignature_v10.xsd
├── response/   RespuestaEnvioDTE_v10.xsd  SiiTypes_v10.xsd  xmldsignature_v10.xsd
├── receipts/   EnvioRecibos_v10.xsd  Recibos_v10.xsd  SiiTypes_v10.xsd  xmldsignature_v10.xsd
└── iecv/       LibroCV_v10.xsd  SiiTypes_v10.xsd  xmldsignature_v10.xsd
```

## Nota sobre LibroCV

Algunos XSD del SII (p. ej. el tipo `LceCal` en `LibroCV_v10.xsd`) declaran
decimales fuera del rango que acepta libxml2 y fallan al compilar
(`XSDNotAvailable` con detalle). Requieren un pequeño parche en el XSD; si no
necesitas validar el libro localmente, omítelo y usa `validate_xsd=false`.

## Docker

`docker-compose.yml` monta esta carpeta en el contenedor del API
(`./schemas:/srv/schemas:ro`, `DTE_SCHEMAS_DIR=/srv/schemas`). Basta con dejar
los XSD aquí antes de `docker compose up`.
