# EPIC 02 — Modelo de datos y contratos

**Objetivo:** que modelos, servicios, estados y páginas hablen el mismo idioma y que la base de
datos garantice integridad.

---

## T-010 · Normalización de claves (`id`, `usuario_id`, `producto_id`)

- **Estado:** hecha · **Prioridad:** P0 · **Épica:** 02
- **Archivos:** `app/model/*`, `repository/`, `service/`, `state/`
- **Problema:** el código usa `Users.id_users`, `Pedido.id_usuario`, `Producto.id_producto` y
  `Users.es_admin`, pero los modelos definen `id`, `usuario_id`, `id` y no tienen `es_admin`.
  Esto produce `AttributeError` / `ValidationError` en login, pedidos y detalle.
- **Decisión (D-019):** identidad en `LocalUser` + `UserProfile`; el resto de tablas referencia
  `usuario_id` → `local_user.id`.
- **AC propuestos:**
  - [x] Convención única: `LocalUser.id`, `UserProfile.local_user_id`, `Pedido.usuario_id`,
    `Producto.id`, `Carrito.usuario_id/variante_id`.
  - [x] `rg "id_users|id_usuario|id_producto|es_admin"` no devuelve usos de modelo/servicio.
  - [x] Login, alta de pedido, detalle y carrito funcionan de punta a punta.
  - [x] No hay migración de datos: la DB se recrea (D-012).
  - [x] El carrito referencia `variante_id`/`stock_id` y el pedido guarda color/talle (D-009).
- **Grill / preguntas abiertas:**
  - Ninguna: cerrado en D-009 y D-019.
- **Verificación (2026-11-02):**
  - Se verificó con una búsqueda exacta sobre `app/` y `tests/`: no quedan referencias heredadas a
    `id_users`, `id_usuario`, `id_producto`, `Users`, `Gerente`, `producto_model_pydantic` ni `rx.Model`.
  - La suite actual y el compile siguen pasando; la convención final quedó aplicada en los modelos,
    servicios y estados activos.
- **Depende de:** T-003

---

## T-011 · Identidad y rol del administrador

- **Estado:** hecha · **Prioridad:** P0 · **Épica:** 02
- **Archivos:** `model/gerente_model.py`, `model/users_model.py`, `service/gerente_service.py`,
  `pages/andmin_page.py`, `state/users_state.py:64-73`
- **Problema:** hoy el admin se valida contra `Gerente`, pero también se intenta usar
  `Users.es_admin`. Hay un solo admin por defecto según el negocio, pero el modelo permite N.
- **Decisión (D-019):** toda la identidad vive en `LocalUser` + `UserProfile`; el admin se marca
  con `UserProfile.is_admin`. Se eliminan `users` y `gerentes`.
- **AC propuestos:**
  - [x] Una única fuente de identidad: `LocalUser` (credenciales) + `UserProfile` (perfil/rol).
  - [x] El admin no se registra desde el formulario público; se crea por seed (D-013).
  - [x] Existe un mecanismo de bootstrap/seed para crear el admin inicial (T-024).
  - [x] No se puede eliminar/degradar al último admin.
        → `desactivar_usuario` rechaza con "último administrador";
        `test_ultimo_admin_no_se_puede_desactivar` en verde.
  - [x] El admin no compra: su sesión no muestra carrito ni checkout.
        → `usuario_puede_comprar` bloquea carrito y checkout en el servicio, y la UI esconde el
        CTA y el link del carrito (T-077, D-050); `test_solo_el_comprador_puede_comprar`,
        `test_admin_no_puede_agregar_ni_tocar_el_carrito` y `test_admin_no_puede_confirmar_pedido`.
- **Grill / preguntas abiertas:**
  - Ninguna: cerrado en D-019. Un solo admin por defecto; si se agrega otro, el modelo lo permite.
- **Verificación (2026-11-05):** el rol vive solo en `UserProfile.is_admin`; no quedan `users` ni
  `gerentes` en el esquema (`tests/test_esquema.py` fija las tablas). El seed crea el admin inicial
  (`crear_admin_si_no_existe`) y el alta pública no lo permite.
- **Depende de:** T-010

---

## T-012 · Integridad de datos (FK, cascadas, unique email)

- **Estado:** hecha · **Prioridad:** P1 · **Épica:** 02
- **Archivos:** `model/*`, `service/pedido_service.py`, `pages/adnmin_shouder_page.py:171-188`
- **Problema:** el email del comprador no tenía unicidad garantizada; borrar un producto elimina
  stocks a mano y no contempla carritos/FKs; varias tablas legado no tienen FKs.
- **Decisión (D-028):** borrado lógico de productos (`activo`) y desactivación de usuarios
  (`LocalUser.enabled`); nunca borrado físico.
- **AC propuestos:**
  - [x] `LocalUser.username` y `UserProfile.email` son únicos; el alta devuelve un error claro si
    se repite.
  - [x] Borrar producto no deja huérfanos: se marca `activo = False` y se conservan pedidos.
  - [x] FKs declaradas en los modelos que se usan, incluida `UserProfile.local_user_id`.
  - [x] Tests de integridad para los casos anteriores.
        → `test_email_duplicado_no_deja_restos` (unicidad y alta atómica), `test_variante_es_unica_por_producto_color_y_talle`,
        `test_carrito_exige_usuario_existente` y `test_pedido_guarda_snapshot_de_la_compra`
        (borrado lógico sin huérfanos) en `tests/test_esquema.py` y `tests/test_auth_servicio.py`.
  - [x] Los usuarios se desactivan, no se borran.
- **Grill / preguntas abiertas:**
  - Ninguna: cerrado en D-028.
- **Verificación (2026-11-05):** el borrado de producto es lógico (`activo = False`) y el catálogo lo
  excluye; el pedido conserva su snapshot (`precio_unitario`, `color`, `talle`) aunque el producto
  cambie de precio o se desactive.
- **Depende de:** T-010, T-013

---

## T-013 · Tablas legado `rx.Model` y alcance

- **Estado:** hecha · **Prioridad:** P2 · **Épica:** 02
- **Archivos:** `app/model/`, `repository/`, `service/`, `seed.py`
- **Problema:** conviven modelos `rx.Model` (legado) sin FKs ni uso claro con SQLModel. No está
  claro si envíos, presupuestos y detalles están en el alcance del producto.
- **Decisión (D-029):** se eliminan `detalles`, `envios`, `presupuestos`, `solicitan` y
  `producto_model_pydantic`; las líneas del pedido pasan a `PedidoItem`.
- **AC propuestos:**
  - [x] Decisión documentada: las tablas legado se eliminan.
  - [x] No queda ningún `rx.Model`; todo es SQLModel.
  - [x] Se borran también sus repositorios y referencias.
  - [x] `PedidoItem` reemplaza a `Detalles` y a `Pedido.productos_json`.
- **Grill / preguntas abiertas:**
  - Ninguna: cerrado en D-029.
- **Verificación (2026-11-02):**
  - Se verificó con una búsqueda exacta que no quedan modelos ni clases heredados (`rx.Model`,
    `class Detalle`, `class Envio`, `class Presupuesto`, `class Solicitan`, `producto_model_pydantic`).
  - El esquema activo y la suite restante siguen pasando, por lo que la migración de alcance quedó
    cerrada y consistente con la base final.
- **Depende de:** T-010

---

## T-014 · Contrato de precios (Decimal, moneda, formato)

- **Estado:** hecha · **Prioridad:** P1 · **Épica:** 02
- **Archivos:** `model/product_model.py:15`, `service/catalogo_service.py:15`,
  `state/carrito_state.py:75-84`, `pages/adnmin_shouder_page.py:52-55`
- **Problema:** `precio` es `Decimal`, pero se expone como `float` en algunos estados y como
  `Decimal` en otros; no hay un formato único y el total se calcula en varios lugares.
- **Decisión (D-003):** precio final en ARS, IVA incluido, sin descuentos, `DECIMAL(10,2)`,
  formato es-AR y totales en servidor.
- **AC propuestos:**
  - [x] `precio` se guarda con precisión definida (`DECIMAL(10,2)`) y se serializa de forma consistente.
  - [x] Un único helper de formato (`$ 1.234,56`) y una única moneda (ARS).
  - [x] Los totales se calculan en el servidor, no en la UI.
  - [x] Tests de redondeo y de subtotales.
        → `test_formatear_precio` (redondeo a dos decimales y ceros finales),
        `test_agregar_arma_la_linea_con_precio_y_variante` y
        `test_subtotal_suma_varias_lineas` (subtotal por línea y total del carrito).
- **Grill / preguntas abiertas:**
  - Ninguna: cerrado en D-003.
- **Verificación (2026-11-05):** `formatear_precio` es el único formateador; el carrito y el pedido
  usan `Decimal` y `quantize(CENTAVOS)` en el servicio, y la UI solo pinta el string.
- **Depende de:** T-010
