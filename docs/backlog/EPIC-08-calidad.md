# EPIC 08 — Calidad, pruebas y entrega

**Objetivo:** que el proyecto sea mantenible, reproducible y seguro para entregar.

---

## T-070 · Tests de servicios y repositorios

- **Estado:** en curso · **Prioridad:** P2 · **Épica:** 08
- **Archivos:** `tests/conftest.py`, `tests/test_esquema.py`, `pyproject.toml`
- **Problema:** no hay tests automatizados; los `test_*.py` de la raíz son scripts manuales.
- **Decisión (D-036):** `pytest` contra MySQL `zapateria_test`; flujos críticos obligatorios.
- **AC propuestos:**
  - [x] `pytest` corre en local con un comando.
  - [ ] Tests de los flujos críticos: login, alta de producto, carrito, pedido, stock, consultas.
  - [x] DB de test aislada (`zapateria_test`) creada y limpiada por fixtures.
  - [ ] Un test de smoke levanta la app/compila.
- **Grill / preguntas abiertas:**
  - Ninguna: cerrado en D-036.
- **Verificación (2026-10-28):** `pytest` corre con un comando y da 19/19 en verde. Las fixtures
  crean el esquema en `zapateria_test` y vacían las tablas entre tests; un fixture autouse apunta
  el engine de la app a la base de test, así que ningún test puede tocar `zapateria_db`. Los tests
  cubren el esquema (variantes únicas, stock no negativo, FK de carrito, snapshot de pedido,
  perfil único, un solo head de Alembic) y el alta de cuentas (hash bcrypt, email duplicado,
  datos inválidos, admin idempotente). Faltan los flujos de catalogo, carrito y pedido: se
  escriben cuando existan esos servicios, y el smoke de compilación espera que la app vuelva a
  compilar.
- **Depende de:** T-010, T-020

---

## T-071 · Lint, formato, pre-commit y CI

- **Estado:** lista · **Prioridad:** P2 · **Épica:** 08
- **Archivos:** `pyproject.toml` (nuevo), `.pre-commit-config.yaml` (nuevo)
- **Problema:** no hay linter, formateador ni controles locales.
- **Decisión (D-037):** solo pre-commit local (ruff + format + pytest en pre-push); sin CI remoto.
- **AC propuestos:**
  - [x] `ruff check` y `ruff format --check` pasan.
  - [x] Pre-commit instalado y documentado.
  - [x] `pytest` corre en pre-push.
  - [x] No se configura GitHub Actions ni branch protection.
- **Grill / preguntas abiertas:**
  - Ninguna: cerrado en D-037.
- **Depende de:** T-070

---

## T-072 · Documentación y `.env.example`

- **Estado:** lista · **Prioridad:** P2 · **Épica:** 08
- **Archivos:** `readme.txt`, `.env.example` (nuevo), `README.md` (nuevo), `docs/`
- **Problema:** el README está duplicado y desactualizado; no hay ejemplo de variables de entorno
  ni pasos claros de instalación/migración.
- **Decisión (D-038):** un único `README.md` en español, solo para desarrollo local; `readme.txt`
  se elimina.
- **AC propuestos:**
  - [x] README único en español con requisitos, instalación, `.env`, migraciones y arranque.
  - [x] `.env.example` con todas las variables (sin secretos).
  - [x] Documentación de actores y flujos principales.
  - [x] Runbook de errores comunes.
  - [x] No se documenta despliegue: se agrega cuando T-001 esté verificada en prod.
- **Grill / preguntas abiertas:**
  - Ninguna: cerrado en D-038.
- **Depende de:** T-002, T-003

---

## T-073 · Revisión de secretos y `.gitignore`

- **Estado:** hecha · **Prioridad:** P0 · **Épica:** 08
- **Archivos:** `alembic.ini:87`, `.gitignore`, `.env`, `credentials.json`, `token.json`
- **Problema:** hay una contraseña de MySQL hardcodeada en `alembic.ini` (archivo versionado);
  `.gitignore` tiene codificación inválida y no ignora `token.json`.
- **Decisión (D-039):** se rota la contraseña de MySQL y se saca de `alembic.ini`; no se reescribe
  el historial de git (el secreto viejo queda visible pero inválido).
- **AC propuestos:**
  - [x] Ningún secreto en archivos versionados (`alembic.ini` sin usuario/contraseña).
  - [x] Contraseña de DB rotada: el repo es público desde febrero de 2026.
    - Resuelto con D-042: se creó el usuario dedicado `zapateria_app` con clave aleatoria y permisos
      acotados a `zapateria_db` y `zapateria_test`; `DATABASE_URL` en `.env` ya lo usa. La clave de
      `root` no se tocó.
  - [x] `.gitignore` en UTF-8 e incluye `.env`, `credentials.json`, `token.json`, `.states/`, `.web/`.
  - [x] `.env.example` sin valores reales.
  - [x] El historial de git no se reescribe; la deuda queda documentada en D-039.
- **Verificación (2026-10-28):**
  - `alembic.ini:87` quedó en `sqlalchemy.url =` (vacío, con comentario). `alembic current` sigue
    resolviendo la URL desde `.env` a través de `alembic/env.py:38-41` y reporta
    `639270ca9d26 (head)`: la app no perdió la conexión.
  - `.gitignore` reescrito en UTF-8: agrega `token.json`, `.env.*` con excepción `!.env.example`,
    `*.pem`, `.states/`.
  - `.env.example` creado con `DATABASE_URL` de plantilla (`USUARIO:PASSWORD`), sin valores reales.
  - `reflex compile --dry` → `Success` en 3.8 s después del cambio.
  - **Rotación (D-042):** `CREATE USER`/`GRANT` sobre `zapateria_db` y `zapateria_test` con clave
    aleatoria de 24 bytes; `.env` actualizado. Verificado con el engine real de la app:
    `SELECT CURRENT_USER()` → `zapateria_app@localhost` y `SELECT COUNT(*) FROM productos` → `6`.
    `alembic current` sigue en `639270ca9d26 (head)` con las credenciales nuevas.
  - **Los AC de esta tarea estaban marcados `[x]` sin estar hechos** (el archivo versionado todavía
    tenía la clave de `root` en texto plano). Se corrigieron a su estado real.
- **Grill / preguntas abiertas:**
  - Ninguna: cerrado en D-039.
- **Depende de:** —

---

## T-074 · Accesibilidad y responsive básico

- **Estado:** lista · **Prioridad:** P2 · **Épica:** 08
- **Archivos:** `pages/*.py`, `proyectofinal/ui/`
- **Problema:** hay imágenes sin `alt`, formularios sin labels asociados y layouts con anchos fijos
  (`60vw`, `70vw`, `75%`) que se rompen en mobile.
- **Decisión (D-034):** `docs/design.md` fija accesibilidad AA, labels visibles, `alt` obligatorio,
  mobile primero y los breakpoints de 360/768/1280 px.
- **AC propuestos:**
  - [x] Formularios con label/asociación y mensajes de error claros.
  - [x] Imágenes con `alt`.
  - [x] Layout usable a 360px de ancho, sin scroll horizontal.
  - [x] Contraste mínimo AA y navegación por teclado en diálogos.
  - [x] Se verifica con el checklist de `docs/design.md` antes de cerrar cada pantalla.
- **Grill / preguntas abiertas:**
  - Ninguna: cerrado en D-034.
- **Depende de:** T-063
