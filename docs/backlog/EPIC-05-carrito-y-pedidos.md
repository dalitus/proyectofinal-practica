# EPIC 05 — Carrito y pedidos

**Objetivo:** que el comprador agregue productos sin errores, vea totales correctos y pueda
completar un pedido con stock consistente.

---

## T-040 · Estado único de carrito y vars inexistentes

- **Estado:** hecha · **Prioridad:** P1 · **Épica:** 05
- **Archivos:** `app/state/carrito_estado.py`, `app/pages/carrito_pagina.py`,
  `app/service/carrito_servicio.py`, `app/repository/carrito_repositorio.py`,
  `app/service/sesion_servicio.py`, `tests/test_carrito_servicio.py`
- **Problema:** hay tres implementaciones de carrito; `CarritoState` usa `error_message` y
  `success_message` que no declara (AttributeError al agregar/eliminar). La agrupación de productos
  se calcula de dos formas distintas.
- **Decisión (D-002/D-008/D-022):** carrito solo en DB por usuario; sin carrito de invitado; tope
  únicamente por stock.
- **Qué se hizo (2026-10-30):**
  - Un solo `CarritoEstado` (async) con vars declarados y `on_load`: carga el carrito del comprador
    o manda al login. La identidad se resuelve con `sesion_servicio.usuario_autenticado(token)`
    contra `localauthsession`; el id nunca viaja como var del cliente.
  - `carrito_servicio` calcula totales, subtotales y validación de stock una sola vez; el
    repositorio hace SQL y no conoce HTTP ni UI (D-033, T-062).
  - Página `/carrito` con `CartLine`, stepper (tope = stock), quitar, vaciar con `ConfirmDialog`,
    `OrderSummary` sticky, skeleton, error con “Reintentar” y vacío con CTA al catálogo.
  - El ítem apunta a la variante `(producto, color, talle)` y el detalle pasa `variante_id`.
  - Verificado en el navegador: agregar (2 veces suma), sumar/restar, quitar, vaciar y total
    `$ 179.998,00` con 2 unidades; `test_carrito_servicio.py` (9 tests).
- **AC propuestos:**
  - [x] Un solo `CartState` (o `CarritoState`) con vars declarados.
  - [x] Agregar, sumar cantidad, quitar uno y vaciar funcionan sin excepciones.
  - [x] El ítem del carrito referencia una variante `(producto, color, talle)` (D-009).
  - [x] Totales y subtotales calculados en un único lugar.
  - [x] El carrito se recarga al iniciar sesión y se limpia al cerrar sesión.
  - [x] `AppState`/`GlobalState` eliminados (ver T-060).
  - [x] No hay tope de unidades distinto del stock disponible.
- **Grill / preguntas abiertas:**
  - Ninguna: cerrado en D-002, D-008 y D-022.
- **Depende de:** T-020, T-010

---

## T-041 · Política de invitados vs logueados en carrito

- **Estado:** hecha · **Prioridad:** P1 · **Épica:** 05
- **Archivos:** `app/state/carrito_estado.py`, `app/state/checkout_estado.py`,
  `app/pages/producto_pagina.py`, `app/state/login_estado.py`
- **Problema:** se puede ver el catálogo sin login, pero agregar al carrito exige sesión y el
  mensaje aparece sin redirección. No está definido qué puede hacer un invitado.
- **Decisión (D-002):** invitado solo lectura; carrito y compra requieren login; sin carrito local.
- **Qué se hizo (2026-10-30):** el invitado que agrega al carrito o abre `/checkout` va a
  `/login?next=<ruta>`; `LoginEstado` ya validaba rutas internas y vuelve al origen. Verificado en
  el navegador: `/checkout` sin sesión termina en `/login?next=/checkout`.
- **AC propuestos:**
  - [x] Política de invitado definida y documentada en `DECISIONS.md`.
  - [x] El invitado puede ver catálogo, precios finales y detalle.
  - [x] Al intentar comprar sin sesión, se redirige al login y se vuelve al punto de origen.
  - [x] No se pierde el carrito al loguearse porque no existe carrito de invitado.
- **Grill / preguntas abiertas:**
  - Ninguna: cerrado en D-002.
- **Depende de:** T-020, T-021

---

## T-042 · Validación y descuento de stock

- **Estado:** hecha · **Prioridad:** P1 · **Épica:** 05
- **Archivos:** `app/service/carrito_servicio.py`, `app/repository/pedido_repositorio.py`,
  `app/service/pedido_servicio.py`, `tests/test_carrito_servicio.py`,
  `tests/test_pedido_servicio.py`
- **Problema:** se puede agregar cualquier cantidad sin mirar stock; al confirmar el pedido no se
  descuenta stock. Dos compradores pueden comprar la última unidad.
- **Decisión (D-004/D-010):** validar al agregar y al confirmar; descontar en transacción; sin
  reservas; al cancelar un pedido se repone el stock de todas sus variantes.
- **Qué se hizo (2026-10-30):** al agregar se valida el stock contando lo que ya está en el carrito
  (D-022); al confirmar, el repositorio bloquea las variantes con `FOR UPDATE`, revalida, descuenta
  y crea pedido + items + vacía el carrito en una sola transacción. Si falta stock no se escribe
  nada y el mensaje nombra producto, color, talle y unidades restantes. Los tests cubren carrito
  vacío, stock insuficiente (rollback sin pedido ni descuento) y producto desactivado.
- **AC propuestos:**
  - [x] No se puede agregar/superar la cantidad disponible.
  - [x] Al confirmar el pedido se revalida y descuenta stock de forma atómica.
  - [x] Si falta stock, el pedido no se crea y se informa qué producto falló.
  - [x] El stock se controla por la variante `(producto, color, talle)` (D-009).
  - [x] Cancelar un pedido repone stock en la misma transacción (D-010).
        → `_reponer_stock` en `pedido_repositorio` suma las líneas de `PedidoItem`
        y bloquea las variantes en orden de `id_stock`; cubierto por
        `test_cancelar_repone_stock_y_registra_fecha` y
        `test_cancelar_repone_solo_las_variantes_del_pedido`.
- **Grill / preguntas abiertas:**
  - Ninguna: cerrado en D-004 y D-010.
- **Depende de:** T-040, T-012

---

## T-043 · Checkout: datos de entrega y creación de pedido

- **Estado:** hecha · **Prioridad:** P1 · **Épica:** 05
- **Archivos:** `app/state/checkout_estado.py`, `app/pages/checkout_pagina.py`,
  `app/service/pedido_servicio.py`, `app/repository/pedido_repositorio.py`,
  `tests/test_pedido_servicio.py`
- **Problema:** el modal pide dirección, número, ciudad, provincia, talles y colores; la validación
  es parcial (solo exige dirección/ciudad/provincia) y el pedido se crea con datos que pueden venir
  vacíos. No hay costo de envío ni método de pago.
- **Decisión (D-005/D-032):** solo se registra el pedido; sin pago online; checkout en página
  `/checkout`, no en modal; envío a coordinar sin costo en la app.
- **Qué se hizo (2026-10-30):**
  - `CheckoutEstado` carga el carrito, exige sesión y redirige a `/carrito` si está vacío. El
    formulario es controlado y muestra error por campo (dirección, número, ciudad y provincia
    obligatorios; departamento y código postal opcionales).
  - `pedido_servicio.confirmar_pedido` recalcula el total desde el carrito y crea el pedido con
    snapshot en `PedidoItem`; el repositorio hace todo en una transacción con `FOR UPDATE`.
  - Página `/checkout` con `AddressForm` + `OrderSummary` sticky y vista de confirmación con número
    de pedido, total y dirección. No hay CTA a rutas inexistentes.
  - Verificado en el navegador: carrito → checkout → error por campo vacío → confirmar → “Pedido #1”,
    total `$ 89.999,00`, stock Blanco 42 de 3 a 2 y carrito vacío.
  - `tests/test_pedido_servicio.py` (7 tests) cubre snapshot, total, vaciado, rollback por stock,
    producto desactivado y validación de entrega.
- **AC propuestos:**
  - [x] Campos obligatorios definidos y validados en servidor.
  - [x] El pedido guarda un snapshot de productos, variante (color/talle) y precios en `PedidoItem` (D-029).
  - [x] El total se recalcula en servidor y coincide con el carrito.
  - [x] El checkout es una página `/checkout` con `AddressForm` + `OrderSummary` (D-032).
  - [x] Carrito vacío no permite confirmar y redirige a `/carrito`.
  - [x] Confirmación visible con número de pedido.
  - [x] No se pide ni se guarda información de tarjeta.
  - [x] El total no incluye envío; se muestra “envío a coordinar”.
  - [x] Talles/colores no se piden como texto: se eligen como variante (D-009).
- **Grill / preguntas abiertas:**
  - Ninguna: cerrado en D-005 y D-009.
- **Depende de:** T-040, T-042, T-014

---

## T-044 · Ciclo de vida y estados del pedido

- **Estado:** hecha · **Prioridad:** P1 · **Épica:** 05
- **Archivos:** `app/service/pedido_servicio.py`, `app/repository/pedido_repositorio.py`,
  `app/model/pedido_model.py`, `alembic/versions/8d2f4c1a7b90_add_fecha_cancelacion.py`,
  `tests/test_pedido_estado.py`
- **Problema:** los estados están hardcodeados (“en espera”, “enviado”, “entregado”) y el admin
  puede cambiarlos sin transiciones válidas ni confirmación. No hay cancelación ni fecha de entrega.
- **Decisión (D-010):** solo el admin cancela; el usuario no. Cancelar repone stock.
- **Qué se hizo (2026-10-30):**
  - `ESTADOS_DE_PEDIDO` y `TRANSICIONES` en `pedido_servicio`: en espera → enviado o cancelado;
    enviado → entregado/cancelado; entregado y cancelado son finales. El repositorio no conoce
    estados: recibe el esperado, el nuevo y si hay que reponer.
  - `cambiar_estado` y `cancelar_pedido` validan el destino, explican el rechazo con los dos
    estados (“No se puede pasar de 'en espera' a 'entregado'”) y distinguen pedido inexistente.
  - El repositorio bloquea la fila del pedido con `FOR UPDATE` y revalida `estado_esperado`: si otro
    admin cambió el pedido primero, `EstadoCambiado` corta la operación sin escribir. Repetir
    “cancelar” no repone stock dos veces.
  - Cancelar repone cada variante leyendo `PedidoItem` y bloqueando las filas en orden de
    `id_stock` (mismo orden que `crear_pedido`, sin deadlocks) dentro de la misma transacción.
  - `fecha_entrega` se llena al entregar y `fecha_cancelacion` al cancelar (columna nueva, migración
    `8d2f4c1a7b90`, aplicada en la base de desarrollo).
  - `tests/test_pedido_estado.py` (11 tests): transiciones válidas, fecha de entrega, cancelación
    desde en espera y desde enviado con reposición, doble cancelación, entregado no cancela, salto
    inválido, estado desconocido, pedido inexistente, dos pedidos sobre la misma variante y la
    guarda de `estado_esperado`.
- **AC propuestos:**
  - [x] Estados y transiciones definidos: en espera → enviado → entregado; en espera/enviado → cancelado.
  - [x] Solo el admin cambia estado o cancela; el usuario solo consulta.
        → el comprador no tiene ninguna acción de estado; hoy tampoco hay ruta de admin (T-023/T-051).
  - [x] Transiciones inválidas se rechazan con mensaje.
        → `ErrorDePedido` con los dos estados nombrados; cubierto por
        `test_en_espera_no_puede_saltar_a_entregado` y `test_entregado_no_se_puede_cancelar`.
  - [x] Se registra `fecha_entrega` y fecha/historial de cancelación.
        → `fecha_entrega` y `fecha_cancelacion`; el historial completo de cambios llega con la
        auditoría de T-053 (D-031), fuera de esta versión.
  - [x] Cancelar repone el stock de todas las variantes en una transacción, leyendo `PedidoItem`.
  - [x] El filtro del admin usa los mismos estados.
        → `pedido_servicio.opciones_de_estado()` se arma desde `ESTADOS_DE_PEDIDO` y
        `normalizar_filtro` descarta los desconocidos; `test_el_filtro_usa_los_estados_del_ciclo_de_vida`
        falla si alguien agrega un estado en un solo lado. La pantalla que lo muestra es T-051.
- **Grill / preguntas abiertas:**
  - Notificaciones al cambiar estado: fuera de esta versión (si se necesitan, T-064).
- **Depende de:** T-043
- **Nota:** el botón de cambiar estado y la guarda de rol llegaron con T-051 y T-023; acá queda el
  ciclo de vida y sus datos.

---

## T-045 · Eliminar consulta automática al comprar

- **Estado:** hecha · **Prioridad:** P2 · **Épica:** 05
- **Archivos:** `app/service/pedido_servicio.py`, `app/repository/pedido_repositorio.py`,
  `alembic/versions/b3c9e2d5a1f7_clean_compra_realizada_consultas.py`,
  `tests/test_pedido_servicio.py`
- **Problema:** cada compra crea una “Consulta” con asunto “Compra realizada” que luego se oculta
  en las pantallas de consultas. Duplica información y ensucia la tabla.
- **Decisión (D-006):** eliminar la consulta automática; el pedido es la fuente de verdad.
- **Qué se hizo (2026-10-30):**
  - La creación del pedido (`confirmar_pedido` + `crear_pedido`) solo escribe `Pedido`,
    `PedidoItem`, stock y carrito: no toca `consultas`. `test_confirmar_no_crea_consulta_automatica`
    lo fija para que no vuelva.
  - No quedan filtros ni ramas de “Compra realizada” en el código: el panel de consultas viejo se
    borró con T-060 y la versión nueva (T-052) todavía no existe.
  - Migración `b3c9e2d5a1f7`: copia las consultas históricas con asunto “Compra realizada” a
    `consultas_compra_backup` y después las borra. El backup es una tabla plana (sin FK) para que
    el `downgrade` pueda reponerlas aunque el usuario se haya borrado. Probada en desarrollo:
    subir deja el backup con 1 fila y `consultas` con la consulta real; bajar repone la fila y
    borra el backup.
- **AC propuestos:**
  - [x] La compra no crea consultas.
  - [x] El pedido es la única fuente de verdad de la compra.
  - [x] Se eliminan los filtros especiales de “Compra realizada”.
  - [x] Migración de limpieza de consultas históricas de ese asunto (con backup).
- **Grill / preguntas abiertas:**
  - Ninguna: cerrado en D-006.
- **Depende de:** T-043

---

## T-076 · Historial de pedidos del comprador

- **Estado:** hecha · **Prioridad:** P1 · **Épica:** 05
- **Archivos:** `app/repository/pedido_repositorio.py`, `app/service/pedido_servicio.py`,
  `app/state/comprador_estado.py`, `app/state/mis_pedidos_estado.py`,
  `app/pages/mis_pedidos_pagina.py`, `app/pages/mi_pedido_pagina.py`,
  `app/pages/cuenta_menu.py`, `tests/test_mis_pedidos_servicio.py`
- **Problema:** el actor comprador tiene que “ver sus pedidos” (README, D-002) y el admin sí tenía
  su panel, pero el comprador no tenía ninguna pantalla: compraba y el pedido desaparecía de su
  vista. El backlog no tenía la tarea; se creó acá.
- **Decisión (D-002, D-030):** el comprador consulta sus pedidos con login obligatorio, solo los
  propios y sin acciones de escritura (el ciclo de vida lo mueve el admin, T-044).
- **Qué se hizo (2026-11-03):**
  - `/pedidos`: tabla paginada a 10 con número, fecha, estado, unidades y total; el badge usa los
    mismos estados del ciclo de vida (T-044). Vacío, carga (`Skeleton`) y error propios.
  - `/pedidos/[pedido_id]`: datos del pedido, dirección de entrega, líneas con snapshot de color,
    talle, precio y subtotal, y el total. Un pedido ajeno o inexistente muestra “no existe”, no un
    error de permisos: así no se confirman ids de otras cuentas.
  - El `usuario_id` sale de `sesion_servicio.usuario_con_rol(token)`; el filtro por dueño está en
    SQL (`WHERE usuario_id = :id`), no en la página. La pantalla no manda ids desde el cliente.
  - `CompradorEstado` es la base compartida con `MisConsultasEstado`: guarda de sesión y redirect a
    `/login?next=...` en un solo lugar (T-065).
  - El header muestra “Mis pedidos” y “Mis consultas” a los compradores; el admin sigue viendo
    “Panel”.
  - `_detalle_de` se extrajo de `obtener_detalle` para que admin y comprador pinten el mismo
    detalle desde una sola implementación.
- **AC propuestos:**
  - [x] Un comprador logueado ve su historial de pedidos.
        → `/pedidos` con tabla paginada; verificado en el navegador con una sesión de comprador.
  - [x] Solo ve sus propios pedidos: un id ajeno no es legible.
        → filtro por dueño en SQL; `obtener_mi_pedido` trata el id ajeno como inexistente;
        `test_detalle_de_otro_usuario_es_inexistente` en verde.
  - [x] El invitado va al login y vuelve a `/pedidos`.
        → `CompradorEstado` redirige a `/login?next=/pedidos`; verificado como visitante.
  - [x] El detalle muestra líneas, entrega y total con el mismo formato de precio.
        → `_detalle_de` + `formatear_precio` (T-032); `test_detalle_trae_lineas_y_envio` en verde.
  - [x] Estados vacío, carga y error en las dos pantallas.
        → `EmptyState`, `Skeleton` y `Alert` + reintento.
- **Grill / preguntas abiertas:**
  - Ninguna: cerrado en D-002 y D-030 (sin correo; se lee en la web).
- **Depende de:** T-043, T-044, T-065

