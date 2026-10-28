# AGENTS.md

Contexto para agentes que trabajen en este repositorio. Leer esto antes de tocar código.

## Proyecto

Tienda online de indumentaria/calzado hecha con **Reflex + MySQL**. Dos actores:

- **Comprador registrado:** ve catálogo y precios, agrega al carrito, compra, consulta sus pedidos.
- **Administrador:** gestiona productos, stock, pedidos y consultas. No compra.

Comprar requiere cuenta (no hay carrito de invitado). Ver `docs/backlog/DECISIONS.md` (D-002).

## Documentos que mandan

| Documento | Qué define |
|---|---|
| `docs/backlog/README.md` | Índice de tareas, estados y Definition of Done |
| `docs/backlog/EPIC-*.md` | Detalle de cada tarea con criterios de aceptación |
| `docs/backlog/DECISIONS.md` | Decisiones cerradas (D-001 a D-020) |
| `docs/design.md` | Sistema de diseño obligatorio para toda la UI |

**Regla:** no se implementa una tarea con preguntas abiertas o AC sin confirmar. Si aparece una
decisión nueva, se registra en `DECISIONS.md` antes de codear.

## Regla de oro: el backlog se actualiza mientras se trabaja

El backlog es la fuente de verdad y el tablero (`.\tablero.ps1`) lo lee en vivo. No hay un archivo
que regenerar: si el `.md` no cambia, el tablero no cambia. Por eso **todo agente actualiza el
backlog en el mismo commit que el código**, nunca "después".

Estados válidos, escritos exactamente así (son las columnas del tablero): `propuesta`,
`en grill`, `lista`, `en curso`, `bloqueada`, `hecha`. No inventar estados nuevos: crearían
columnas nuevas.

| Momento | Qué tocar |
|---|---|
| Al empezar una tarea | `- **Estado:** lista` → `en curso` en el `EPIC-*.md` |
| Al cerrar cada AC | `- [ ]` → `- [x]` en el `EPIC-*.md` |
| Al cerrar la tarea | `- **Estado:** hecha` en el `EPIC-*.md` |
| Siempre, junto con el estado | La fila de esa tarea en la tabla de `docs/backlog/README.md` (última columna) |
| Si la tarea no existe | Crearla primero en la épica **y** en el índice del README |
| Si aparece un bloqueo | `- **Estado:** bloqueada` y anotar qué falta |

Las dos ubicaciones tienen que coincidir. El tablero marca en rojo (`README: <estado>`) cualquier
tarea cuyo estado de la épica no coincida con el del índice.

## Stack real (no el ideal)

- Python 3.13.1, entorno virtual en `.venv/` (lo crea `uv sync` desde `uv.lock`; D-027).
- Reflex **0.10.1**, SQLModel 0.0.30, SQLAlchemy 2.0.46, pydantic **2.14.1**, Alembic 1.18.1.
  Versiones verificadas con `importlib.metadata` sobre `.venv/` el 2026-10-28.
- MySQL 8, base `zapateria_db`, URL única en `.env` (`DATABASE_URL`).
- La migración a Reflex 0.10.x **ya está hecha** (T-006). Escribir APIs de 0.10: `.model_dump()`
  en vez de `.dict()`, modelos pydantic v2, y no usar `--single-port` (no existe).

## Arquitectura

```
model/ → repository/ → service/ → state/ → pages/
```

- `model/`: SQLModel. Sin lógica.
- `repository/`: consultas. No conoce HTTP ni UI.
- `service/`: validación y reglas de negocio.
- `state/`: estado de Reflex. **No abre sesiones ni importa `engine`** (T-062).
- `pages/`: solo composición visual. **No accede a la DB.**

## Comandos

```powershell
uv sync                    # instala/actualiza .venv desde uv.lock
.\run.ps1                  # dev con recarga
.\run.ps1 -Prod            # producción
.\.venv\Scripts\reflex.exe compile --dry  # validar sin levantar
alembic upgrade head       # migraciones
.\.venv\Scripts\python.exe seed.py        # admin + datos de ejemplo
.\tablero.ps1              # tablero kanban del backlog (solo lectura)
.\tablero.ps1 -Write       # tablero con arrastre que reescribe el .md
```

- Frontend en `:3000`, backend en `:8000`. Tablero del backlog en `:8765`.
- **Siempre activar el venv** (o prefijar `venv\Scripts` al `PATH`). Si no, Reflex lanza el `granian`
  global y el backend muere con `TypeError: 'module' object is not callable` en `@rx.event`.
- **Antes de levantar el tablero del backlog, preguntar al usuario si lo quiere levantar.**
  No arrancarlo por iniciativa propia: queda un proceso escuchando en `:8765`.

## Reglas de código

- Identificadores, comentarios y strings de código en **inglés**; **nombres de archivo en español**
  con el sufijo de capa (`producto_repositorio.py`, `carrito_estado.py`) y sin errores de
  ortografía (D-040). Documentación y copy de UI en **español**.
- UI: usar solo componentes de `proyectofinal/ui/`. Prohibido hex sueltos, `box_shadow` o
  `color_scheme` en `pages/` (T-063).
- Estados de UI obligatorios: vacío, carga (`Skeleton`) y error. Sin spinners de página completa.
- Sin `print()` de depuración: usar `logging` (T-064).
- Sin secretos en el repo: `.env` no se commitea, `.env.example` sin valores reales.
- Commits convencionales, sin atribución de IA.

## Trampas conocidas

| Problema | Estado |
|---|---|
| `app_globals.current_user_id` es global de módulo y mezcla sesiones | T-020 |
| Contraseñas en texto plano | T-022 |
| `/admin_dashboard`, `/pedidos_admin` y `/consulta_admin` abiertas por URL | T-023 |
| Rutas duplicadas y doble registro (`/` vs `/catalogo`) | T-061 |
| `productos` sin variante: el stock está por color y falta el talle | D-009, T-050 |
| La DB local puede estar vacía: si el catálogo no muestra nada, verificar `SELECT COUNT(*) FROM productos` | — |

## Antes de cerrar una tarea

- [ ] AC de la tarea marcados en la épica (`- [x]`).
- [ ] `- **Estado:** hecha` en la épica **y** en la fila del índice del `README.md`.
- [ ] `reflex compile --dry` sin errores ni warnings nuevos.
- [ ] Flujo afectado probado a mano.
- [ ] `DECISIONS.md` actualizado si hubo decisión.
- [ ] Sin `print()`, sin secretos, sin estilos sueltos.
