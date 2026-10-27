# EPIC 05 — Carrito y pedidos

**Objetivo:** que el comprador agregue productos sin errores, vea totales correctos y pueda
completar un pedido con stock consistente.

---

## T-040 · Estado único de carrito y vars inexistentes

- **Estado:** lista · **Prioridad:** P1 · **Épica:** 05
- **Archivos:** `state/carrito_state.py:17-218`, `state/global_state.py`, `state/app_state.py`,
  `pages/carrito_page.py`
- **Problema:** hay tres implementaciones de carrito; `CarritoState` usa `error_message` y
  `success_message` que no declara (AttributeError al agregar/eliminar). La agrupación de productos
  se calcula de dos formas distintas.
- **Decisión (D-002/D-008/D-022):** carrito solo en DB por usuario; sin carrito de invitado; tope
  únicamente por stock.
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
- **Depende de:** T-020, T-010

---

## T-041 · Política de invitados vs logueados en carrito

- **Estado:** lista · **Prioridad:** P1 · **Épica:** 05
- **Archivos:** `pages/catalogo_page.py:15-44`, `state/catalogo_state.py:54-75`,
  `state/carrito_state.py:61-68`
- **Problema:** se puede ver el catálogo sin login, pero agregar al carrito exige sesión y el
  mensaje aparece sin redirección. No está definido qué puede hacer un invitado.
- **Decisión (D-002):** invitado solo lectura; carrito y compra requieren login; sin carrito local.
- **AC propuestos:**
  - [x] Política de invitado definida y documentada en `DECISIONS.md`.
  - [x] El invitado puede ver catálogo, precios finales y detalle.
  - [ ] Al intentar comprar sin sesión, se redirige al login y se vuelve al punto de origen.
  - [x] No se pierde el carrito al loguearse porque no existe carrito de invitado.
- **Grill / preguntas abiertas:**
  - Ninguna: cerrado en D-002.
- **Depende de:** T-020, T-021

---

## T-042 · Validación y descuento de stock

- **Estado:** lista · **Prioridad:** P1 · **Épica:** 05
- **Archivos:** `state/carrito_state.py:86-148`, `service/pedido_service.py:35-84`,
  `repository/carrito_repository.py:49-65`
- **Problema:** se puede agregar cualquier cantidad sin mirar stock; al confirmar el pedido no se
  descuenta stock. Dos compradores pueden comprar la última unidad.
- **Decisión (D-004/D-010):** validar al agregar y al confirmar; descontar en transacción; sin
  reservas; al cancelar un pedido se repone el stock de todas sus variantes.
- **AC propuestos:**
  - [x] No se puede agregar/superar la cantidad disponible.
  - [x] Al confirmar el pedido se revalida y descuenta stock de forma atómica.
  - [x] Si falta stock, el pedido no se crea y se informa qué producto falló.
  - [x] El stock se controla por la variante `(producto, color, talle)` (D-009).
  - [x] Cancelar un pedido repone stock en la misma transacción (D-010).
- **Grill / preguntas abiertas:**
  - Ninguna: cerrado en D-004 y D-010.
- **Depende de:** T-040, T-012

---

## T-043 · Checkout: datos de entrega y creación de pedido

- **Estado:** lista · **Prioridad:** P1 · **Épica:** 05
- **Archivos:** `state/carrito_state.py:86-148`, `pages/carrito_page.py:39-146`,
  `service/pedido_service.py:35-84`
- **Problema:** el modal pide dirección, número, ciudad, provincia, talles y colores; la validación
  es parcial (solo exige dirección/ciudad/provincia) y el pedido se crea con datos que pueden venir
  vacíos. No hay costo de envío ni método de pago.
- **Decisión (D-005/D-032):** solo se registra el pedido; sin pago online; checkout en página
  `/checkout`, no en modal; envío a coordinar sin costo en la app.
- **AC propuestos:**
  - [x] Campos obligatorios definidos y validados en servidor.
  - [x] El pedido guarda un snapshot de productos, variante (color/talle) y precios en `PedidoItem` (D-029).
  - [x] El total se recalcula en servidor y coincide con el carrito.
  - [x] El checkout es una página `/checkout` con `AddressForm` + `OrderSummary` (D-032).
  - [x] Carrito vacío no permite confirmar y redirige a `/carrito`.
  - [ ] Confirmación visible con número de pedido.
  - [x] No se pide ni se guarda información de tarjeta.
  - [x] El total no incluye envío; se muestra “envío a coordinar”.
  - [x] Talles/colores no se piden como texto: se eligen como variante (D-009).
- **Grill / preguntas abiertas:**
  - Ninguna: cerrado en D-005 y D-009.
- **Depende de:** T-040, T-042, T-014

---

## T-044 · Ciclo de vida y estados del pedido

- **Estado:** lista · **Prioridad:** P1 · **Épica:** 05
- **Archivos:** `service/pedido_service.py:192-208`, `pages/pedidos_admin_page.py:69-126`,
  `pages/pedidos_page.py:21-30`
- **Problema:** los estados están hardcodeados (“en espera”, “enviado”, “entregado”) y el admin
  puede cambiarlos sin transiciones válidas ni confirmación. No hay cancelación ni fecha de entrega.
- **Decisión (D-010):** solo el admin cancela; el usuario no. Cancelar repone stock.
- **AC propuestos:**
  - [x] Estados y transiciones definidos: en espera → enviado → entregado; en espera/enviado → cancelado.
  - [x] Solo el admin cambia estado o cancela; el usuario solo consulta.
  - [ ] Transiciones inválidas se rechazan con mensaje.
  - [ ] Se registra `fecha_entrega` y fecha/historial de cancelación.
  - [ ] Cancelar repone el stock de todas las variantes en una transacción, leyendo `PedidoItem`.
  - [ ] El filtro del admin usa los mismos estados.
- **Grill / preguntas abiertas:**
  - Notificaciones al cambiar estado: fuera de esta versión (si se necesitan, T-064).
- **Depende de:** T-043

---

## T-045 · Eliminar consulta automática al comprar

- **Estado:** lista · **Prioridad:** P2 · **Épica:** 05
- **Archivos:** `state/carrito_state.py:103-114`, `pages/consulta_admin_page.py:77-79`,
  `pages/consulta_usuario_page.py:112-114`
- **Problema:** cada compra crea una “Consulta” con asunto “Compra realizada” que luego se oculta
  en las pantallas de consultas. Duplica información y ensucia la tabla.
- **Decisión (D-006):** eliminar la consulta automática; el pedido es la fuente de verdad.
- **AC propuestos:**
  - [x] La compra no crea consultas.
  - [x] El pedido es la única fuente de verdad de la compra.
  - [x] Se eliminan los filtros especiales de “Compra realizada”.
  - [x] Migración de limpieza de consultas históricas de ese asunto (con backup).
- **Grill / preguntas abiertas:**
  - Ninguna: cerrado en D-006.
- **Depende de:** T-043
