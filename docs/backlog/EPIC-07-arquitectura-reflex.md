# EPIC 07 — Arquitectura Reflex y UI

**Objetivo:** que la app tenga una sola fuente de estado, rutas coherentes, capas limpias y una UI
consistente.

---

## T-060 · Eliminar estados duplicados y código muerto

- **Estado:** hecha · **Prioridad:** P1 · **Épica:** 07
- **Archivos:** todo `app/pages/`, `app/state/`, `app/service/`, `app/repository/` previos
- **Problema:** hay estados y páginas sin uso, dos `UbicacionState`, dos servicios de Drive y
  lógica de carrito repetida en tres lugares.
- **Decisión (D-015/D-025):** Drive queda fuera (upload local); ubicación con imagen + link a
  Google Maps; se elimina el código muerto.
- **Qué se hizo (Fase 5):** se borró el árbol completo de `app/pages/` y `app/state/`, y todos los
  `app/service/*` y `app/repository/*` salvo `auth_servicio.py` y `conect_db.py`. Sobreviven los
  modelos finales (`app/model/`), los tokens de diseño (`app/ui/tokens.py`) y el alta de comprador.
  La app vuelve a compilar porque `app/app.py` ya no importa nada eliminado.
- **AC:**
  - [x] No quedan archivos/clases sin referencias.
  - [x] `rg` de los nombres eliminados no devuelve usos.
  - [x] `reflex compile` pasa.
  - [x] `google_drive_service.py` se elimina; solo queda el upload local.
  - [x] La ubicación no embebe mapas ni usa API keys.
  - [ ] Una sola implementación de carrito, login, ubicación y subida de imágenes.
        **Movido:** el login existe (plugin), pero carrito, ubicación y subida todavía no tienen
        código. Se cierran cuando se reimplementen en Fase 6-7 (T-061, T-076, T-077). No se marca
        acá porque marcar un AC de código que no existe es mentir en el tablero.
- **Grill / preguntas abiertas:**
  - Ninguna: cerrado en D-015 y D-025.
- **Depende de:** T-005

---

## T-061 · Registro único de rutas y URLs canónicas

- **Estado:** lista · **Prioridad:** P1 · **Épica:** 07
- **Archivos:** `app/app.py:21-33`, `pages/*.py` (`@rx.page`)
- **Problema:** todas las páginas se registran dos veces (`@rx.page` + `app.add_page`), hay rutas
  duplicadas (`/` vs `/catalogo`, `/user` vs `/users`) y warnings en el compile.
- **Decisión (D-024):** `/` catálogo; `/login` + `/register`; `/producto/[id]`; redirects para
  rutas viejas; registro único con `@rx.page`.
- **AC propuestos:**
  - [x] Un solo mecanismo de registro (`@rx.page`).
  - [x] URLs canónicas definidas y enlaces internos actualizados.
  - [ ] Sin warnings de “Page … is being redefined”.
  - [ ] Ruta inexistente muestra 404 amigable.
  - [ ] `/catalogo`, `/users`, `/user` y `/detalle_producto` redirigen a la URL canónica.
- **Grill / preguntas abiertas:**
  - Ninguna: cerrado en D-024.
- **Depende de:** T-031

---

## T-062 · Capa de servicios y event handlers

- **Estado:** hecha · **Prioridad:** P1 · **Épica:** 07
- **Archivos:** `app/state/*.py`, `app/pages/*.py`, `tests/test_arquitectura.py`
- **Problema:** algunos estados abren `Session(engine)` y llaman repositorios; otros pasan por
  services. Los handlers mezclan validación, acceso a datos y UI.
- **Decisión (D-033):** se mantiene `repository → service → state → pages`; estados sin engine/sesiones;
  handlers finos y síncronos salvo `await` de otro estado; errores al log y mensaje claro.
- **Qué se hizo (2026-10-30):**
  - Los seis estados (`carrito`, `catalogo`, `checkout`, `detalle`, `login`, `registro`) importan
    solo `app.service`; ninguno toca `app.repository`, `sqlmodel` ni abre sesión.
  - `tests/test_arquitectura.py` verifica la regla sobre el AST, no con grep: estados sin
    repositorio ni llamadas a `Session`/`get_session`/`create_engine`, páginas sin acceso a datos,
    sin `print()`, sin `traceback` crudo y sin hex/`box_shadow`/`color_scheme` (T-063, T-064).
  - Un test por estado y por página (`parametrize`), así el que agrega una capa de más sabe cuál
    archivo rompió la regla.
- **AC propuestos:**
  - [x] Los estados no importan `engine` ni abren sesiones.
        → `test_los_estados_no_tocan_la_base`.
  - [x] Toda operación pasa por un service con validación.
        → los estados solo importan `app.service.*`; los services validan y devuelven dataclasses.
  - [x] Handlers finos: llamar al service, actualizar vars, devolver evento/toast.
  - [x] Manejo de errores uniforme (sin `traceback.print_exc()` al usuario).
        → `logger.exception` + mensaje en la UI; `test_sin_print_de_depuracion` y
        `test_sin_traceback_crudo_al_usuario`.
  - [x] `async` solo cuando hace falta `await` de otro estado.
        → solo `carrito_estado` y `checkout_estado` leen el token del estado del plugin.
- **Grill / preguntas abiertas:**
  - Ninguna: cerrado en D-033.
- **Depende de:** T-002, T-020

---

## T-063 · Sistema de diseño: tokens, shell y primitivos

- **Estado:** hecha · **Prioridad:** P1 · **Épica:** 07
- **Archivos:** `docs/design.md` (spec), `app/ui/` (nuevo), `app/app.py`,
  `app/pages/*.py`, `app/pages/ui_helpers.py`
- **Problema:** cada página define su propio fondo, ancho y estilos (`background_color="#ADD8E6"`,
  `min_height="100vh"`, cards de `220px` fijas, `box_shadow` por card). No hay tokens, ni layout
  compartido, ni primitivos: `ui_helpers.py` solo envuelve botones de Radix sin criterio visual. El
  resultado es inconsistente entre pantallas y no es responsive.
- **Spec:** `docs/design.md` (v1) — principios, tokens, layout, inventario de componentes, patrones
  por página y checklist de PR. Es la referencia obligatoria.
- **Decisión (D-034):** paleta neutra con acento negro, Inter 400/600, borde en lugar de sombra,
  componentes en `app/ui/`.
- **Qué se hizo (avance 1, 2026-10-28):**
  - `tokens.py` con color, espacio, radio y escala tipográfica (`TYPE`); es el único archivo con
    valores literales.
  - `styles.py` (D-045): emite los tokens como variables CSS y concentra `:hover`,
    `:focus-visible`, `[disabled]`, `[aria-invalid]` y las media queries. Se inyecta una vez en
    `app/app.py`, así que toda ruta lo hereda.
  - `layout.py`: `AppShell`, `TopNav` (marca, buscador y cuenta como slots), `Container`,
    `PageHeader` y `Footer`.
  - `primitives.py`: `Button` (primary/secondary/ghost/danger + loading), `Input` (label visible,
    error junto al campo, `aria-invalid`), `Select` (nativo, con error), `Card`, `Badge` (dot por
    tono), `SizeChip` (seleccionado/deshabilitado) y `EmptyState` (título, texto y una acción).
  - `feedback.py`: `Skeleton` (línea/bloque/card), `Toast` (devuelve el evento de `rx.toast`),
    `Drawer` (panel lateral con título, cierre y `open` opcional) y `ConfirmDialog`
    (`role="alertdialog"`, confirmar/cancelar como botones propios).
  - `/` y `/register` se reescribieron con el shell y los primitivos: `pages/` no tiene hex,
    `box_shadow` ni `color_scheme`.
  - Verificado en el navegador con una galería temporal (borrada antes del commit): 360, 768 y
    1280px sin scroll horizontal; Inter cargada; controles de 44px; drawer a la derecha con scrim
    de `text` al 35 %; `ConfirmDialog` con `role="alertdialog"` y sin botones anidados; toast real
    al confirmar; el formulario de alta muestra el `Alert` de error con `role="alert"` al fallar.
- **Qué se hizo (avance 2, 2026-10-28):** el catálogo piloto se construyó entero con el sistema
  (`app/pages/catalogo_pagina.py`) y no necesitó ni un valor suelto: el bloque `_CATALOGO` de
  `styles.py` agrega `.ui-filters*`, `.ui-grid` (4/2/1 columnas), `.ui-product*` y `.ui-pagination`.
  `Select` acepta `opciones` con una lista de la base y `Badge` gana `quiet` para el
  `StockBadge` de design.md 4.3 (el punto lleva el tono, la etiqueta queda en `muted`).
- **AC propuestos:**
  - [x] Existe `app/ui/tokens.py` con los valores de `docs/design.md`; ningún archivo de
        `pages/` contiene hex, `box_shadow` ni `color_scheme` sueltos.
  - [x] `layout.py` implementa `AppShell`, `TopNav`, `Container`, `PageHeader` y `Footer`, y las
        páginas existentes los usan en lugar de repetir fondo y estructura.
  - [x] `primitives.py` implementa `Button` (primary/secondary/ghost/danger), `Input`, `Select`,
        `Card`, `Badge`, `SizeChip` y `EmptyState`, con estados normal/hover/focus/disabled.
        Se agrega `Alert` (D-045), que no estaba en la lista original.
  - [x] `feedback.py` implementa `Skeleton`, `Toast`, `Drawer` y `ConfirmDialog`.
  - [x] `ui_helpers.py` se elimina y no quedan imports.
  - [x] El catálogo se ve en 360px, 768px y 1280px sin scroll horizontal.
        Medido con iframes sobre `/`: 360 → 1 columna, 768 → 2, 1024/1280 → 4; `scrollWidth`
        igual a `clientWidth` en los cuatro anchos y filtros en 1/3/4/5 columnas.
  - [x] Contraste AA verificado; focus visible de 2px en todos los interactivos.
        Medido: texto/tarjeta 18.88:1, muted/lienzo 4.97:1, danger/tarjeta 6.57:1, success/tarjeta
        5.69:1. Foco: `outline: 2px solid accent` con `offset: 2px`.
  - [x] `reflex compile` pasa sin warnings nuevos.
- **Fuera de alcance:** componentes de dominio (`ProductCard`, `CartLine`, `OrdersTable`); se
  construyen dentro de T-030/T-031, T-040 y T-050 siguiendo el mismo documento.
- **Grill / preguntas abiertas:**
  - Ninguna: cerrado en D-034 y `docs/design.md`.
- **Depende de:** —

---

## T-064 · Notificaciones y logging

- **Estado:** lista · **Prioridad:** P2 · **Épica:** 07
- **Archivos:** `service/notifail.py`, `state/users_state.py:80-97`, `service/*`, `pages/*`
- **Problema:** se devuelven componentes desde handlers (error de Reflex), se usa `print()` y
  `traceback.print_exc()` en producción, y los errores se muestran crudos al usuario.
- **Decisión (D-035):** logging solo por consola, `INFO` en prod y `DEBUG` en dev; sin servicio
  externo ni identificador de error.
- **AC propuestos:**
  - [x] Feedback con `rx.toast` o vars de estado, nunca componentes desde handlers.
  - [x] `logging` configurado; sin `print()` de depuración.
  - [x] Errores técnicos al log; mensaje amigable al usuario.
  - [x] `notifail_component` eliminado o convertido en componente de UI válido.
  - [x] Los logs van solo a stdout, con nivel por entorno.
- **Grill / preguntas abiertas:**
  - Ninguna: cerrado en D-035.
- **Depende de:** T-060, T-062

---

## T-065 · Consultas de usuario (login obligatorio)

- **Estado:** lista · **Prioridad:** P1 · **Épica:** 07
- **Archivos:** `pages/consulta_usuario_page.py:7-52`, `state/users_state.py`
- **Problema:** si no hay sesión se usa `usuario_id = 1`, así que cualquiera escribe consultas a
  nombre de otro usuario. Además se lee `UsersState.id` como si fuera un valor, no un Var.
- **Decisión (D-002):** las consultas requieren login; no hay consultas anónimas.
- **AC propuestos:**
  - [x] Solo un usuario logueado puede crear consultas.
  - [x] El `usuario_id` sale de `LocalAuthState`/`UserProfile`, nunca de un default.
  - [x] El usuario solo ve sus propias consultas.
  - [x] Invitado → redirect al login.
  - [x] No se aceptan consultas anónimas con email.
- **Grill / preguntas abiertas:**
  - Ninguna: cerrado en D-002.
- **Depende de:** T-020, T-023

---

## T-075 · Nombres de archivo: ortografía y función

- **Estado:** lista · **Prioridad:** P1 · **Épica:** 07
- **Archivos:** todo `app/**/*.py`
- **Problema:** varios módulos tienen palabras mal escritas o nombres que no dicen qué hacen
  (`adnmin_shouder_page.py`, `andmin_page.py`, `ubicaccion_page.py`, `consulta_repocitory.py`,
  `conect_db.py`, `notifail.py`), y las capas mezclan sufijos en inglés y en español.
- **Decisión (D-040):** nombres de archivo en español, dominio y sufijo de capa; carpetas de capa
  sin cambios; los nombres de clase quedan como están (`CarritoState`), porque `AGENTS.md` sigue
  exigiendo identificadores en inglés.
- **Mapa de renombres (solo archivos que sobreviven a T-005, T-013, T-019 y T-060):**

| Capa | Actual | Nuevo |
|---|---|---|
| model | `product_model.py` | `producto_modelo.py` |
| model | `users_model.py` | `usuario_modelo.py` |
| model | `stock_model.py` | `variante_modelo.py` |
| model | `consulta_model.py` | `consulta_modelo.py` |
| model | `pedido_model.py` | `pedido_modelo.py` |
| model | `carrito_model.py` | `carrito_modelo.py` |
| model | `ubicacion_model.py` | `ubicacion_modelo.py` |
| repository | `conect_db.py` | `base_de_datos.py` |
| repository | `producto_repocitory.py` | `producto_repositorio.py` |
| repository | `consulta_repocitory.py` | `consulta_repositorio.py` |
| repository | `carrito_repository.py` | `carrito_repositorio.py` |
| repository | `catalogo_repository.py` | `catalogo_repositorio.py` |
| repository | `ubicacion_repository.py` | `ubicacion_repositorio.py` |
| repository | `users_repository.py` | `usuario_repositorio.py` |
| service | `servicio_stock.py` | `variante_servicio.py` |
| service | `ubicaccion_servicio.py` | `ubicacion_servicio.py` |
| service | `carrito_service.py` | `carrito_servicio.py` |
| service | `catalogo_service.py` | `catalogo_servicio.py` |
| service | `consulta_service.py` | `consulta_servicio.py` |
| service | `pedido_service.py` | `pedido_servicio.py` |
| service | `users_service.py` | `usuario_servicio.py` |
| service | `notifail.py` | `notificaciones.py` |
| state | `carrito_state.py` | `carrito_estado.py` |
| state | `catalogo_state.py` | `catalogo_estado.py` |
| state | `pedido_state.py` | `pedido_estado.py` |
| state | `users_state.py` | `autenticacion_estado.py` |
| state | `data.py` | `catalogo_datos.py` (o se elimina si queda sin uso) |
| pages | `adnmin_shouder_page.py` | `panel_admin_pagina.py` |
| pages | `catalogo_page.py` | `catalogo_pagina.py` |
| pages | `carrito_page.py` | `carrito_pagina.py` |
| pages | `producto_detalle_page.py` | `producto_detalle_pagina.py` |
| pages | `pedidos_page.py` | `pedidos_pagina.py` |
| pages | `pedidos_admin_page.py` | `pedidos_admin_pagina.py` |
| pages | `consulta_admin_page.py` | `consultas_admin_pagina.py` |
| pages | `consulta_usuario_page.py` | `consultas_usuario_pagina.py` |
| pages | `ubicaccion_page.py` + `ubicacion_page.py` | `ubicacion_pagina.py` (uno solo) |
| pages | `users_page.py` | `login_pagina.py` + `registro_pagina.py` |
| pages | `andmin_page.py` | se fusiona en `login_pagina.py` (D-018) |

- **Sin cambios:** `app/app.py` (convención del template de Reflex) y las
  carpetas `model/`, `repository/`, `service/`, `state/`, `pages/`, `ui/`.
- **Se eliminan, no se renombran:** `detalle_model.py`, `envio_model.py`, `presupuesto_model.py`,
  `solicitan_model.py`, `producto_model_pydantic.py`, `gerente_model.py`, `detalle_repository.py`,
  `gerente_repocitory.py`, `detalle_service.py`, `gerente_service.py`, `security.py`,
  `gdrive_service.py`, `google_drive_service.py`, `app_globals.py`, `app_state.py`,
  `global_state.py`, `compras_admin_state.py`, `compras_admin_page.py`, `ui_helpers.py`.
- **AC propuestos:**
  - [x] Convención definida: español para archivos, inglés para clases (D-040).
  - [ ] Ningún nombre de archivo contiene una palabra mal escrita.
  - [ ] Todas las capas usan `<dominio>_<capa>.py` con el sufijo en español.
  - [ ] No quedan dos archivos que representen lo mismo (`ubicacion_page.py` vs `ubicaccion_page.py`).
  - [ ] Los `import` están actualizados; `rg` de los nombres viejos no devuelve nada.
  - [ ] `reflex compile` pasa sin warnings nuevos y los tests corren.
  - [ ] El rename va en un commit aislado (solo movimientos + imports) para poder revisarlo.
  - [ ] Cada nombre permite adivinar capa y dominio sin abrir el archivo.
- **Grill / preguntas abiertas:**
  - Ninguna: cerrado en D-040.
- **Depende de:** T-005, T-013, T-019, T-060, T-061
