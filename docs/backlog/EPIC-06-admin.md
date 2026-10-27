# EPIC 06 — Panel de administración

**Objetivo:** que el administrador gestione productos, pedidos y consultas sin errores y sin
poder romper la integridad del negocio.

---

## T-050 · CRUD de productos y variantes (color + talle)

- **Estado:** lista · **Prioridad:** P1 · **Épica:** 06
- **Archivos:** `pages/adnmin_shouder_page.py:14-237,274-493`,
  `service/producto_servicio.py`, `service/servicio_stock.py`
- **Problema:** crear y editar comparten estado de modal (`agregar_color` abre el modal de edición),
  el campo de imagen no coincide (`imagen_url` vs `imagen`), y el borrado de stocks se hace a mano
  fuera de una transacción.
- **Decisión (D-009/D-015/D-023):** variante `(producto, color, talle)`; una imagen local por
  producto; categoría fija + marca libre.
- **AC propuestos:**
  - [x] Modelo de variante `(producto, color, talle)` con cantidad y unique compuesto.
  - [x] `Producto` sin `talle`; la DB se recrea (D-012), no hay migración de datos.
  - [x] El admin crea/edita/elimina variantes y el borrado del producto limpia sus variantes.
  - [x] Carrito y pedido referencian la variante, no solo el producto.
  - [x] El detalle permite elegir color + talle antes de agregar al carrito.
  - [x] Crear y editar son flujos separados y no se pisan.
  - [x] Los campos del formulario coinciden con el modelo.
  - [x] Errores de validación visibles y sin perder lo cargado.
  - [x] Categoría desde tabla `Categoria`; marca como texto libre.
- **Grill / preguntas abiertas:**
  - Ninguna: cerrado en D-009, D-015 y D-023.
- **Depende de:** T-010, T-034

---

## T-051 · Administración de pedidos

- **Estado:** lista · **Prioridad:** P1 · **Épica:** 06
- **Archivos:** `pages/pedidos_admin_page.py:1-194`, `state/pedido_state.py`
- **Problema:** se muestran tarjetas y tabla duplicadas; los botones de estado no piden
  confirmación; no hay paginación; el filtro por producto está declarado pero no se usa.
- **Decisión (D-030):** sin exportación ni borrado; filtros por estado y búsqueda; detalle con
  `PedidoItem`.
- **AC propuestos:**
  - [x] Listado con filtros por estado y búsqueda por cliente/producto.
  - [x] Cambio de estado con confirmación y feedback.
  - [x] Detalle del pedido con `PedidoItem` (color, talle, cantidad, precio), dirección y total.
  - [x] Paginación o límite si hay muchos pedidos.
  - [x] Solo admin puede acceder.
  - [x] No se borran pedidos ni se exportan.
- **Grill / preguntas abiertas:**
  - Ninguna: cerrado en D-010, D-029 y D-030.
- **Depende de:** T-044, T-023

---

## T-052 · Administración de consultas

- **Estado:** lista · **Prioridad:** P1 · **Épica:** 06
- **Archivos:** `pages/consulta_admin_page.py:1-182`, `service/consulta_service.py`,
  `repository/consulta_repocitory.py`
- **Problema:** muestra `id_users` cuando el modelo usa `usuario_id` (el ID sale vacío); el filtro
  y la respuesta funcionan, pero no hay paginación ni confirmación de borrado.
- **Decisión (D-030):** respuesta solo en la web; eliminación con confirmación; sin email ni
  archivado.
- **AC propuestos:**
  - [x] Se muestra el usuario correcto (`usuario_id` y nombre si aplica).
  - [x] Responder y eliminar funcionan con confirmación.
  - [x] Filtros pendiente/respondida y orden por fecha.
  - [x] Solo admin puede acceder.
  - [x] La respuesta no se envía por email; se muestra en la web.
- **Grill / preguntas abiertas:**
  - Ninguna: cerrado en D-030.
- **Depende de:** T-023, T-065

---

## T-053 · Operaciones sensibles y auditoría mínima

- **Estado:** lista · **Prioridad:** P2 · **Épica:** 06
- **Archivos:** `pages/adnmin_shouder_page.py`, `pages/pedidos_admin_page.py`,
  `pages/consulta_admin_page.py`, `service/` (logging)
- **Problema:** operaciones destructivas (borrar producto, cambiar estado, borrar consulta) no
  dejan rastro ni tienen protecciones más allá de un diálogo.
- **Decisión (D-031):** logging estructurado por operación sensible; sin tabla de auditoría;
  confirmación en la UI; borrado lógico (D-028).
- **AC propuestos:**
  - [x] Confirmación explícita en toda operación destructiva.
  - [x] Registro estructurado (quién, qué, entidad, cuándo) en el log.
  - [x] Protección del último admin (T-024).
  - [x] Borrado lógico de productos y desactivación de usuarios (D-028).
- **Grill / preguntas abiertas:**
  - Ninguna: cerrado en D-028, D-031 y D-024.
- **Depende de:** T-012, T-024
