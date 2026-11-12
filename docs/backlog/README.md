# Backlog del proyecto — Tienda

> Última actualización: 2026-11-06
> **Sesión nueva: leer primero `docs/HANDOFF.md`** (estado real verificado + roadmap por fases).
> Origen: scan de código + `compile_log.txt` / `run_log.txt`.
> Este backlog es la fuente de verdad para bugs y refactorizaciones. Cada tarea se cierra con
> criterios de aceptación (AC) verificados y, cuando aplique, tests.

## Actores (cerrado en D-002, D-018, D-019 y D-050)

| Actor | Descripción | Puede |
|---|---|---|
| **Administrador de la tienda** (1 por defecto) | Dueño/gerente del local | Gestionar productos y stock, pedidos, consultas y ver reportes. No compra. |
| **Usuario comprador** | Cliente registrado | Ver catálogo y precios finales, agregar al carrito, comprar, ver sus pedidos y consultas. |
| **Invitado** (D-002) | Visitante sin cuenta | Ver catálogo, precios y detalle. Necesita cuenta para carrito, compra y consultas. |

## Flujo de trabajo

1. `propuesta`: tarea creada con problema y AC preliminares.
2. `en grill`: hacemos preguntas para cerrar ambigüedades. Las respuestas se registran en `DECISIONS.md` y se actualizan los AC.
3. `lista`: AC cerrados, sin preguntas abiertas, dependencias resueltas.
4. `en curso`: alguien la está implementando.
5. `bloqueada`: falta una decisión o una tarea previa.
6. `hecha`: AC marcados + verificación (manual o test) + sin regresiones.

**Regla:** no se implementa una tarea con preguntas abiertas o AC sin confirmar.

## Definition of Done (global)

- [ ] Los AC de la tarea están marcados.
- [ ] `reflex compile` (o `reflex run`) pasa sin warnings nuevos.
- [ ] No se agregaron `print()` ni secretos.
- [ ] Se actualizó `DECISIONS.md` si hubo una decisión de producto/técnica.
- [ ] Se verificó el flujo afectado en dev (y en prod si toca arranque/config).
- [ ] Si toca datos: migración de Alembic incluida y probada en una DB limpia.

## Índice

| ID | Título | Épica | Prioridad | Estado |
|---|---|---|---|---|
| T-001 | La app no arranca en producción (`@rx.event`) | 01 Arranque | P0 | hecha |
| T-002 | Configuración única de base de datos y engine | 01 Arranque | P0 | hecha |
| T-003 | Migraciones Alembic (head roto, credenciales) | 01 Arranque | P0 | hecha |
| T-004 | Dependencias reproducibles y versiones | 01 Arranque | P0 | hecha |
| T-005 | Limpieza de archivos muertos y scripts sueltos | 01 Arranque | P1 | hecha |
| T-006 | Plan de migración Reflex 0.8.4 → 0.10.x | 01 Arranque | P0 | hecha |
| T-010 | Normalización de claves (`id`, `usuario_id`, `producto_id`) | 02 Datos | P0 | hecha |
| T-011 | Identidad y rol del administrador | 02 Datos | P0 | hecha |
| T-012 | Integridad de datos (FK, cascadas, unique email) | 02 Datos | P1 | hecha |
| T-013 | Tablas legado `rx.Model` y alcance | 02 Datos | P2 | hecha |
| T-014 | Contrato de precios (Decimal, moneda, formato) | 02 Datos | P1 | hecha |
| T-020 | Reemplazar `app_globals` por `AuthState` por sesión | 03 Sesión | P0 | hecha |
| T-021 | Flujo de login/logout/registro y redirecciones | 03 Sesión | P0 | hecha |
| T-022 | Hash de contraseñas y persistencia de sesión | 03 Sesión | P0 | hecha |
| T-023 | Guardas de rutas por rol | 03 Sesión | P0 | hecha |
| T-024 | Cuenta única de administrador y bootstrap | 03 Sesión | P1 | hecha |
| T-030 | Estado de carga y listado del catálogo | 04 Catálogo | P1 | hecha |
| T-031 | Detalle de producto por URL (refresh-safe) | 04 Catálogo | P1 | hecha |
| T-032 | Precio final y formato en la UI | 04 Catálogo | P1 | hecha |
| T-033 | Visibilidad, filtros y orden del catálogo | 04 Catálogo | P2 | hecha |
| T-034 | Imágenes: placeholder, upload, Drive, create/edit | 04 Catálogo | P1 | hecha |
| T-040 | Estado único de carrito y vars inexistentes | 05 Carrito | P1 | hecha |
| T-041 | Política de invitados vs logueados en carrito | 05 Carrito | P1 | hecha |
| T-042 | Validación y descuento de stock | 05 Carrito | P1 | hecha |
| T-043 | Checkout: datos de entrega y creación de pedido | 05 Carrito | P1 | hecha |
| T-044 | Ciclo de vida y estados del pedido | 05 Carrito | P1 | hecha |
| T-045 | Eliminar consulta automática al comprar | 05 Carrito | P2 | hecha |
| T-076 | Historial de pedidos del comprador | 05 Carrito | P1 | hecha |
| T-077 | Restringir compras al administrador | 05 Carrito | P1 | hecha |
| T-050 | CRUD de productos y variantes (color + talle) | 06 Admin | P1 | hecha |
| T-051 | Administración de pedidos | 06 Admin | P1 | hecha |
| T-052 | Administración de consultas | 06 Admin | P1 | hecha |
| T-053 | Operaciones sensibles y auditoría mínima | 06 Admin | P2 | hecha |
| T-060 | Eliminar estados duplicados y código muerto | 07 Arquitectura | P1 | hecha |
| T-061 | Registro único de rutas y URLs canónicas | 07 Arquitectura | P1 | hecha |
| T-062 | Capa de servicios y event handlers | 07 Arquitectura | P1 | hecha |
| T-063 | Sistema de diseño: tokens, shell y primitivos | 07 Arquitectura | P1 | hecha |
| T-064 | Notificaciones y logging | 07 Arquitectura | P2 | hecha |
| T-065 | Consultas de usuario (login obligatorio) | 07 Arquitectura | P1 | hecha |
| T-070 | Tests de servicios y repositorios | 08 Calidad | P2 | hecha |
| T-071 | Lint, formato, pre-commit y CI | 08 Calidad | P2 | hecha |
| T-072 | Documentación y `.env.example` | 08 Calidad | P2 | hecha |
| T-073 | Revisión de secretos y `.gitignore` | 08 Calidad | P0 | hecha |
| T-074 | Accesibilidad y responsive básico | 08 Calidad | P2 | hecha |
| T-075 | Nombres de archivo: ortografía y función | 07 Arquitectura | P1 | hecha |
| T-078 | Iconos en el header y contador del carrito | 07 Arquitectura | P2 | hecha |

## Archivos del backlog

- `EPIC-01-arranque-y-entorno.md`
- `EPIC-02-datos-y-contratos.md`
- `EPIC-03-actores-y-sesion.md`
- `EPIC-04-catalogo.md`
- `EPIC-05-carrito-y-pedidos.md`
- `EPIC-06-admin.md`
- `EPIC-07-arquitectura-reflex.md`
- `EPIC-08-calidad.md`
- `DECISIONS.md` — decisiones cerradas en cada grill

## Cómo agregar una tarea

Copiar este bloque en la épica correspondiente y sumarla al índice:

```md
## T-XXX · Título corto
- **Estado:** propuesta · **Prioridad:** P0/P1/P2 · **Épica:** NN
- **Archivos:** `ruta:línea`
- **Problema:** qué falla hoy y por qué importa.
- **AC propuestos:**
  - [ ] ...
- **Grill / preguntas abiertas:**
  - ...
- **Depende de:** T-XXX
```
