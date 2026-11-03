# EPIC 06 — Panel de administración

**Objetivo:** que el administrador gestione productos, pedidos y consultas sin errores y sin
poder romper la integridad del negocio.

---

## T-050 · CRUD de productos y variantes (color + talle)

- **Estado:** hecha · **Prioridad:** P1 · **Épica:** 06
- **Archivos:** `app/repository/producto_repositorio.py`, `app/service/producto_servicio.py`,
  `app/service/imagen_servicio.py`, `app/state/productos_admin_estado.py`,
  `app/pages/productos_admin_pagina.py`, `app/pages/producto_nuevo_pagina.py`,
  `app/pages/producto_admin_pagina.py`, `tests/test_productos_admin_servicio.py`
- **Problema:** crear y editar compartían estado de modal (`agregar_color` abría el modal de
  edición), el campo de imagen no coincidía (`imagen_url` vs `imagen`), y el borrado de stocks se
  hacía a mano fuera de una transacción. Las páginas viejas se borraron en T-060 y la pantalla se
  rehace sobre la arquitectura actual.
- **Decisión (D-009/D-015/D-023/D-028/D-049):** variante `(producto, color, talle)` editada por
  filas; una imagen local por producto; categoría fija + marca libre; borrado lógico del producto.
- **AC propuestos:**
  - [x] Modelo de variante `(producto, color, talle)` con cantidad y unique compuesto.
  - [x] `Producto` sin `talle`; la DB se recrea (D-012), no hay migración de datos.
  - [x] Carrito y pedido referencian la variante, no solo el producto.
  - [x] El detalle permite elegir color + talle antes de agregar al carrito.
  - [x] Categoría desde tabla `Categoria`; marca como texto libre.
  - [x] El admin crea/edita/elimina variantes por fila, y dar de baja el producto no borra filas.
  - [x] Crear y editar son pantallas separadas y no comparten estado de formulario.
  - [x] Los campos del formulario coinciden con el modelo (precio, categoría, imagen, marca).
  - [x] Errores de validación visibles junto al campo y sin perder lo cargado.
  - [x] La imagen se sube con `rx.upload` y se valida en el servidor (JPG/PNG/WebP, ≤ 2 MB).
  - [x] El producto se desactiva con confirmación y se puede reactivar; ambas operaciones se auditan.
- **Grill / preguntas abiertas:**
  - Ninguna: cerrado en D-009, D-015, D-023, D-028 y D-049.
- **Depende de:** T-010, T-034

---

## T-051 · Administración de pedidos

- **Estado:** hecha · **Prioridad:** P1 · **Épica:** 06
- **Archivos:** `app/repository/pedido_repositorio.py`, `app/service/pedido_servicio.py`,
  `app/state/pedidos_admin_estado.py`, `app/pages/pedidos_admin_pagina.py`,
  `app/pages/pedido_admin_pagina.py`, `tests/test_pedidos_admin_servicio.py`
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
- **Qué se hizo (2026-10-31, pantallas):**
  - `/admin/pedidos`: tabla con cliente y email, estado como `Badge`, unidades, total y "Ver";
    filtro por estado, búsqueda por formulario (no consulta por tecla), paginación al pie, y
    estados vacío / cargando / error con "Reintentar".
  - `/admin/pedidos/[pedido_id]`: datos del cliente y la entrega, líneas con color y talle, total.
    Los botones salen de `estados_siguientes(estado)`: la página no inventa una transición.
  - Cada transición pide `ConfirmDialog`; cancelar avisa que repone stock y queda en rojo. Verificado
    a mano: "Marcar como enviado" con toast `Pedido #1: enviado`, y un pedido cancelado desde la
    pantalla devolvió la unidad al stock (5 → 4 → 5) y dejó la línea de auditoría.
- **AC propuestos:**
  - [x] Listado con filtros por estado y búsqueda por cliente/producto.
        → `listar_pedidos` + `/admin/pedidos`.
  - [x] Cambio de estado con confirmación y feedback.
        → `ConfirmDialog` + `Toast` en el detalle; la acción se revalida contra el rol.
  - [x] Detalle del pedido con `PedidoItem` (color, talle, cantidad, precio), dirección y total.
        → `obtener_detalle` + `/admin/pedidos/[pedido_id]`.
  - [x] Paginación o límite si hay muchos pedidos.
        → 10 por página con `PaginaDePedidos.hay_anterior/hay_siguiente`.
  - [x] Solo admin puede acceder.
        → guarda de `AdminEstado` (T-023); invitado → login, comprador → `/403`.
  - [x] No se borran pedidos ni se exportan.
- **Grill / preguntas abiertas:**
  - Ninguna: cerrado en D-010, D-029 y D-030.
- **Depende de:** T-044, T-023

---

## T-052 · Administración de consultas

- **Estado:** hecha · **Prioridad:** P1 · **Épica:** 06
- **Archivos:** `app/repository/consulta_repositorio.py`, `app/service/consulta_servicio.py`,
  `app/state/consultas_admin_estado.py`, `app/pages/consultas_admin_pagina.py`,
  `app/pages/consulta_admin_pagina.py`, `tests/test_consulta_servicio.py`,
  `app/model/consulta_model.py`, `alembic/versions/c4d8f1a9e2b6_consulta_mensaje_text.py`
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
- **Qué se hizo (2026-10-31, pantallas):**
  - `/admin/consultas`: tabla con asunto, resumen, cliente, fecha, estado y quién respondió;
    filtro pendiente/respondida (y "Todas"), paginación y estados vacío / cargando / error.
  - `/admin/consultas/[consulta_id]`: mensaje completo, respuesta existente con autor y fecha, y el
    formulario con el error del largo al lado del campo (no en un toast). Una consulta respondida
    muestra la respuesta en vez del formulario.
  - Eliminar pide `ConfirmDialog` y vuelve a la bandeja. Verificado a mano: respuesta guardada en
    una consulta de prueba, formulario reemplazado por la respuesta y línea de auditoría
    `responder_consulta`; el borrado dejó la bandeja vacía con su línea `eliminar_consulta`.
- **AC propuestos:**
  - [x] Se muestra el usuario correcto (`usuario_id` y nombre si aplica).
        → el servicio resuelve nombre y email desde `UserProfile`; la tabla y el detalle los pintan.
  - [x] Responder y eliminar funcionan con confirmación.
        → formulario con `max_length` y validación en el servicio; borrado con `ConfirmDialog`.
  - [x] Filtros pendiente/respondida y orden por fecha.
        → `listar_consultas(filtro=...)`, orden por `fecha_creacion DESC`.
  - [x] Solo admin puede acceder.
        → guarda de `AdminEstado` (T-023); invitado → login, comprador → `/403`.
  - [x] La respuesta no se envía por email; se muestra en la web.
        → no hay ningún envío de correo en el servicio ni en el repositorio.
- **Grill / preguntas abiertas:**
  - Ninguna: cerrado en D-030.
- **Depende de:** T-023, T-065

---

## T-053 · Operaciones sensibles y auditoría mínima

- **Estado:** hecha · **Prioridad:** P2 · **Épica:** 06
- **Archivos:** `app/service/auditoria.py`, `app/service/pedido_servicio.py`,
  `app/service/consulta_servicio.py`, `app/service/producto_servicio.py`,
  `tests/test_auditoria.py`, `tests/test_auth_servicio.py`
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
  - `crear_producto`, `actualizar_producto`, `agregar_variante`, `actualizar_variante`,
    `eliminar_variante`, `desactivar_producto` y `reactivar_producto` registran auditoría
    quedando el flujo de productos completo.
- **Qué se hizo (2026-11-02, cierre real):**
  - `desactivar_usuario()` no permite desactivar al último admin activo, protegiendo el
    bootstrap de la tienda.
  - `cambiar_password()` valida la contraseña actual antes de rehashing y actualiza la credencial
    con la nueva contraseña.
  - El archivo `logs/auditoria.log` sigue siendo el destino real, con `configurar_destino()`
    invocado desde `app/app.py` y con idempotencia en el handler.
- **AC propuestos:**
  - [x] Confirmación explícita en toda operación destructiva.
        → `ConfirmDialog` en cancelar pedido, eliminar consulta y cambio de estado.
  - [x] Registro estructurado (quién, qué, entidad, cuándo) en el log.
        → línea JSON con los cinco campos, escrita en `logs/auditoria.log`.
  - [x] Protección del último admin (T-024).
        → `desactivar_usuario()` rechaza la desactivación si ese admin es el último habilitado.
  - [x] Borrado lógico de productos y desactivación de usuarios (D-028).
        → `cambiar_activo()` y `desactivar_usuario()` soportan el flujo real sin romper la regla del negocio.
- **Grill / preguntas abiertas:**
  - Ninguna: cerrado en D-028, D-031 y D-024.
- **Depende de:** T-012, T-024
