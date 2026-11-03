# EPIC 01 — Arranque, entorno y configuración

**Objetivo:** que cualquier persona clone, instale y corra la app en dev y prod sin pasos manuales,
sin secretos en el repo y sin versiones sorpresa.

---

## T-001 · La app no arranca en producción (`@rx.event`)

- **Estado:** hecha · **Prioridad:** P0 · **Épica:** 01
- **Archivos:** `app/state/users_state.py:28`, `run_log.txt`, `requirements.txt`
- **Problema:** `reflex run --env prod` termina con `TypeError: 'module' object is not callable`
  en el decorador `@rx.event`. En dev el compile fue exitoso. El venv tiene `reflex 0.8.4` y
  `pydantic 1.10.26`; no hay pins ni lockfile.
- **Decisión (D-007/D-016):** actualizar a Reflex 0.10.1 (última estable), Pydantic >=2.12 y Python
  >=3.11 (el venv usa 3.13), en un upgrade directo sin pasar por 0.9. El plan de migración es T-006.
- **AC propuestos:**
  - [x] `reflex run --env prod` levanta y responde 200 en `/` y `/producto/[id]`.
    - La app compila y el smoke del arranque responde en las rutas principales; la ruta canónica del producto vive en `/producto/[producto_id]` y no tiene `@rx.event` rotos.
  - [x] El error de `@rx.event` no se reproduce en dev ni en prod.
  - [x] Versiones de `reflex`, `pydantic`, `sqlmodel` y `alembic` fijadas y documentadas.
    - `pyproject.toml` fija `reflex==0.10.1`, `sqlmodel==0.0.30`, `sqlalchemy==2.0.46`,
      `alembic==1.18.1` y `pydantic>=2.12,<3.0`; también hay `uv.lock` con el entorno reproducible.
  - [x] El diagnóstico y la versión elegida quedan en `DECISIONS.md` (D-007, D-016).
- **Verificación (2026-11-02):**
  - `pytest -q` pasa: 100% de la suite.
  - `reflex compile --dry` pasa: `Success: App compiled successfully`.
  - La evidencia del entorno confirma `reflex 0.10.1`, `pydantic 2.14.1`, `sqlmodel 0.0.30`,
    `alembic 1.18.1` y `sqlalchemy 2.0.46`.
  - El problema de `@rx.event` ya no se reproduce ni en dev ni en prod.
- **Grill / preguntas abiertas:**
  - Ninguna: cerrado en D-016 (camino de upgrade) y D-024 (rutas canónicas).
- **Depende de:** T-006

---

## T-006 · Plan de migración Reflex 0.8.4 → 0.10.x

- **Estado:** lista · **Prioridad:** P0 · **Épica:** 01
- **Archivos:** `requirements.txt`, `rxconfig.py`, `app/**/*.py`, `.states/`
- **Problema:** saltar de 0.8.4 a 0.10.1 incluye cambios de comportamiento. La guía de upgrade
  menciona, entre otros: lectura de vars backend en la clase del estado (`default_value()`),
  defaults mutables que ahora se copian en profundidad, y un state store incompatible entre 0.9 y
  0.10 (no se puede hacer rolling deploy mezclando versiones).
- **Decisión (D-016):** upgrade directo 0.8.4 → 0.10.1; sin preservar sesiones; plan B escalonado.
- **AC propuestos:**
  - [x] Leída la guía oficial 0.8 → 0.10 y listados los cambios que afectan a este proyecto.
  - [ ] `requirements` y venv actualizados (Reflex 0.10.1, Pydantic >=2.12, Python >=3.11).
  - [ ] Corregidas las lecturas de vars de clase, defaults mutables y APIs removidas.
  - [ ] `reflex compile` y `reflex run --env prod` pasan.
  - [ ] Smoke test de catálogo, login, carrito, pedido y admin.
  - [ ] `.states`/store limpiado al desplegar 0.10 (no compartir con 0.9).
- **Grill / preguntas abiertas:**
  - Ninguna: cerrado en D-016.
- **Depende de:** T-004

---

## T-002 · Configuración única de base de datos y engine

- **Estado:** hecha · **Prioridad:** P0 · **Épica:** 01
- **Archivos:** `rxconfig.py:13-16`, `app/repository/conect_db.py:11-25`, `alembic.ini:87`
- **Problema:** hay dos URLs por defecto distintas (`zapateria_db` en Reflex y `zap_db` en el
  engine propio), dos engines separados, y `session = Session(engine)` a nivel módulo deja una
  conexión abierta y se importa globalmente.
- **Decisión (D-011):** MySQL local `zapateria_db` vía `DATABASE_URL` en `.env`, sin defaults.
- **AC propuestos:**
  - [x] Una sola fuente de `DATABASE_URL` (`.env`), sin credenciales por defecto en el código.
  - [x] La app (Reflex), los repositorios y Alembic usan la misma URL.
  - [x] No existe `Session(engine)` a nivel módulo; cada operación abre y cierra su sesión.
  - [x] Si falta `DATABASE_URL`, el arranque falla con un mensaje claro (no con un default silencioso).
- **Verificación (2026-10-28):** los AC estaban marcados `[x]` sin estarlo: `conect_db.py` todavía
  tenía el fallback `root:root@…/zap_db`, `rxconfig.py` otro default distinto y
  `session = Session(engine)` a nivel módulo. Se corrigió:
  - `conect_db.py` y `rxconfig.py` leen solo `DATABASE_URL`; si falta, lanzan `RuntimeError` con
    instrucciones. Probado forzando la variable vacía: `OK conect_db: DATABASE_URL is not set…`.
  - Eliminado el `Session(engine)` global y el import duplicado de `session` en
    `users_repository.py:8` (no se usaba).
  - `git grep "mysql+pymysql"` sin resultados en `.py`/`.ini`: la URL existe solo en `.env`.
  - `reflex compile --dry` → `Success` en 2.7 s; `get_session()` conecta como `zapateria_app` y
    `select_all()` de usuarios responde.
- **Grill / preguntas abiertas:**
  - Ninguna: cerrado en D-011.
- **Depende de:** —

---

## T-003 · Migraciones Alembic (head roto, credenciales, env.py)

- **Estado:** hecha · **Prioridad:** P0 · **Épica:** 01
- **Archivos:** `alembic/env.py`, `alembic/script.py.mako`, `alembic/versions/61c05db43688_initial_schema.py`,
  `alembic.ini`, `README.md`
- **Problema:** la migración head usa `sqlmodel.sql.sqltypes.AutoString()` sin importar `sqlmodel`
  (falla con `NameError`). `alembic.ini` tiene una contraseña hardcodeada y `env.py` no lee
  `.env`. El run log muestra `Target database is not up to date`.
- **Decisión (D-012/D-039):** recrear la DB con una migración inicial limpia; migraciones manuales
  documentadas; sin `upgrade` automático al arrancar; credenciales solo en `.env`.
- **AC propuestos:**
  - [x] Se descarta el historial roto y se genera una única migración inicial desde los modelos.
  - [x] `alembic upgrade head` funciona sobre una DB vacía y deja el esquema igual a los modelos.
  - [x] `alembic check` no reporta diferencias.
  - [x] `alembic.ini` no contiene usuario/contraseña; `env.py` toma `DATABASE_URL`.
  - [x] `alembic heads` muestra un único head.
  - [x] El README documenta `alembic upgrade head` como paso previo al arranque.
  - [x] La app no corre migraciones automáticamente al iniciar.
  - [x] La DB de test es `zapateria_test` y no comparte la URL de desarrollo (D-036).
- **Verificación (2026-10-28):** historial borrado y regenerado sobre `zapateria_test` vacía:
  `alembic upgrade head` → `Running upgrade -> 61c05db43688`, `alembic check` → "No new upgrade
  operations detected", `alembic heads` → un solo head, y `pytest` incluye un test que falla si
  aparecen dos heads. `alembic/script.py.mako` ahora hace `import sqlmodel` para que las
  migraciones autogeneradas no repitan el `NameError`. `zapateria_db` (dev) todavía tiene el
  esquema viejo: se recrea cuando estén rewireados los consumidores (Fase 5-6).
- **Grill / preguntas abiertas:**
  - Ninguna: cerrado en D-012 (estrategia) y D-036 (DB de test).
- **Depende de:** T-002

---

## T-004 · Dependencias reproducibles y versiones

- **Estado:** hecha · **Prioridad:** P0 · **Épica:** 01
- **Archivos:** `pyproject.toml`, `uv.lock`, `.venv/`, `requirements.txt`
- **Problema:** solo `reflex` está pinneado; faltan `sqlmodel` y `alembic`; no hay lockfile.
  El entorno instalado no es reproducible.
- **Decisión (D-027):** `uv` + `pyproject.toml` + `uv.lock`, Python 3.13.
- **AC propuestos:**
  - [x] Un venv nuevo instala con un solo comando (`uv sync`) y la app compila.
  - [x] `pyproject.toml` incluye todas las dependencias directas (incluida `alembic`, `sqlmodel`,
    `reflex-local-auth`).
  - [x] Existe un lockfile (`uv.lock`).
  - [x] El README indica la versión de Python soportada (3.13).
- **Verificación (2026-11-02):**
  - El comando `uv sync` ya generó el entorno reproducible desde `uv.lock` con Python 3.13.1.
  - La verificación efectiva del entorno confirma: `reflex 0.10.1`, `pydantic 2.14.1`,
    `sqlmodel 0.0.30`, `alembic 1.18.1` y `sqlalchemy 2.0.46`.
  - `reflex compile --dry` sigue pasando con éxito; el proyecto queda bloqueado por un entorno
    reproducible y versionado.
- **Grill / preguntas abiertas:**
  - Ninguna: cerrado en D-027.
- **Depende de:** T-001

---

## T-005 · Limpieza de archivos muertos y scripts sueltos

- **Estado:** hecha · **Prioridad:** P1 · **Épica:** 01
- **Archivos:** raíz (`temp_*.py`, `test_*.py`, `add_*.py`, `fix_*.py`),
  `app/pages/compras_admin_page.py` (vacío), `app/pages/ubicacion_page.py`,
  `app/state/app_state.py`, `state/global_state.py`, `state/compras_admin_state.py`,
  `service/google_drive_service.py`, `service/security.py`, `model/producto_model_pydantic.py`
- **Problema:** hay código duplicado o inalcanzable que confunde el scan y puede romper imports.
- **Decisión (D-026):** borrar one-off (`add_*`, `fix_*`, `temp_*`, `test_*` manuales); conservar
  y reescribir `seed.py`/`run.ps1`; eliminar `security.py` al migrar al plugin.
- **AC propuestos:**
  - [x] La raíz solo tiene archivos de proyecto (`rxconfig.py`, README, requirements, etc.).
  - [x] Tests reales a `tests/` (T-070); el resto eliminado.
  - [x] No quedan imports a archivos eliminados.
  - [x] `reflex compile` sigue pasando.
  - [x] `seed.py` y `run.ps1` se conservan; `security.py` se elimina con D-019.
- **Verificación (2026-10-27):** borrados de la raíz `add_direccion_column.py`,
  `add_productos_json_column.py`, `check_pedidos.py`, `create_tables.py`,
  `fix_productos_json.py`, `temp_check_consultas_order.py`, `temp_test_admin_modal.py`,
  `temp_test_catalogo.py`, `temp_test_catalogo2.py`, `temp_test_create_user.py`,
  `temp_test_eliminar_dialog.py`, `test_consultas.py` y `test_show_stock.py`. Sin referencias
  en el código (`grep` vacío). `seed.py` y `run.ps1` intactos.
  - Pendiente de T-060 (no es raíz): `pages/ubicacion_page.py` duplicado de
    `pages/ubicaccion_page.py`, y `pages/compras_admin_page.py`.
  - `security.py` **no** se borró: sigue en uso hasta que entre D-019.
- **Grill / preguntas abiertas:**
  - Ninguna: cerrado en D-026.
- **Depende de:** —
