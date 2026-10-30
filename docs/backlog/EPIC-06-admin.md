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

- **Estado:** en curso · **Prioridad:** P1 · **Épica:** 06
- **Archivos:** `app/repository/pedido_repositorio.py`, `app/service/pedido_servicio.py`,
  `tests/test_pedidos_admin_servicio.py`
- **Problema:** se muestran tarjetas y tabla duplicadas; los botones de estado no piden
  confirmación; no hay paginación; el filtro por producto está declarado pero no se usa.
- **Decisión (D-030):** sin exportación ni borrado; filtros por estado y búsqueda; detalle con
  `PedidoItem`.
- **Qué se hizo (2026-10-30, backend):**
  - `listar_pedidos(estado, busqueda, pagina)` devuelve `PaginaDePedidos` con el cliente, el total
    formateado, las unidades y la etiqueta del estado. Los filtros se aplican en el SQL, no en la
    página, para que el conteo de la paginación vea las mismas filas.
  - La búsqueda cubre nombre, apellido, email, nombre de producto (vía `PedidoItem → Stocks →
    Producto`) y número de pedido si el término es numérico.
  - Unidades por pedido con una subconsulta agregada, sin una consulta por fila.
  - El filtro de estado se arma desde `ESTADOS_DE_PEDIDO` (`opciones_de_estado`) y un estado
    desconocido cae en “todos” en vez de romper un link viejo.
  - `obtener_detalle(pedido_id)` devuelve las líneas con nombre de producto, color, talle,
    cantidad, precio y subtotal (snapshot de D-029), más la dirección armada y el total. Pedido
    inexistente → `ErrorDePedido`.
  - 10 pedidos por página; una página fuera de rango cae en la última.
  - `tests/test_pedidos_admin_servicio.py` (11 tests): listado, filtro válido e inválido, búsqueda
    por cliente/email/producto/número, paginación 13 → 10 + 3, detalle, pedido inexistente, opciones
    de estado y una compra real por carrito + checkout que aparece en el panel.
- **AC propuestos:**
  - [x] Listado con filtros por estado y búsqueda por cliente/producto.
        → `listar_pedidos`; falta la pantalla.
  - [ ] Cambio de estado con confirmación y feedback.
        **Pendiente:** el backend existe (`cambiar_estado`/`cancelar_pedido`, T-044); falta el botón
        con `ConfirmDialog` y el toast en la página.
  - [x] Detalle del pedido con `PedidoItem` (color, talle, cantidad, precio), dirección y total.
        → `obtener_detalle`; falta la pantalla.
  - [x] Paginación o límite si hay muchos pedidos.
        → 10 por página con `PaginaDePedidos.hay_anterior/hay_siguiente`.
  - [ ] Solo admin puede acceder.
        **Bloqueada:** depende de las guardas de rol de T-023.
  - [x] No se borran pedidos ni se exportan.
- **Grill / preguntas abiertas:**
  - Ninguna: cerrado en D-010, D-029 y D-030.
- **Depende de:** T-044, T-023

---

## T-052 · Administración de consultas

- **Estado:** en curso · **Prioridad:** P1 · **Épica:** 06
- **Archivos:** `app/repository/consulta_repositorio.py`, `app/service/consulta_servicio.py`,
  `tests/test_consulta_servicio.py`, `app/model/consulta_model.py`,
  `alembic/versions/c4d8f1a9e2b6_consulta_mensaje_text.py`
- **Problema:** muestra `id_users` cuando el modelo usa `usuario_id` (el ID sale vacío); el filtro
  y la respuesta funcionan, pero no hay paginación ni confirmación de borrado.
- **Decisión (D-030):** respuesta solo en la web; eliminación con confirmación; sin email ni
  archivado.
- **Qué se hizo (2026-10-30, backend):**
  - `consulta_repositorio` lee con dos `aliased(UserProfile)`: quién preguntó y quién respondió, sin
    consultas extra por fila. El predicado pendiente/respondida es uno solo y lo comparten el
    listado y el conteo, así la paginación no puede desalinearse de la tabla.
  - `consulta_servicio` devuelve `PaginaDeConsultas` y `DetalleDeConsulta` con nombre y email del
    comprador, resumen de 140 caracteres, etiqueta de estado y quién respondió.
  - `responder` valida texto no vacío y máximo 2000 caracteres, bloquea la fila con `FOR UPDATE` y
    rechaza sobrescribir una respuesta existente. `eliminar` borra con la misma guarda.
  - `mensaje` y `respuesta` pasan a `TEXT` (D-048, migración `c4d8f1a9e2b6`): con `VARCHAR(255)`
    MySQL cortaba con error 1406 en vez de truncar. Migración probada subir y bajar.
  - `tests/test_consulta_servicio.py` (14 tests): listado, resumen, filtros, filtro inválido,
    paginación 12 → 10 + 2, orden por fecha, respuesta con admin y fecha, respuesta vacía, respuesta
    larga, doble respuesta, consulta inexistente y borrado.
- **AC propuestos:**
  - [x] Se muestra el usuario correcto (`usuario_id` y nombre si aplica).
        → el servicio resuelve nombre y email desde `UserProfile`; falta la pantalla.
  - [ ] Responder y eliminar funcionan con confirmación.
        **Pendiente:** `responder`/`eliminar` están listos; falta el formulario y el `ConfirmDialog`.
  - [x] Filtros pendiente/respondida y orden por fecha.
        → `listar_consultas(filtro=...)`, orden por `fecha_creacion DESC`.
  - [ ] Solo admin puede acceder.
        **Bloqueada:** depende de las guardas de rol de T-023.
  - [x] La respuesta no se envía por email; se muestra en la web.
        → no hay ningún envío de correo en el servicio ni en el repositorio.
- **Grill / preguntas abiertas:**
  - Ninguna: cerrado en D-030.
- **Depende de:** T-023, T-065

---

## T-053 · Operaciones sensibles y auditoría mínima

- **Estado:** en curso · **Prioridad:** P2 · **Épica:** 06
- **Archivos:** `app/service/auditoria.py`, `app/service/pedido_servicio.py`,
  `app/service/consulta_servicio.py`, `tests/test_auditoria.py`
- **Problema:** operaciones destructivas (borrar producto, cambiar estado, borrar consulta) no
  dejan rastro ni tienen protecciones más allá de un diálogo.
- **Decisión (D-031):** logging estructurado por operación sensible; sin tabla de auditoría;
  confirmación en la UI; borrado lógico (D-028).
- **Qué se hizo (2026-10-30, backend):**
  - `app/service/auditoria.py` escribe una línea JSON en el logger `app.auditoria` con
    `fecha`, `admin_id`, `accion`, `entidad`, `entidad_id` y `detalle`. Se llama después de
    confirmada la operación, nunca antes.
  - `cambiar_estado` registra `cambiar_estado` con el detalle `en espera -> enviado`;
    `cancelar_pedido` registra su propia acción `cancelar_pedido` (D-031 las distingue).
  - `responder` y `eliminar` de consultas registran `responder_consulta` y `eliminar_consulta`.
  - `admin_id` es opcional mientras no exista la guarda de rol (T-023): se audita aunque falte el
    autor, con `admin_id: null`.
  - `tests/test_auditoria.py` (6 tests): campos de la línea, acción propia de cancelar, transición
    rechazada sin rastro, respuesta, borrado y operación sin autor.
- **AC propuestos:**
  - [ ] Confirmación explícita en toda operación destructiva.
        **Pendiente:** el `ConfirmDialog` existe (T-063); falta usarlo en las pantallas del admin.
  - [x] Registro estructurado (quién, qué, entidad, cuándo) en el log.
        → línea JSON con los cinco campos; cubierto por `tests/test_auditoria.py`.
  - [ ] Protección del último admin (T-024).
        **Pendiente:** no hay borrado de usuarios todavía (T-024).
  - [ ] Borrado lógico de productos y desactivación de usuarios (D-028).
        **Parcial:** `Producto.activo` existe y el catálogo lo respeta; falta el CRUD (T-050) y la
        baja de usuarios.
- **Grill / preguntas abiertas:**
  - Ninguna: cerrado en D-028, D-031 y D-024.
- **Depende de:** T-012, T-024
