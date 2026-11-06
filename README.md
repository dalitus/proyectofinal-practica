# Tienda online de Calzado Fermin

Aplicación web de venta de Calzado Fermin hecha con **Reflex + MySQL**.
Dos actores: el **administrador** gestiona productos, stock, pedidos y consultas;
el **comprador registrado** ve el catálogo, arma el carrito, compra y consulta sus
pedidos. Comprar requiere cuenta (D-002).

## Stack

| Pieza | Versión |
|---|---|
| Python | **3.13** |
| Reflex | 0.10.1 |
| SQLModel / SQLAlchemy | 0.0.30 / 2.0.46 |
| Alembic | 1.18.1 |
| MySQL | 8 |

## Requisitos

- **Python 3.13** (el proyecto no soporta 3.12 ni 3.14: `requires-python = ">=3.13,<3.14"`).
- **MySQL 8** con una base creada.
- **Node.js >= 22.22**: Reflex compila el frontend con Node.
- **uv**: gestor de dependencias y lockfile (D-027).

## Instalación

```powershell
uv sync                              # crea .venv desde uv.lock
Copy-Item .env.example .env          # completar DATABASE_URL con credenciales reales
.\.venv\Scripts\Activate.ps1
alembic upgrade head                 # crea el esquema
```

Opcional, para tener datos de ejemplo:

```powershell
python seed.py
```

## Ejecución

```powershell
.\run.ps1          # desarrollo, con recarga
.\run.ps1 -Prod    # producción
.\run.ps1 -Port 3001
```

`run.ps1` activa el entorno virtual antes de lanzar Reflex. **No** lo ejecutes con
un `reflex` global: el backend toma `granian` del `PATH` y muere con
`TypeError: 'module' object is not callable`.

Frontend en `http://localhost:3000`, backend en `http://localhost:8000`.

## Variables de entorno

Todas viven en `.env` (no se commitea). `.env.example` trae la plantilla sin credenciales reales.

| Variable | Obligatoria | Para qué |
|---|---|---|
| `DATABASE_URL` | Sí | URL SQLAlchemy/MySQL de la app, los repositorios y Alembic (D-011). Formato `mysql+pymysql://USUARIO:PASSWORD@localhost:3306/zapateria_db`. Si falta, la app corta con un `RuntimeError` claro. |
| `ADMIN_EMAIL` | Solo para `seed.py` | Email de la cuenta administradora inicial (D-013). |
| `ADMIN_PASSWORD` | Solo para `seed.py` | Contraseña inicial del administrador; cambiala antes de usar la app fuera de tu máquina. |
| `ADMIN_NOMBRE` | Solo para `seed.py` | Nombre visible del administrador. |

## Actores y flujos

| Actor | Puede | No puede |
|---|---|---|
| **Invitado** | Ver catálogo, precios y detalle de producto | Carrito, compra y consultas (lo manda a `/login` con `redirect_to`) |
| **Comprador registrado** | Carrito, checkout, historial de pedidos, consultas | Panel de administración (403) |
| **Administrador** | Productos y variantes, stock, pedidos, consultas y reportes | Comprar: carrito y checkout rechazan su rol (D-050) |

Flujo de compra: catálogo (`/`) → detalle (`/producto/[id]`) → carrito (`/carrito`) → checkout
(`/checkout`, datos de entrega) → pedido creado con el stock descontado → seguimiento en
`/mis-pedidos`. El administrador cambia el estado del pedido desde `/admin/pedidos`.

## Estructura

```
model/ → repository/ → service/ → state/ → pages/
```

- `model/`: modelos SQLModel, sin lógica.
- `repository/`: consultas; no conoce HTTP ni UI.
- `service/`: validación y reglas de negocio.
- `state/`: estado de Reflex; no abre sesiones de base de datos.
- `pages/`: composición visual; no accede a la base de datos.

## Calidad y controles locales

El proyecto usa **ruff** para lint y formato, y **pytest** contra `zapateria_test` (D-036, D-037).

```powershell
.\.venv\Scripts\ruff.exe check .            # lint
.\.venv\Scripts\ruff.exe format --check .   # formato
.\.venv\Scripts\python.exe -m pytest        # tests
```

**Pre-commit** (opcional pero recomendado) corre esos controles antes de commitear:

```powershell
.\.venv\Scripts\pre-commit.exe install --hook-type pre-commit --hook-type pre-push
.\.venv\Scripts\pre-commit.exe run --all-files
```

- `ruff check --fix` y `ruff format` corren en cada commit.
- `pytest` corre antes de cada push.
- No hay CI remoto ni GitHub Actions: los controles viven en la máquina (D-037).

## Documentación del proyecto

| Documento | Contenido |
|---|---|
| `AGENTS.md` | contrato de trabajo para agentes: reglas, comandos y trampas |
| `docs/HANDOFF.md` | estado verificado y roadmap por fases |
| `docs/backlog/README.md` | índice de tareas, estados y Definition of Done |
| `docs/backlog/DECISIONS.md` | decisiones cerradas (D-001 en adelante) |
| `docs/design.md` | sistema de diseño obligatorio para la UI |

## Problemas comunes

| Síntoma | Causa probable | Solución |
|---|---|---|
| El backend muere con `TypeError: 'module' object is not callable` en `@rx.event` | Se lanzó el `reflex` global en vez del del venv y tomó otro `granian` | Activá `.venv` (`\.venv\Scripts\Activate.ps1`) o usá `.\run.ps1` |
| `RuntimeError: DATABASE_URL is not set` | Falta `.env` o la variable está vacía | `Copy-Item .env.example .env` y completá `DATABASE_URL` |
| `alembic upgrade head` falla con `Unknown database` | La base no existe | Creala en MySQL 8 (`CREATE DATABASE zapateria_db CHARACTER SET utf8mb4`) y reintentá |
| El catálogo aparece vacío | La base no tiene productos | Corré `python seed.py` o cargá productos desde `/admin/productos` |
| `reflex run --env prod` aborta con `Detected database schema changes` | La DB tiene tablas o columnas fuera de los modelos | `alembic upgrade head` y `alembic check` para ver el drift |
| `Address already in use` en `3000`/`8000` | Quedó un proceso anterior | Cerrá el proceso o usá `.\run.ps1 -Port 3001` |
| El login falla con error de acceso a MySQL | Credenciales o usuario sin permisos sobre la base | Revisá `DATABASE_URL` y los `GRANT` del usuario |

