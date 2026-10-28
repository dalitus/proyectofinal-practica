# EPIC 04 — Catálogo y producto

**Objetivo:** que el comprador vea productos con precio final claro, detalle consistente e
imágenes que no se rompan.

---

## T-030 · Estado de carga y listado del catálogo

- **Estado:** lista · **Prioridad:** P1 · **Épica:** 04
- **Archivos:** `pages/catalogo_page.py:119-128`, `state/catalogo_state.py:18-45`
- **Problema:** `CatalogoState.productos == []` se compila a `=== []` (siempre falso), así que el
  spinner nunca aparece y no se distingue “cargando” de “sin resultados”.
- **Decisión (D-014):** los agotados se muestran como “sin stock”; filtros y paginación definidos.
- **AC propuestos:**
  - [x] Var `loading: bool` explícita, con skeleton mientras carga.
  - [x] Estado vacío distinto de error y de “sin resultados de búsqueda”.
  - [x] Usar `.length() == 0` en lugar de comparar con `[]`.
  - [x] Refrescar la página vuelve a cargar el catálogo.
  - [x] Los productos sin stock se muestran como “sin stock” (D-014).
- **Grill / preguntas abiertas:**
  - Ninguna: cerrado en D-014.
- **Depende de:** T-010

---

## T-031 · Detalle de producto por URL (refresh-safe)

- **Estado:** lista · **Prioridad:** P1 · **Épica:** 04
- **Archivos:** `pages/producto_detalle_page.py:4-30`, `state/catalogo_state.py:47-51`,
  `app/app.py:27`
- **Problema:** el detalle depende de `producto_seleccionado` en memoria y la ruta está registrada
  dos veces (estática `/detalle_producto` y dinámica `[producto_id]`). Al refrescar o compartir el
  link se pierde el producto.
- **Decisión (D-024):** ruta única `/producto/[id]`; `/detalle_producto` redirige; el detalle es
  público (D-002).
- **AC propuestos:**
  - [x] Ruta única `/producto/[producto_id]`.
  - [x] El handler `on_load` busca el producto en la DB por ID.
  - [x] Refresh y link directo funcionan.
  - [x] Producto inexistente → estado “no encontrado” con link al catálogo.
  - [x] “Agregar al carrito” usa el ID real de la variante elegida (D-009).
  - [x] El detalle es visible para invitados; agregar al carrito exige login (D-002).
- **Grill / preguntas abiertas:**
  - Ninguna: cerrado en D-024 y D-002.
- **Depende de:** T-030, T-061

---

## T-032 · Precio final y formato en la UI

- **Estado:** lista · **Prioridad:** P1 · **Épica:** 04
- **Archivos:** `pages/catalogo_page.py:83`, `pages/producto_detalle_page.py:24`,
  `pages/carrito_page.py:19-21`, `pages/pedidos_page.py:53`
- **Problema:** el precio se muestra de formas distintas y no hay una definición única de “precio
  final”. El comprador debe ver el precio final sin sorpresas.
- **Decisión (D-003):** precio final ARS con IVA incluido, formato es-AR, sin descuentos.
- **AC propuestos:**
  - [x] Un helper único de formato (moneda, separador de miles, decimales).
  - [ ] Catálogo, detalle, carrito y pedidos muestran el mismo precio para el mismo producto.
  - [x] El precio final se define una vez (D-003) y se documenta.
  - [ ] El total del carrito y del pedido sale del mismo cálculo.
- **Grill / preguntas abiertas:**
  - Ninguna: cerrado en D-003.
- **Depende de:** T-014

---

## T-033 · Visibilidad, filtros y orden del catálogo

- **Estado:** lista · **Prioridad:** P2 · **Épica:** 04
- **Archivos:** `pages/catalogo_page.py:6-49`, `service/catalogo_service.py:22-29`
- **Problema:** el catálogo solo filtra por nombre/marca y oculta productos sin stock. No hay
  filtros por categoría/talle/color ni orden.
- **Decisión (D-014):** mostrar agotados como “sin stock”; filtros de texto/categoría/talle/color;
  orden nombre A-Z con precio asc/desc; 12 por página.
- **AC propuestos:**
  - [x] Política de stock definida: se muestran como “sin stock” y no se pueden agregar.
  - [x] Filtros de búsqueda, categoría, talle y color, combinables.
  - [x] Orden por nombre (default) y por precio asc/desc.
  - [x] Paginación de 12 productos por página.
  - [ ] Estado vacío claro cuando no hay coincidencias.
- **Grill / preguntas abiertas:**
  - Ninguna: cerrado en D-014.
- **Depende de:** T-030

---

## T-034 · Imágenes: placeholder, upload, Drive, create/edit

- **Estado:** lista · **Prioridad:** P1 · **Épica:** 04
- **Archivos:** `pages/adnmin_shouder_page.py:108-110,198-201,383-385`,
  `service/producto_servicio.py:32-46,67-76`, `service/gdrive_service.py`,
  `rxconfig.py:12`, `assets/`
- **Problema:** se referencia `/static/default.jpg`, que no existe; `upload_dir="static"` no sigue
  la convención de Reflex (`assets/`); no hay `rx.upload`, así que `imagen_local` nunca se llena y
  la subida a Drive es inalcanzable. Crear producto ignora `imagen_url` y editar no actualiza la imagen.
- **Decisión (D-015):** una imagen por producto, upload local en `assets/uploads/`, JPG/PNG/WebP
  hasta 2 MB, placeholder real.
- **AC propuestos:**
  - [x] Existe un placeholder válido en `assets/` y se usa en todo el sitio.
  - [x] Crear/editar producto persiste la imagen subida.
  - [x] `rx.upload` con validación de tipo/tamaño y feedback.
  - [x] Si la subida falla, el producto se guarda con placeholder y se informa.
  - [x] `alt` descriptivo en todas las imágenes.
  - [x] Una sola imagen por producto.
- **Grill / preguntas abiertas:**
  - Ninguna: cerrado en D-015.
- **Depende de:** T-050
