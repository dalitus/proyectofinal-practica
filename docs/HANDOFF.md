# Handoff — estado real y roadmap

> Fecha: 2026-10-27. Para arrancar una sesión nueva sin releer todo el historial.
> Antes de tocar código: leer `AGENTS.md`, `docs/backlog/README.md` y este archivo.

---

## 1. Qué es

Tienda online de indumentaria/calzado con **Reflex 0.10.1 + MySQL**. Dos actores: administrador
(gestiona productos, stock, pedidos y consultas; no compra) y comprador registrado (catálogo,
carrito, pedidos). El invitado ve catálogo y detalle, pero comprar exige cuenta.

Arquitectura: `model → repository → service → state → pages`.

## 2. Estado verificado hoy (no aspiracional)

| Componente | Estado | Evidencia |
|---|---|---|
| Reflex / Pydantic | **Ya migrado** a 0.10.1 / 2.14.1 | `pyproject.toml` + `.venv` |
| `reflex compile --dry` | **Pasa** en `wip/baseline` | ejecutado 2026-10-28 |
| Arranque en prod | **Sin verificar** | hay que correr `run.ps1 -Prod` y pedir 200 |
| `reflex-local-auth` | **Instalado** (0.5.0) y verificado | `pyproject.toml` + spike en T-022 |
| `alembic/env.py` | Lee `DATABASE_URL` | `alembic/env.py` |
| `alembic.ini` | **Sin credenciales** (vacío; D-039/D-042) | `alembic.ini` |
| Migración inicial | **Una sola, desde los modelos finales** (`61c05db43688`) | `alembic upgrade head` + `alembic check` OK en `zapateria_test` |
| `model/__init__.py` | **11 tablas finales**, incluidas las del plugin | `SQLModel.metadata.tables` |
| UI | Solo `ui/tokens.py` (4 diccionarios) | sin componentes ni shell |
| Tests | `pytest` con 19 tests (esquema + identidad) | `tests/`, verde sobre `zapateria_test` |
| Seed | Admin + 6 productos con variantes, idempotente | `seed.py`, verificado contra MySQL |
| Árbol de trabajo | Rama `wip/esquema` (modelos+ migración) sobre `wip/baseline` | `e563f63` |

⚠️ `wip/esquema` **no compila la app**: los consumidores todavía importan los modelos borrados.
`wip/baseline` sigue siendo la rama que arranca.

Conclusión: el **upgrade está hecho**, la **arquitectura de datos no**. El trabajo pendiente no es
"migrar Reflex", es **rediseñar el esquema y la identidad** y después reconstruir la UI sobre eso.

## 3. Regla de oro

El backlog es la fuente de verdad: 43 tareas en `docs/backlog/`, todas en `lista`, con 40
decisiones cerradas en `docs/backlog/DECISIONS.md`. **No se implementa una tarea con preguntas
abiertas.** Si aparece una decisión nueva, se registra en `DECISIONS.md` antes de codear.

## 4. Roadmap recomendado

El orden no sigue las prioridades del backlog: sigue los **bloqueos reales**. Cada fase tiene un
gate verificable; no se pasa a la siguiente sin cumplirlo.

### Fase 0 · Baseline y secreto (30 min)

1. ✅ **Hecho** (2026-10-27): rama `wip/baseline` + commit `fd090f7` con todo el trabajo real
   (docs, `ui/`, `seed.py`, `run.ps1`, migración, `AGENTS.md` corregido a Reflex 0.10.1).
2. ✅ **Hecho** (2026-10-28): **T-073** cerrada con D-042. `alembic.ini` sin credenciales, `.gitignore`
   en UTF-8 (incluye `token.json`), `.env.example` creado y la app conectada con el usuario dedicado
   `zapateria_app` (permisos solo sobre `zapateria_db` y `zapateria_test`). `root` no se tocó.

**Gate:** `git grep` del secreto viejo no devuelve nada en archivos actuales; la app sigue
conectando; el historial queda como deuda documentada (D-039).

### Fase 1 · Cerrar el arranque (medio día)

- ✅ **T-004** (2026-10-28): `pyproject.toml` + `uv.lock` (77 paquetes) y `.venv` creado con
  `uv sync`. `run.ps1` detecta `.venv` o `venv`. Queda abierto solo el AC de `reflex-local-auth`,
  que entra con el spike de la Fase 2.
- **T-001**: `/producto/[id]` sigue pendiente de T-031; el resto del smoke en prod pasó (2026-10-28).
- ✅ **T-005**: hecha.

**Gate:** compile pasa, prod responde 200, la raíz solo tiene archivos de proyecto.

### Fase 2 · Spike de identidad (1 día)

✅ **Hecho (2026-10-28, rama `spike/local-auth`).** `reflex-local-auth` 0.5.0 instala y resuelve
sobre Reflex 0.10.1 sin conflictos; registro, hash bcrypt y sesión de 7 días verificados en el
navegador. Detalle en T-022. **No hizo falta el plan B de D-019.**

**Gate:** cumplido (login real contra la DB). Queda para la Fase 4 el `AuthState` propio,
`require_login` y el logout desde UI.

### Fase 3 · Modelos finales y UNA migración (2-3 días)

✅ **Hecho (2026-10-28, rama `wip/esquema`).** Modelos finales aplicados en el orden previsto:
**D-009** (`Stocks` es la variante `(producto, color, talle)` con unique y check de stock no
negativo), **D-019** (`LocalUser` + `UserProfile`, borrados `users` y `gerentes`), **D-023**
(`Categoria` + `producto.categoria_id`), **D-028** (`producto.activo`), **D-029** (`PedidoItem` con
snapshot, borrados `detalles`/`envios`/`presupuestos`/`solicitan`). La migración vieja se borró y
se regeneró la inicial única (`61c05db43688`). Arnés de tests (T-070) con `pytest` contra
`zapateria_test`: 9/9 en verde.

**Gate:** cumplido en `zapateria_test`. `upgrade head` OK, `alembic check` sin diferencias,
`alembic heads` con un solo head (hay un test que lo hace fallar si se duplica), `pytest` verde
con el esquema nuevo.

**Deuda que deja esta fase:** 28 archivos de `repository/`, `service/`, `state/`, `pages/` y
`seed.py` siguen importando los modelos borrados, así que `wip/esquema` **no compila la app**
todavía. Se resuelve en las Fases 4-6. `zapateria_db` (dev) mantiene el esquema legacy hasta ese
momento.

### Fase 4 · Identidad y sesión (2 días)

🟡 **En curso (2026-10-28).** Hecho: `service/auth_servicio.py` con alta de comprador
(`LocalUser` + `UserProfile` en una transacción), búsqueda de perfil y bootstrap del admin
idempotente (**T-022** cerrada, **T-024** a medias); `seed.py` reescrito sobre el esquema nuevo y
verificado contra MySQL real; 8 tests de identidad en verde. Falta: `AuthState` sobre
`LocalAuthState` (vars `user_id`/`is_admin`/`logeado`), matar `app_globals` (**T-020**), login
único con `redirect_to` (**T-021**), guardas por rol (**T-023**) y la UI de cuenta.

**Gate:** dos navegadores con carritos distintos; admin entra al panel; comprador recibe 403;
invitado va a `/login` con `redirect_to`.

⚠️ Ese gate no se puede verificar hasta la Fase 5: las páginas y estados viejos siguen
importando los modelos borrados, así que la app no compila en `wip/esquema`.

### Fase 5 · Esqueleto de UI y limpieza (2 días)

🟢 **Cerrada la limpieza (2026-10-28).** **T-060 hecha:** se borró todo `app/pages/` y
`app/state/`, y todos los `app/service/*` y `app/repository/*` salvo `auth_servicio.py` y
`conect_db.py`. Sobreviven `app/model/` (11 tablas), `app/ui/tokens.py` y el alta de comprador.
La app compila otra vez (17 módulos contra 34 antes) y levanta: `/` es una home provisoria,
`/login` es la página del plugin y `/register` es propia (D-044) porque la del plugin no crea
`UserProfile`. `seed.py` arreglado y corrido sobre `zapateria_db` recreada.

**Pendiente en esta fase:** **T-062** (handlers finos), **T-061** (rutas únicas), **T-063**
(tokens, primitivos, shell) y **T-064** (logging, sin `print()`).

**Por qué antes de las pantallas:** construir páginas con los estilos y estados actuales significa
reescribirlas dos veces.

**Gate:** `rg` de los nombres borrados sin resultados, compile sin warnings nuevos, catálogo piloto
con el shell nuevo.

⚠️ Lo que la Fase 5 borró (carrito, ubicación, subida de imágenes, panel del admin) **no está
reimplementado**: vuelve en las fases 6 y 7 sobre el esquema nuevo. Ese es el AC de T-060 que
quedó abierto a propósito.

### Fase 6 · Camino del comprador (1 semana)

**T-030/031/032/033/034** (catálogo, detalle, precio, filtros, imágenes) y **T-040/042/043/044/045**
(carrito, stock, `/checkout`, estados del pedido, borrar la consulta automática).

**Gate:** comprar de punta a punta, con stock descontado y visible en el admin.

### Fase 7 · Admin y cierre (1 semana)

**T-050** (CRUD de variantes + imagen) → **T-051/052/053** (pedidos, consultas, auditoría) →
**T-075** (rename final) → **T-072** (README) → **T-074** (accesibilidad) → **T-071** (pre-commit).

**Por qué el rename al final:** una decena de los archivos mal nombrados los borran T-013, T-019 y
T-060. Renombrar antes es hacer el mismo trabajo dos veces.

**Gate:** Definition of Done global de `docs/backlog/README.md`.

## 5. Lo que NO hay que hacer

- **No usar `639270ca9d26`.** Nació de los modelos legacy; se descarta y se regenera en la Fase 3.
- **No generar una migración por feature.** Una sola, al final de la Fase 3.
- **No renombrar archivos antes de T-060.** T-075 depende de las eliminaciones.
- **No mezclar rename con lógica** en el mismo commit: movimientos + imports, nada más.
- **No commitear `.env`** ni credenciales: el repo es público desde febrero de 2026.
- **No asumir APIs de 0.8.4**: ya estamos en 0.10.1 (no existe `--single-port`, `.dict()` es
  `model_dump()`).
- **No implementar con preguntas abiertas** del backlog.

## 6. Primeros pasos concretos

```powershell
uv sync                                 # crea/actualiza .venv desde uv.lock

.\.venv\Scripts\reflex.exe compile --dry   # debe decir Success
```

Después: abrir `docs/backlog/EPIC-02-datos-y-contratos.md` y encarar la Fase 2 (spike de identidad).

## 7. Comandos

```powershell
uv sync                                # dependencias desde uv.lock
.\run.ps1                              # dev con recarga
.\run.ps1 -Prod                        # producción (verificar 200)
.\.venv\Scripts\reflex.exe compile --dry
alembic upgrade head
.\.venv\Scripts\python.exe seed.py
```

Siempre con el `.venv` activo (o prefijando `.venv\Scripts` al `PATH`), si no Reflex lanza el
`granian` global y muere con `TypeError: 'module' object is not callable`.

## 8. Mapa de archivos

| Archivo | Para qué |
|---|---|
| `docs/backlog/README.md` | índice, estados y Definition of Done |
| `docs/backlog/EPIC-01..08` | AC y detalle por tarea |
| `docs/backlog/DECISIONS.md` | D-001..D-040, la fuente de verdad de producto |
| `docs/design.md` | sistema de diseño obligatorio |
| `AGENTS.md` | reglas de código, comandos y trampas |
| `rxconfig.py`, `app/repository/conect_db.py` | configuración de DB (ambos deben leer `.env`) |
| `alembic.ini`, `alembic/env.py` | migraciones |

## 9. Riesgos abiertos

| Riesgo | Impacto | Mitigación |
|---|---|---|
| `reflex-local-auth` sin release probado en 0.10.1 | Alto | Spike en Fase 2; plan B en D-019 |
| Contraseña de MySQL expuesta en el historial público | Alto si se expone MySQL | Rotar en Fase 0 (D-039) |
| Migración actual generada desde modelos legacy | Alto si se aplica | Descartar y regenerar en Fase 3 |
| Cambios 0.9→0.10 en `default_value()` y defaults mutables | Medio | Smoke test por pantalla, no confiar en el compile |
| Árbol de trabajo sucio con trabajo sin commitear | Medio | Baseline de la Fase 0 |
