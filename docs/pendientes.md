# Pendientes

Lo que queda por hacer fuera de la certificación ante el SII, que tiene su
propio archivo en [`certificacion-sii.md`](certificacion-sii.md).

**Actualizar al avanzar.** Última revisión: **2026-09-07**.

---

## 1. Endurecer el servicio para exponerlo a internet

El servicio es multiempresa y va a quedar público, así que estos huecos dejan
de ser teóricos. Salen de una auditoría del código, no de una lista genérica:
cada uno se verificó leyendo la implementación.

### Lo que ya está bien resuelto — no gastar ahí

Las `apiKey` van hasheadas con argon2 y se verifican en tiempo constante, con
verificación señuelo para que un `customerCode` inexistente no responda antes
(`app/security/tenant.py`). Certificados y CAF están cifrados en reposo con
Fernet. La cookie de sesión es `httponly` + `secure` + `SameSite=Strict`
(`app/routers/auth.py:34`). Contraseña mínima de 12. Un cliente archivado no
autentica. Hay auditoría de cambios y de requests. Existen `MachineKey` por
consumidor, hasheadas en base y con rol propio.

### Huecos, por gravedad

**1. La clave de administración no tiene límite de intentos.** Es lo más
expuesto. El login del portal sí lo tiene (`app/routers/auth.py:24`, 10/min) y
los clientes máquina también (`app/security/tenant.py:25`, 30 fallos/5 min),
pero `X-Admin-Key` no pasa por ningún limitador — ver `_admin_principal` en
`app/security/auth.py`. Es la credencial con escritura sobre **todos** los
clientes y se puede probar sin tope. Aplicarle el mismo patrón por IP.

**2. La clave de bootstrap no caduca ni se puede apagar.** `DTE_ADMIN_API_KEY`
(`app/core/config.py:21`, comparada en `app/security/auth.py:86`) es una sola
clave estática en variable de entorno con poder total sobre todos los tenants.
Las `MachineKey` son mejores en todo —revocables, con rol, hasheadas— pero la
de entorno sigue viva en paralelo. Debería poder desactivarse una vez que
existan claves de máquina.

**3. Ningún header de seguridad.** `create_app` (`app/main.py`) sólo agrega
CORS. Faltan HSTS, `X-Frame-Options` o CSP `frame-ancestors`,
`X-Content-Type-Options` y `Referrer-Policy`. El portal se puede embeber en un
iframe ajeno, y ahí hay acciones destructivas (retirar CAF, eliminar cliente)
expuestas a clickjacking.

**4. El límite de tasa vive en la memoria de cada proceso**
(`app/security/ratelimit.py`, ya documentado ahí). Con 2 workers el límite
efectivo es el doble; con varias réplicas se multiplica. Para internet hay que
moverlo a Redis, o aplicarlo además en Traefik.

**5. Sin cuota por cliente.** El único freno es sobre *fallos* de
autenticación. Un cliente autenticado llama sin tope, y las operaciones caras
—firmar, hablar con el SII— no tienen límite: un cliente puede degradar el
servicio de los demás. En multiempresa importa.

**6. Sin segundo factor en el portal.** Quien administra el material tributario
de todos los clientes entra sólo con correo y contraseña. Es lo más caro de
implementar y lo que menos urge si el portal queda restringido por IP.

**7. `cors_origins` no se valida** (`app/core/config.py:25` y `:67`). Acepta
cualquier valor, incluido `*`, y se usa con `allow_credentials=True`. Debería
rechazar el comodín al arrancar, como ya hace con las claves débiles.

### Orden sugerido

Los tres primeros son baratos y cierran lo más expuesto. El 4 y el 5 son los
que de verdad importan para multiempresa en serio, y son más trabajo. El 6, al
final.

---

## 2. Despliegue en Dokploy

`docker-compose.dokploy.yml` está listo y validado, **pero no se ha desplegado**.
Publica tres superficies en dominios separados:

| Dominio | Qué es |
|---|---|
| `boletas.dimabe.cl` | Sitio público y anónimo. Su nginx sólo proxya `/api/public/` |
| `dte.dimabe.cl` | Portal de administración |
| `api.dimabe.cl` | API para clientes máquina (Odoo) |

Separados a propósito: el sitio anónimo no comparte origen con el portal que
custodia certificados, ni el API que autentica por `apiKey` con el navegador
que autentica por cookie. La base nunca sale de la red interna.

Al desplegar:
- Definir `DTE_SUPERADMIN_EMAIL` / `DTE_SUPERADMIN_PASSWORD`, o el portal queda
  sin forma de entrar.
- Considerar `PORTAL_ALLOWED_IPS` (lista blanca en Traefik). Vacía, la única
  barrera es el login.
- El API sale a internet **sólo si se crea el registro DNS** de `API_DOMAIN`.
  Si Odoo corre en el mismo servidor, es más seguro no crearlo y conectar Odoo
  a la red interna.

**La instancia arranca con la base vacía**: sin clientes, certificados ni CAF.
Hay que cargarlos por el portal o por la API de administración. Y si ese va a
ser el backend definitivo, conviene **emitir el set de boletas desde ahí**, no
desde la instancia local: si no, las boletas quedan en una base y el sitio
público consulta la otra.

Quedó ofrecido y **sin hacer** un script que cargue empresa, certificado, los
11 CAF y los servicios de una pasada.

---

## 3. Conector de Odoo

Verificado por un agente el 2026-09-07 contra la instancia de pruebas
(`odoo-community-test-odoo-1`, puerto 8169, base `cl_test`). El módulo está
instalado (19.0.1.4.0) y los 13 campos de configuración están expuestos en el
formulario de compañía. El manejo de errores es sólido: configuración
incompleta o servicio caído producen un `UserError` legible, no un traceback, y
un fallo de emisión al postear no revierte el posteo.

**Bug de gravedad media, sin corregir:** el botón *Probar conexión* no prueba
las credenciales que se usan para emitir. Siempre llama a `/rcv/documents` con
las credenciales genéricas de RCV (`dte_service_client.py:150-167`), nunca los
pares certificación/producción que usa la emisión (`_dte_env_credentials`,
`dte_service_client.py:97-119`). Una empresa que sólo emita y no use RCV verá
el botón fallar siempre, aunque su configuración de emisión esté correcta.
Debería probar el par del ambiente del diario.

**También pendiente:** la guía de despacho (tipo 52) está modelada con
transporte y chofer pero **nunca se probó de punta a punta** desde Odoo.

---

## 4. Deuda del propio servicio

- **Exportaciones en el Libro de Ventas**: entran en moneda extranjera tratadas
  como si fueran pesos (una factura de USD 15,40 va como `MntExe=15`). No es lo
  que bloquea la certificación —se descartó como causa—, pero está mal y hay
  que resolverlo antes de producción. El IECV es en pesos y espera la
  conversión al tipo de cambio observado.
- **Las tres ramas están empujadas pero sin mergear** a la principal:
  `feat/certificacion-sii` en el motor y en el servicio, `feat/guia-despacho`
  en el conector. Son fast-forward limpios.

---

## Ambientes: ya resuelto, para no volver a preguntarlo

`Customer.environment` es `CERTIFICATION` (Maullín) o `PRODUCTION` (Palena),
**por cliente**. Una empresa que opere en ambos son dos registros, cada uno con
su certificado, sus CAF y sus folios — y esa separación es la correcta, no un
rodeo: los CAF son distintos, los correlativos independientes, y mezclarlos
llevaría a emitir en producción con un folio de prueba. El conector de Odoo ya
tiene los dos pares de credenciales y elige según el campo
`dte_service_environment` del diario de ventas.
