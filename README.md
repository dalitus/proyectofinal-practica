# Tienda online de indumentaria y calzado

Aplicación web de venta de indumentaria y calzado hecha con **Reflex + MySQL**.
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

## Estructura

```
model/ → repository/ → service/ → state/ → pages/
```

- `model/`: modelos SQLModel, sin lógica.
- `repository/`: consultas; no conoce HTTP ni UI.
- `service/`: validación y reglas de negocio.
- `state/`: estado de Reflex; no abre sesiones de base de datos.
- `pages/`: composición visual; no accede a la base de datos.

## Documentación del proyecto

| Documento | Contenido |
|---|---|
| `AGENTS.md` | contrato de trabajo para agentes: reglas, comandos y trampas |
| `docs/HANDOFF.md` | estado verificado y roadmap por fases |
| `docs/backlog/README.md` | índice de tareas, estados y Definition of Done |
| `docs/backlog/DECISIONS.md` | decisiones cerradas (D-001 en adelante) |
| `docs/design.md` | sistema de diseño obligatorio para la UI |
