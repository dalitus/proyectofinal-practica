# Decisiones (ADR-lite)

Registro de decisiones cerradas durante el grill. Cada decisión tiene ID, tarea asociada, fecha,
opción elegida y motivo. Las decisiones pendientes se marcan como `pendiente`.

---

## D-001 · Identidad del administrador

- **Tarea:** T-011
- **Estado:** reemplazada por D-019
- **Opciones:** tabla `gerentes` existente / `Users` con rol / ambos
- **Decisión original:** el administrador único vivía en `gerentes`; `AuthState` exponía
  `rol = "admin"`.
- **Motivo del cambio:** al adoptar `reflex-local-auth` (D-019), toda la identidad pasa a
  `LocalUser` + `UserProfile`, y el admin se marca con `UserProfile.is_admin`. Mantener `gerentes`
  habría dejado dos caminos de auth.
- **Fecha:** 2026-10-27

---

## D-002 · Política de invitados

- **Tarea:** T-041
- **Estado:** decidida
- **Opciones:** solo lectura / carrito local / login obligatorio
- **Decisión:** el invitado puede ver catálogo, precios finales y detalle. Para agregar al carrito,
  comprar, ver pedidos o enviar consultas debe iniciar sesión. Al intentar una acción protegida se
  redirige al login y se vuelve al punto de origen. No hay carrito de invitado.
- **Motivo:** mantiene simple la consistencia del carrito (solo DB por usuario), evita fusiones y
  cumple con “ver precios y agregar al carrito” para compradores registrados.
- **Consecuencias:** el carrito se persiste solo en DB; `CartState` depende de `AuthState`; las
  guardas de T-023 cubren carrito, pedidos y consultas; se elimina la idea de merge local/DB.
- **Fecha:** 2026-10-27

---

## D-003 · Precio final

- **Tarea:** T-014, T-032
- **Estado:** decidida
- **Opciones:** IVA incluido sin extras / IVA discriminado / descuentos
- **Decisión:** el precio es final en ARS, con IVA incluido y sin descuentos ni cargos extra en esta
  versión. Se guarda con dos decimales (`DECIMAL(10,2)`) y se muestra con formato es-AR
  (`$ 1.234,56`). Los totales se calculan en el servidor.
- **Motivo:** es lo que el comprador espera ver (“precio final”) y evita mostrar sorpresas al pagar.
- **Consecuencias:** no hay línea de IVA ni promociones en el MVP; el modelo queda preparado para
  agregarlas después. Los estados y la UI consumen un único helper de formato.
- **Fecha:** 2026-10-27

---

## D-004 · Stock

- **Tarea:** T-042
- **Estado:** decidida (queda abierta la granularidad en T-050)
- **Opciones:** reservar en checkout / descontar al confirmar / permitir sobreventa
- **Decisión:** se valida stock al agregar y se revalida al confirmar. El descuento se hace en una
  transacción al crear el pedido; si no alcanza, el pedido no se crea y se informa el producto que
  falló. No hay reservas con vencimiento ni sobreventa.
- **Motivo:** evita vender unidades inexistentes sin agregar una tabla de reservas y trabajos de
  expiración; la transacción cubre la carrera de dos compradores.
- **Consecuencias:** el carrito puede quedar desactualizado y se corrige al confirmar; cancelar un
  pedido debería reponer stock (definir en T-044); hace falta bloquear la fila de stock en la
  transacción.
- **Fecha:** 2026-10-27

---

## D-005 · Checkout y pago

- **Tarea:** T-043
- **Estado:** decidida
- **Opciones:** solo registro de pedido / pago online / retiro en local
- **Decisión:** el checkout solo registra el pedido con datos de entrega; no hay pago online ni
  estados de pago. El pago se coordina fuera de la app (efectivo/transferencia) y el pedido nace en
  “en espera”. MercadoPago queda fuera de esta versión.
- **Motivo:** es el alcance más cercano a lo que ya existe y evita credenciales, webhooks y manejo
  de fallos de una pasarela en el MVP.
- **Consecuencias:** no se agrega `estado_pago`; `pedido.estado` cubre solo el cumplimiento;
  `tmp_mp_test.py` se descarta o queda como experimento fuera del alcance. El envío se coordina con
  el administrador y no se guarda un costo de envío en la DB.
- **Fecha:** 2026-10-27

---

## D-006 · Consulta automática al comprar

- **Tarea:** T-045
- **Estado:** decidida
- **Opciones:** eliminarla / conservarla como nota interna / convertirla en notificación
- **Decisión:** se elimina. La compra no crea consultas; el pedido es la única fuente de verdad.
  Se quitan los filtros especiales de “Compra realizada” y se limpian las consultas históricas de
  ese asunto mediante una migración (con backup previo).
- **Motivo:** evita duplicar datos y que la tabla de consultas se ensucie con eventos de compra.
- **Consecuencias:** el admin ve la compra en “Pedidos”; si en el futuro hace falta un aviso, se
  implementa como notificación (T-064), no como consulta.
- **Fecha:** 2026-10-27

---

## D-007 · Versiones y entorno

- **Tarea:** T-001, T-004, T-006
- **Estado:** decidida
- **Opciones:** Reflex 0.8.4 + Pydantic 2 / última Reflex / congelar entorno
- **Decisión:** actualizar a Reflex 0.10.1 (última estable al 2026-10-27), Pydantic >=2.12 y
  Python >=3.11 (el venv usa 3.13). La migración se planifica en T-006.
- **Motivo:** salir de una combinación vieja y frágil, y evitar el fallo de arranque en prod.
- **Consecuencias:** hay breaking changes de 0.10 (lectura de vars backend con `default_value()`,
  defaults mutables deep-copy, state store incompatible con 0.9). Actualizar todas las instancias
  juntas y limpiar `.states` al desplegar. `pydantic 2` obliga a revisar `.dict()` → `model_dump()`.
- **Fecha:** 2026-10-27

---

## D-008 · Persistencia del carrito de invitado

- **Tarea:** T-041
- **Estado:** descartada
- **Opciones:** cookie/local storage / solo DB al loguearse / no permitir
- **Decisión:** no se implementa carrito de invitado. D-002 establece que el carrito vive solo en
  la DB y requiere sesión.
- **Motivo:** evita merge de carritos y mantiene una sola fuente de verdad.
- **Fecha:** 2026-10-27

---

## D-010 · Cancelación de pedidos

- **Tarea:** T-044
- **Estado:** decidida
- **Opciones:** usuario cancela en espera / solo admin / sin cancelación
- **Decisión:** solo el administrador puede cancelar, desde “en espera” o “enviado” (nunca desde
  “entregado”). Al cancelar se repone el stock de todas las variantes del pedido. El usuario no
  cancela; solo consulta el estado.
- **Motivo:** evita carreras y abusos desde la cuenta del comprador, y deja el control de stock en
  manos del admin.
- **Consecuencias:** transiciones válidas: en espera → enviado → entregado; en espera/enviado →
  cancelado. Se necesita historial/fecha de cancelación y una operación transaccional de reposición.
- **Fecha:** 2026-10-27

---

## D-011 · Base de datos canónica

- **Tarea:** T-002, T-003
- **Estado:** decidida
- **Opciones:** MySQL local `zapateria_db` / MySQL remoto / SQLite dev + MySQL prod
- **Decisión:** una sola URL en `.env` (`DATABASE_URL`) apuntando a MySQL local con la base
  `zapateria_db`. Sin credenciales por defecto en el código: si falta la variable, el arranque
  falla con un mensaje claro. La app, los repositorios y Alembic usan esa misma URL.
- **Motivo:** es la opción más simple para desarrollo y entrega, y evita divergencias entre el
  motor de Reflex y el engine propio. SQLite se descarta porque `DECIMAL`, locks y constraints no
  se comportan igual que en producción.
- **Consecuencias:** `rxconfig.py`, `conect_db.py` y `alembic/env.py` leen la misma variable; se
  elimina `session = Session(engine)` a nivel módulo; `.env.example` documenta la URL. `zap_db`
  deja de existir como nombre alternativo.
- **Fecha:** 2026-10-27

---

## D-012 · Estrategia de migraciones

- **Tarea:** T-003
- **Estado:** decidida
- **Opciones:** recrear desde cero / preservar datos / sin Alembic
- **Decisión:** se borra `zapateria_db`, se descarta el historial roto (incluida `57fefbfec4ff`) y
  se genera una única migración inicial limpia desde los modelos. Las migraciones se corren a mano
  con `alembic upgrade head`, documentado en el README; no se ejecutan automáticamente al arrancar.
- **Motivo:** la base actual es de prueba y no hay datos reales que conservar; empezar de cero deja
  un historial coherente y evita arrastrar el `NameError` de `sqlmodel`.
- **Consecuencias:** se pierde cualquier dato de la DB local; hay que recrear el admin por seed
  (T-024); cada cambio de esquema posterior va en una migración nueva; el deploy debe correr la
  migración como paso explícito.
- **Fecha:** 2026-10-27

---

## D-009 · Variantes de producto

- **Tarea:** T-050, T-010, T-040, T-043
- **Estado:** decidida
- **Opciones:** color + talle / solo color / solo producto
- **Decisión:** la variante con stock propio es la combinación `(producto_id, color, talle)`.
  `Producto` deja de tener un `talle` único; el talle pasa a la variante. El carrito referencia
  una variante (`stock_id`/`variante_id`), no solo el producto. El pedido guarda un snapshot con
  color, talle y precio unitario.
- **Motivo:** es calzado/indumentaria: el mismo modelo en negro 38 y negro 39 son unidades
  distintas. Sin esto se puede vender un talle agotado.
- **Consecuencias:** migración de `stocks` (agregar `talle` y unique `(producto_id, color, talle)`),
  quitar `talle` de `productos`, ajustar carrito/pedido/admin/catálogo, y la UI debe pedir
  variante antes de agregar al carrito.
- **Fecha:** 2026-10-27

---

## D-013 · Bootstrap del administrador

- **Tarea:** T-024
- **Estado:** decidida
- **Opciones:** seed desde `.env` / CLI interactivo / SQL manual
- **Decisión:** un seed idempotente lee `ADMIN_EMAIL` y `ADMIN_PASSWORD` del `.env`. Si el admin no
  existe, lo crea en `gerentes` con la contraseña hasheada; si existe, no lo modifica. Se ejecuta
  con un comando documentado, una sola vez. No se fuerza el cambio de contraseña en el primer login.
- **Motivo:** deja el alta reproducible y sin intervención manual, y permite que el admin cambie su
  contraseña desde el panel cuando quiera.
- **Consecuencias:** `ADMIN_EMAIL`/`ADMIN_PASSWORD` entran en `.env.example` (sin valores reales);
  el seed forma parte del runbook de instalación; el formulario público nunca crea gerentes.
- **Fecha:** 2026-10-27

---

## D-014 · Catálogo: visibilidad, filtros y orden

- **Tarea:** T-033, T-030
- **Estado:** decidida
- **Opciones:** ocultar agotados / mostrar “sin stock” / permitir pedir sin stock
- **Decisión:** los productos y variantes agotadas se siguen mostrando, marcadas como “sin stock” y
  sin poder agregarse al carrito. Filtros combinables: búsqueda por texto, categoría, talle y color.
  Orden por defecto nombre A-Z, con opción precio menor→mayor y mayor→menor. Paginación de 12
  productos por página con anterior/siguiente.
- **Motivo:** el comprador ve que el producto existe y puede consultar; los filtros por talle/color
  son los que realmente usa en calzado. La paginación mantiene los links compartibles y no rompe con
  filtros.
- **Consecuencias:** el catálogo necesita `loading`, `pagina`, `total_paginas` y filtros como vars;
  la consulta se hace server-side con `LIMIT/OFFSET`; las variantes agotadas se deshabilitan en el
  detalle (D-009).
- **Fecha:** 2026-10-27

---

## D-015 · Imágenes de producto

- **Tarea:** T-034
- **Estado:** decidida
- **Opciones:** upload local / Google Drive / solo URL
- **Decisión:** una sola imagen por producto. El admin la sube con `rx.upload`; se guarda en
  `assets/uploads/` con nombre único y la DB persiste la ruta relativa. Se aceptan JPG, PNG y WebP
  de hasta 2 MB, validados en el servidor. Si no hay imagen, se usa un placeholder en `assets/`.
- **Motivo:** funciona sin credenciales externas, es el mecanismo estándar de Reflex y evita la
  fragilidad de Google Drive para un proyecto de entrega.
- **Consecuencias:** `upload_dir` pasa de `static` a `assets` o se alinea con la convención;
  el placeholder `/static/default.jpg` se reemplaza por uno real; `gdrive_service.py` queda fuera
  del flujo (se evalúa eliminar en T-005/T-060); `alt` obligatorio en la UI.
- **Fecha:** 2026-10-27

---

## D-016 · Camino de upgrade a Reflex 0.10

- **Tarea:** T-006
- **Estado:** decidida
- **Opciones:** directo 0.8.4 → 0.10.1 / escalonado por 0.9
- **Decisión:** upgrade directo de 0.8.4 a 0.10.1 en una rama, aplicando las guías de upgrade de
  0.9 y 0.10, con `reflex compile` y smoke tests de catálogo, login, carrito, pedido y admin. No se
  preservan sesiones activas porque no hay usuarios reales.
- **Motivo:** el proyecto es chico y no hay estado que conservar; pasar por 0.9 duplica trabajo y
  pruebas sin un beneficio claro.
- **Consecuencias:** revisar `default_value()` en lecturas de vars backend, defaults mutables,
  `.dict()` → `model_dump()`, y limpiar `.states`/`.web` al desplegar. Si algo se traba, se puede
  abrir una rama intermedia 0.9 como plan B.
- **Fecha:** 2026-10-27

---

## D-017 · Duración y concurrencia de sesión

- **Tarea:** T-020
- **Estado:** reemplazada por D-020
- **Opciones:** sesión de Reflex / cookie HttpOnly persistente / “recordarme”
- **Decisión original:** sesión de Reflex sin persistencia extra; el login sobrevivía a refresh
  pero no a un reinicio del servidor.
- **Motivo del cambio:** el plugin adoptado en D-019 ya persiste la sesión 7 días en
  `LocalAuthSession` + `localStorage`; forzar sesión efímera habría requerido desactivar esa capa.
- **Fecha:** 2026-10-27

---

## D-018 · Login y registro

- **Tarea:** T-021
- **Estado:** decidida
- **Opciones:** login único / rutas separadas / selector de rol
- **Decisión:** un solo formulario de login (`email` + `password`) en `/login`. El servicio busca
  primero en `gerentes` y después en `users`, y redirige según el rol. El registro es abierto solo
  para compradores. No hay verificación de email ni recuperación automática de contraseña: el admin
  puede resetear la clave de un comprador.
- **Motivo:** evita duplicar formularios y redirecciones, y no agrega dependencia de SMTP en el MVP.
- **Consecuencias:** el admin nunca se registra desde el formulario público (D-013); el email de
  comprador es único; el mensaje de error no revela si el email existe; si más adelante hace falta
  recuperación, se agrega como flujo nuevo sobre T-021/T-022.
- **Fecha:** 2026-10-27

---

## D-019 · Autenticación con `reflex-local-auth`

- **Tarea:** T-022, T-011, T-010, T-024
- **Estado:** decidida (validada en el spike del 2026-10-28 sobre Reflex 0.10.1)
- **Opciones:** bcrypt + AuthState propio / plugin `reflex-local-auth` / FastAPI + JWT
- **Decisión:** se usa `reflex-local-auth` 0.5.0 para todos los actores. `LocalUser` guarda
  credenciales (`username` = email, `password_hash`, `enabled`) y `UserProfile` guarda nombre,
  email visible, `is_admin` y `local_user_id`. Se eliminan las tablas `users` y `gerentes`; como la
  DB se recrea (D-012), no hay migración de datos.
- **Motivo:** el plugin ya resuelve hash bcrypt, login, registro, logout y decorador
  `require_login`, y evita reimplementar auth. Se prefiere sobre la implementación propia por
  decisión del usuario.
- **Riesgos:** la 0.5.0 se publicó en mayo 2026 y se actualizó para Reflex 0.9; no hay release
  probado contra 0.10. Si el smoke test de T-006/T-022 falla, el plan B es bcrypt + `AuthState`
  propio manteniendo `LocalUser` + `UserProfile` como modelo.
- **Consecuencias:** el formulario muestra “Email” pero el campo del plugin se llama `username`;
  el registro necesita un estado propio que cree también `UserProfile`; el admin se marca con
  `UserProfile.is_admin`; `UserProfile` debe tener un único admin por defecto.
- **Fecha:** 2026-10-27

---

## D-020 · Sesión persistente del plugin

- **Tarea:** T-020, T-022
- **Estado:** decidida (reemplaza D-017)
- **Opciones:** sesión de Reflex / cookie persistente / “recordarme”
- **Decisión:** se usa la sesión del plugin: `LocalAuthSession` en DB y `auth_token` en
  `localStorage`, con vencimiento de 7 días. El login sobrevive a refresh y a reinicios del
  servidor. Se permiten varias sesiones simultáneas por usuario.
- **Motivo:** es el comportamiento por defecto del plugin adoptado en D-019 y mejora la experiencia
  de compra sin trabajo adicional.
- **Consecuencias:** existe una tabla de sesiones (`LocalAuthSession`); el token vive en
  `localStorage` (riesgo de XSS, mitigado no renderizando HTML de usuario); el logout borra las
  sesiones de ese token; no hay cookie `HttpOnly` propia.
- **Fecha:** 2026-10-27

---

## D-021 · Respuesta ante falta de permiso

- **Tarea:** T-023
- **Estado:** decidida
- **Opciones:** invitado a login + 403 / siempre login / 404
- **Decisión:** invitado → `/login` con `redirect_to`; usuario logueado sin permiso → página 403
  con link al catálogo. El chequeo es server-side en `on_load` de cada página protegida.
- **Motivo:** mantiene el flujo de login para el invitado y le dice la verdad al comprador que
  intenta entrar al panel admin, sin fingir que la ruta no existe.
- **Consecuencias:** hace falta una página 403 reutilizable; las rutas admin usan un guard que lee
  `UserProfile.is_admin`; las rutas de comprador usan `require_login` del plugin.
- **Fecha:** 2026-10-27

---

## D-022 · Límite de unidades en el carrito

- **Tarea:** T-040, T-042
- **Estado:** decidida
- **Opciones:** solo stock / máximo 5 / máximo 10
- **Decisión:** no hay tope arbitrario. La cantidad por variante se limita únicamente al stock
  disponible de esa variante (`(producto_id, color, talle)`).
- **Motivo:** el stock real ya es el límite correcto; un número fijo complica la UI y no aporta.
- **Consecuencias:** el carrito valida contra `stock.cantidad` al agregar y al confirmar (D-004);
  si el admin baja el stock, el carrito se corrige en el checkout.
- **Fecha:** 2026-10-27

---

## D-023 · Categorías y marcas

- **Tarea:** T-050, T-033
- **Estado:** decidida
- **Opciones:** categoría fija + marca libre / ambas fijas / ambas libres
- **Decisión:** la categoría vive en una tabla `Categoria` administrable y el producto la referencia
  con `categoria_id`. La marca es texto libre en el producto. Los filtros del catálogo usan la
  categoría de la tabla y la marca como texto.
- **Motivo:** evita que un typo rompa el filtro de categoría sin obligar al admin a mantener dos
  catálogos completos.
- **Consecuencias:** nueva tabla `Categoria` (nombre único) y migración inicial; el formulario de
  producto usa un select de categoría; el filtro por categoría es por ID; la marca se busca por
  texto normalizado.
- **Fecha:** 2026-10-27

---

## D-024 · Rutas canónicas

- **Tarea:** T-061, T-031, T-030
- **Estado:** decidida
- **Opciones:** `/` catálogo / landing / redirect; `/login` + `/register`; `/producto/[id]`
- **Decisión:** `/` es el catálogo. `/catalogo` redirige a `/`. Login y registro en `/login` y
  `/register`; `/users` y `/user` redirigen a `/login`. El detalle es `/producto/[id]`;
  `/detalle_producto` redirige a `/producto`. Se registra cada página una sola vez con `@rx.page`.
- **Motivo:** URLs cortas y estables, sin duplicar registros ni links; los redirects preservan
  links viejos sin mantener dos implementaciones.
- **Consecuencias:** hay que definir una tabla de redirects o handlers para las rutas viejas; el
  detalle busca el producto por ID en `on_load`; la ruta inexistente muestra un 404 amigable.
- **Fecha:** 2026-10-27

---

## D-025 · Página de ubicación

- **Tarea:** T-060, T-005
- **Estado:** decidida
- **Opciones:** imagen + link / Leaflet / Google Maps embebido
- **Decisión:** la página de ubicación muestra dirección, horarios y una imagen/plano del local,
  con un botón “Abrir en Google Maps”. No se embebe un mapa ni se usa API key.
- **Motivo:** cubre la necesidad sin agregar dependencias JS, credenciales ni costos.
- **Consecuencias:** `google_drive_service.py` y las variantes muertas de `UbicacionState` se
  eliminan (T-005/T-060); la dirección y el link viven en configuración o constantes de la página.
- **Fecha:** 2026-10-27

---

## D-026 · Limpieza de scripts one-off

- **Tarea:** T-005
- **Estado:** decidida
- **Opciones:** borrar one-off / archivar en `scripts/legacy/` / dejar como están
- **Decisión:** se borran `add_*`, `fix_*`, `temp_*` y los `test_*` manuales de la raíz. Se
  conservan y reescriben `seed.py` y `run.ps1`. `security.py` (PBKDF2) se elimina cuando el plugin
  `reflex-local-auth` (bcrypt) esté en su lugar. Los tests reales viven en `tests/` (T-070).
- **Motivo:** la DB se recrea (D-012) y los parches one-off ya no aplican; los `test_*` no son
  pytest y solo imprimen. Archivar mantiene ruido y deuda.
- **Consecuencias:** no hay scripts de migración manual en la raíz; el seed queda como única puerta
  de datos iniciales; antes de borrar, revisar que ningún import apunte a esos archivos.
- **Fecha:** 2026-10-27

---

## D-027 · Gestor de dependencias

- **Tarea:** T-004
- **Estado:** decidida
- **Opciones:** `uv` / `pip-tools` / Poetry
- **Decisión:** se migra a `uv` con `pyproject.toml` y `uv.lock`. Se mantiene Python 3.13 y el venv
  actual; la instalación reproducible es `uv sync`.
- **Motivo:** lockfile real, resolución rápida y un solo comando para reproducir el entorno, sin
  abandonar el venv.
- **Consecuencias:** `requirements.txt` se reemplaza o se conserva como referencia; el README usa
  `uv sync`; el CI (T-071) instala con `uv`; las dependencias directas incluyen `reflex`,
  `reflex-local-auth`, `sqlmodel`, `alembic`, `pymysql` y `bcrypt`.
- **Fecha:** 2026-10-27

---

## D-028 · Borrado lógico y desactivación

- **Tarea:** T-012
- **Estado:** decidida
- **Opciones:** borrado lógico con `activo` / físico sin pedidos / cascada
- **Decisión:** los productos se eliminan lógicamente con `activo = False`; nunca se borra la fila.
  Los usuarios se desactivan con `LocalUser.enabled = False` (el plugin ya bloquea el login); no se
  borran para preservar pedidos. Los pedidos históricos conservan el snapshot de la compra.
- **Motivo:** mantiene la trazabilidad y no rompe pedidos, reportes ni el historial de compras.
- **Consecuencias:** el catálogo filtra `activo = True`; el admin ve inactivos en una vista aparte;
  `Producto` gana `activo: bool = True`; no se permite borrar físicamente desde la UI.
- **Fecha:** 2026-10-27

---

## D-029 · Líneas del pedido y tablas legado

- **Tarea:** T-013, T-043, T-044, T-051
- **Estado:** decidida
- **Opciones:** `PedidoItem` normalizado / `productos_json` / adaptar `detalles`
- **Decisión:** se crea `PedidoItem` con `pedido_id`, `variante_id`, `color`, `talle`, `cantidad` y
  `precio_unitario`. `Pedido.productos_json` se elimina. Se eliminan las tablas y modelos legado
  `detalles`, `envios`, `presupuestos`, `solicitan` y `producto_model_pydantic`.
- **Motivo:** el admin necesita listar líneas sin parsear JSON y la cancelación debe reponer stock
  por variante; una tabla normalizada lo resuelve con FKs y consultas simples.
- **Consecuencias:** el pedido guarda snapshot de color/talle/precio al comprar; el total se calcula
  como suma de `cantidad * precio_unitario`; `Detalles` no se reutiliza; migración inicial incluye
  `pedido_items`.
- **Fecha:** 2026-10-27

---

## D-030 · Administración de pedidos y consultas

- **Tarea:** T-051, T-052
- **Estado:** decidida
- **Opciones:** exportar / borrar pedidos / responder consultas por email
- **Decisión:** los pedidos no se borran ni se exportan; el admin los filtra por estado y busca por
  cliente/producto, y ve el detalle con `PedidoItem`. Las consultas se responden solo en la web y
  se pueden eliminar con confirmación; no hay envío por email ni archivado.
- **Motivo:** el volumen de una tienda chica no justifica exportación ni historial de consultas; el
  pedido ya es la fuente de verdad de la compra.
- **Consecuencias:** no se agrega `openpyxl` ni `archivada`; la eliminación de consultas es física y
  pide confirmación; los filtros de pedidos usan los estados de D-010.
- **Fecha:** 2026-10-27

---

## D-031 · Auditoría mínima

- **Tarea:** T-053
- **Estado:** decidida
- **Opciones:** logging estructurado / tabla `AuditLog` / sin auditoría
- **Decisión:** cada operación sensible (borrar producto, cambiar estado, cancelar pedido, borrar
  consulta) escribe un log estructurado con admin, acción, entidad y timestamp. No hay tabla ni
  pantalla de auditoría.
- **Motivo:** deja rastro para depurar sin sumar modelo, migración ni UI en el MVP.
- **Consecuencias:** se usa el `logging` de T-064; el logger incluye `admin_id` y `entidad_id`; las
  operaciones destructivas siguen pidiendo confirmación en la UI.
- **Fecha:** 2026-10-27

---

## D-032 · Checkout como página

- **Tarea:** T-043
- **Estado:** decidida
- **Opciones:** página `/checkout` / modal / drawer
- **Decisión:** el checkout es una página en `/checkout` con `AddressForm` y `OrderSummary` sticky.
  El carrito solo muestra líneas y el CTA “Ir a pagar”. Carrito vacío redirige a `/carrito`.
- **Motivo:** hay varios campos y validaciones; una página da espacio, funciona mejor en mobile y
  coincide con `docs/design.md`.
- **Consecuencias:** se elimina el modal de checkout del carrito; la validación es por campo y en
  servidor; la confirmación del pedido ocurre en `/checkout`; el total se recalcula al confirmar.
- **Fecha:** 2026-10-27

---

## D-033 · Capas y event handlers

- **Tarea:** T-062
- **Estado:** decidida
- **Opciones:** mantener `repository → service → state` / simplificar a `service → state`
- **Decisión:** se mantiene `model → repository → service → state → pages`. Los estados no abren
  sesiones ni importan `engine`; toda operación pasa por un service. Los handlers son finos:
  llaman al service, actualizan vars y devuelven evento/toast. Los handlers de DB son síncronos;
  `async` solo cuando hace falta `await` de otro estado. Los errores técnicos van al log y al
  usuario le llega un mensaje claro.
- **Motivo:** es la arquitectura que ya fija `AGENTS.md` y evita que la UI toque la DB.
- **Consecuencias:** `conect_db.get_session()` se usa solo en repositories/services; se eliminan
  los `Session(engine)` y `traceback.print_exc()` de states/pages; los services lanzan errores de
  dominio que el state traduce a un mensaje.
- **Fecha:** 2026-10-27

---

## D-034 · Sistema de diseño obligatorio

- **Tarea:** T-063, T-074
- **Estado:** decidida
- **Opciones:** mantener celeste actual / definir paleta nueva / usar `docs/design.md`
- **Decisión:** se usa `docs/design.md` como fuente única: fondo blanco, tokens neutros, acento
  negro, Inter, bordes en lugar de sombras, mobile primero, contraste AA, labels visibles, `alt`
  obligatorio y estados vacío/carga/error. Nada de hex sueltos en `pages/`.
- **Motivo:** el documento ya existe, está completo y evita discutir estilos pantalla por pantalla.
- **Consecuencias:** los componentes viven en `app/ui/`; `pages/` solo compone; se elimina
  `background_color="#ADD8E6"` y los `min_height="100vh"` repetidos; la accesibilidad AA es parte
  del Definition of Done.
- **Fecha:** 2026-10-27

---

## D-035 · Destino de logs

- **Tarea:** T-064, T-053
- **Estado:** decidida
- **Opciones:** consola + archivo / solo consola / servicio externo
- **Decisión:** logging solo por consola (stdout), con `INFO` en producción y `DEBUG` en dev. Sin
  archivo rotativo ni servicio externo.
- **Motivo:** es lo más simple y el hosting puede capturar stdout si hace falta; no agrega
  dependencias ni configuración.
- **Consecuencias:** no hay historial persistente de logs; las operaciones sensibles de D-031 se
  registran en el log de la ejecución, no en una tabla. No se agrega identificador de error.
- **Fecha:** 2026-10-27

---

## D-036 · Base de datos y alcance de tests

- **Tarea:** T-070
- **Estado:** decidida
- **Opciones:** MySQL `zapateria_test` / SQLite en memoria / híbrido
- **Decisión:** los tests corren con `pytest` contra una base MySQL `zapateria_test`, creada y
  limpiada por fixtures. Flujos obligatorios: registro/login, catálogo y detalle, carrito y stock,
  checkout y pedido, y admin de productos/pedidos/consultas.
- **Motivo:** mismo motor que producción; `DECIMAL`, locks y FKs se comportan igual, y los tests de
  stock transaccional tienen sentido.
- **Consecuencias:** el CI necesita un servicio MySQL (T-071); `DATABASE_URL` de test va en
  `.env.test` o variable de entorno; los tests no tocan `zapateria_db`.
- **Fecha:** 2026-10-27

---

## D-037 · Calidad local sin CI

- **Tarea:** T-071
- **Estado:** decidida
- **Opciones:** GitHub Actions informativo / bloqueante / solo pre-commit local
- **Decisión:** solo pre-commit local con `ruff check`, `ruff format --check` y `pytest` en
  pre-push. No se configura GitHub Actions ni branch protection.
- **Motivo:** el proyecto lo trabaja una sola persona; el CI agrega configuración y minutos sin un
  beneficio claro para la entrega.
- **Consecuencias:** el repo no tiene un check remoto; el README explica cómo correr lint y tests;
  `pyproject.toml` centraliza la config de `ruff` y `pytest`.
- **Fecha:** 2026-10-27

---

## D-038 · Documentación: idioma y alcance

- **Tarea:** T-072
- **Estado:** decidida
- **Opciones:** documentación en español / README en inglés / bilingüe; solo dev / dev + prod
- **Decisión:** el README y la documentación de uso se escriben en español, igual que el backlog y
  `docs/design.md`. El código, los identificadores y los comentarios siguen en inglés. El README
  documenta **solo desarrollo local**: requisitos, `uv sync`, `.env`, `alembic upgrade head`,
  `seed.py`, `run.ps1` y runbook de errores comunes. No se documenta despliegue.
- **Motivo:** el proyecto y su documentación ya están en español; un README en inglés dejaría dos
  criterios de idioma conviviendo. El camino de producción todavía no está probado (T-001), así que
  documentarlo sería prometer algo que no funciona.
- **Consecuencias:** `readme.txt` se reemplaza por un `README.md` único en español; no hay versión
  en inglés; la sección de producción se agrega recién cuando T-001 esté cerrada y verificada.
- **Fecha:** 2026-10-27

---

## D-039 · Secreto de MySQL expuesto en el repo público

- **Tarea:** T-073, T-002, T-003
- **Estado:** decidida (deuda aceptada)
- **Opciones:** rotar + limpiar historial / rotar y sacar del archivo actual / no hacer nada
- **Decisión:** se rota la contraseña de MySQL y se saca de `alembic.ini`; `alembic/env.py`,
  `rxconfig.py` y `conect_db.py` leen `DATABASE_URL` desde `.env` (D-011). **No** se reescribe el
  historial de git: el secreto viejo sigue visible en los commits, pero deja de ser válido.
- **Motivo:** rotar el secreto es lo que realmente reduce el riesgo; reescribir el historial
  obliga a un force-push y a invalidar todos los clones, y el usuario decidió no hacerlo.
- **Riesgos:** `github.com/dalitus/proyectofinal-practica` es público desde febrero de 2026 y
  `alembic.ini:87` contenía la clave de `root` en texto plano. Cualquiera puede leer la clave
  vieja, así que la rotación debe hacerse antes de exponer cualquier instancia MySQL. La deuda
  queda registrada acá y en T-073.
- **Consecuencias:** `.gitignore` en UTF-8 e incluye `.env`, `credentials.json`, `token.json`,
  `.states/` y `.web/`; `.env.example` sin valores reales; el runbook de instalación (T-072)
  documenta cómo crear la clave y cargarla en `.env`.
- **Fecha:** 2026-10-27

---

## D-040 · Convención de nombres de archivo

- **Tarea:** T-075
- **Estado:** decidida
- **Opciones:** dominio español + capa en inglés / todo en inglés / todo en español
- **Decisión:** los módulos Python se nombran en español, dominio **y** sufijo de capa:
  `producto_modelo.py`, `producto_repositorio.py`, `producto_servicio.py`, `carrito_estado.py`,
  `producto_pagina.py`, `base_de_datos.py`. Las carpetas de capa (`model/`, `repository/`,
  `service/`, `state/`, `pages/`) **no** cambian, y los nombres deben estar bien escritos y
  describir la función real del módulo.
- **Motivo:** el vocabulario del negocio y de la UI ya es español; traducir el dominio a inglés
  dejaría dos nombres para el mismo concepto y obligaría a traducir mentalmente en cada import.
- **Consecuencias:** `AGENTS.md` deja de exigir identificadores en inglés para nombres de archivo
  (sigue exigiéndolo para el resto del código); T-075 corre al final, después de T-005, T-013,
  T-019, T-060 y T-061, para no renombrar archivos que esas tareas eliminan o fusionan.
- **Fecha:** 2026-10-27

---

## D-041 - Contraste lienzo/tarjeta y modo claro obligatorio

- **Tarea:** T-063
- **Estado:** decidida
- **Opciones:** fondo blanco con borde de 1px / fondo gris con tarjetas blancas / sombras
- **Decisión:** la app se pinta con el token `page` (`#F7F7F5`) y las tarjetas con `card`
  (`#FFFFFF`) más borde `border` (`#E5E5E5`). Se elimina el `box_shadow` de las tarjetas y se
  reemplazan los hex sueltos (`#f0f0f0`, `#e6e6e6`, `white`) por tokens. La UI no tiene variante
  oscura: `default_color_mode="light"` en `rxconfig.py` y un script en `head_components` que fija
  `light` en `localStorage` antes de hidratar.
- **Motivo:** con fondo y tarjeta ambos blancos el bloque no se distinguía; el borde solo no
  alcanzaba. Además, un sistema operativo en modo oscuro activaba la paleta oscura de Radix y el
  texto (`--gray-12`) quedaba casi blanco sobre blanco.
- **Consecuencias:** `docs/design.md` documenta `page`/`card` y la regla de modo claro. Cualquier
  pantalla nueva debe usar `COLORS["page"]` en el contenedor y `COLORS["card"]` en las tarjetas.
  Si algún día se quiere modo oscuro, hay que tokenizar los colores de texto antes de habilitarlo.
- **Fecha:** 2026-10-27

---

## D-042 · Usuario de MySQL dedicado en vez de rotar `root`

- **Tarea:** T-073
- **Estado:** decidida
- **Opciones:** rotar la clave de `root` / crear un usuario `zapateria_app` con permisos acotados /
  no rotar
- **Decisión:** se crea el usuario `zapateria_app` con clave aleatoria, permisos `SELECT, INSERT,
  UPDATE, DELETE, CREATE, DROP, ALTER, INDEX, REFERENCES` sobre `zapateria_db` y `zapateria_test`,
  y `DATABASE_URL` en `.env` pasa a usarlo. La clave de `root` **no** se toca.
- **Motivo:** D-039 pedía rotar, pero la app venía conectando como `root`, así que rotar esa clave
  cambia el acceso de **toda** la instancia local de MySQL y puede romper otros proyectos sin que
  nadie lo note. Un usuario dedicado logra el mismo objetivo de seguridad (la clave filtrada deja
  de servir para este proyecto) con blast radius mínimo y principio de menor privilegio.
- **Consecuencias:** la clave vieja de `root` sigue siendo válida en la instancia local, pero ya no
  es la que usa la app y no da acceso a través del proyecto. `.env.example` documenta `USUARIO` /
  `PASSWORD` genéricos. Si se recrea la DB desde cero hay que volver a correr el `GRANT`.
- **Fecha:** 2026-10-28

---

## D-043 · Paquete Python `app` en lugar de `proyectofinal`

- **Tarea:** T-075 (prerrequisito)
- **Estado:** decidida
- **Opciones:** dejar `proyectofinal/` / renombrar a `app/` / renombrar a `zapateria/`
- **Decisión:** el paquete pasa de `proyectofinal/` a `app/`, con el módulo de entrada en
  `app/app.py` y `app_name="app"` en `rxconfig.py`. El nombre de la distribución en
  `pyproject.toml` (`proyectofinal-practica`) queda como está: no lo importa nadie.
- **Motivo:** Reflex exige que `app_name` sea el nombre del paquete y que exista
  `<app_name>/<app_name>.py`. Con el nombre viejo quedaba `proyectofinal/proyectofinal.py`, es decir
  paquete y repo con el mismo nombre y un módulo de entrada que no dice qué hace. `app` es la
  convención del framework. Se descartó `zapateria/` porque `AGENTS.md` define el proyecto como
  indumentaria **y** calzado, y el nombre encasillaría.
- **Consecuencias:** el renombre tocó 158 referencias en 54 archivos de código y config, más los
  docs que citaban rutas (`AGENTS.md`, `HANDOFF.md`, backlog, `design.md`). Es puramente mecánico:
  `git blame` se ensucia en las líneas de import. `docs/HANDOFF.md` y los docs de esta rama citan
  `app/`; `wip/baseline` sigue con `proyectofinal/` porque ahí el renombre no existe todavía, así
  que esas ediciones **no** se cherry-piquean hasta el merge.
- **Fecha:** 2026-10-28

---

## D-044 · Página de registro propia en vez de la del plugin

- **Tarea:** T-022 / T-061
- **Estado:** decidida
- **Opciones:** usar `/register` del plugin / escribir la página propia / heredar
  `RegistrationState` y pisar `_register_user`
- **Decisión:** `/register` es una página nuestra (`app/pages/registro_pagina.py` +
  `app/state/registro_estado.py`) que llama a `service/auth_servicio.registrar_comprador`. `/login`
  sigue siendo la del plugin, montada con `add_page`.
- **Motivo:** `reflex_local_auth.registration.RegistrationState._register_user` crea `LocalUser`
  directo con `rx.session()` y nunca crea `UserProfile`. Verificado en el navegador contra
  `zapateria_db`: el alta dejaba `localuser` con fila y `user_profiles` vacía. Como el perfil es la
  tabla de la que cuelgan el rol, los pedidos y las consultas, toda cuenta creada por esa página
  quedaba inservible. Heredar y pisar `_register_user` obliga a monkeypatchear la clase que usan
  los componentes del plugin, así que se descartó.
- **Consecuencias:** la lógica de alta queda en una sola función (`registrar_comprador`) y la
  página es solo maquetación. `LocalAuthState` sigue siendo el dueño de la sesión. Si el plugin
  cambia de versión, `/login` puede romperse pero el alta no depende de él. Efecto secundario
  detectado: editar `app/app.py` con la página nueva registrada y la del plugin todavía montada
  rompe el compile con `RouteValueError` (dos páginas en `/register`), así que el reemplazo tiene
  que entrar en un solo commit.
- **Fecha:** 2026-10-28

---

## D-045 · Estados de UI en un stylesheet generado desde los tokens

- **Tarea:** T-063
- **Estado:** decidida
- **Opciones:** estilos inline por componente / Radix Themes con `color_scheme` / clases propias en
  un stylesheet alimentado por `tokens.py`
- **Decisión:** los primitivos se construyen sobre `rx.el` (button, input, div) con clases `ui-*`, y
  todos los estados (`:hover`, `:focus-visible`, `[disabled]`, `[aria-invalid]`, media queries) viven
  en `app/ui/styles.py`, que emite los tokens como variables CSS y se inyecta una sola vez desde
  `app/app.py`. Se agrega `Alert` al inventario de primitivos (informativo, en línea).
- **Motivo:** el prop `style` de Reflex se serializa a estilo inline, así que no puede expresar
  pseudo-clases ni `@media`: sin un stylesheet, "hover y focus visibles" era imposible de cumplir
  sin tocar Radix. Radix Themes trae su propia paleta y su `color_scheme`, que `docs/design.md` 2.1
  prohíbe, y su reset `.rt-reset:where(:focus){outline:none}` compite con el foco de 2px. Los
  elementos HTML con clases propias dejan un único lugar donde se define cada estado y un
  `Alert` en línea para los mensajes de página (el error de campo sigue yendo junto al campo).
- **Consecuencias:** una variante nueva se agrega en `primitives.py` **y** en `styles.py`, nunca en
  la página; el stylesheet se hereda en todas las rutas porque se monta en el `App`; los elementos
  no heredan estilos de Radix, así que cada uno declara `font-family` y `color` desde los tokens.
  El foco usa selectores de clase (especificidad 0,2,0) para ganarle a resets de terceros.
- **Fecha:** 2026-10-28

---

## D-046 · Drawer y ConfirmDialog sobre los primitivos de Reflex

- **Tarea:** T-063
- **Estado:** decidida
- **Opciones:** reimplementar overlay + focus trap + Escape a mano / usar `rx.drawer` (Vaul) y
  `rx.alert_dialog` (Radix) y vestirlos con las clases propias
- **Decisión:** `Drawer` usa `rx.drawer` y `ConfirmDialog` usa `rx.alert_dialog`. El look lo pone
  `app/ui/styles.py`; la semántica (`role="alertdialog"`, foco atrapado, cierre con Escape y con
  click afuera) la pone la librería. `Toast` no es un componente: devuelve el `EventSpec` de
  `rx.toast` para usarse desde un handler (T-064).
- **Motivo:** un drawer con focus trap bien hecho no es un `<div>` con `position: fixed`; es la
  parte que más se rompe con teclado y lectores de pantalla. Vaul y Radix ya resuelven eso y vienen
  con Reflex, así que reimplementarlo era cambiar código probado por código propio sin tests.
- **Consecuencias y trampas verificadas en el navegador:**
  - `DrawerContent` de Reflex fija `inset: 0` y `background: rgba(0,0,0,.5)` en el overlay, así que
    las reglas del panel y del scrim llevan prefijo `body` (especificidad 0,1,1) para ganarles; el
    lado lo decide `direction` en el `Root`, no el CSS.
  - `AlertDialog.Action`/`Cancel` usan `asChild`: hay que pasarles **un** elemento, y ese elemento es
    el `Button` propio. Sin `as_child=False` explícito, un `as_child=True` termina en `css` y rompe
    el render.
  - Ambos viven en un portal fuera de `.ui-shell`, así que no heredan tipografía: el
    `font-family` se declara en sus propias clases.
- **Fecha:** 2026-10-28

---

## D-047 · Catálogo: marca, umbral de stock y dónde viven los filtros

- **Tarea:** T-030, T-033
- **Estado:** decidida
- **Opciones:** un `select` de marca aparte / buscar la marca con el mismo campo de texto
- **Decisión:**
  - La búsqueda por texto cubre **nombre y marca** con el mismo campo. No hay `select` de marca.
  - `StockBadge`: "Sin stock" con 0 unidades; "Ultimas N" cuando el total de unidades es 1 a 3;
    "Disponible" desde 4. El umbral es `UMBRAL_ULTIMAS_UNIDADES = 3` y cuenta la suma de todas las
    variantes del producto, no cada variante por separado.
  - Filtros, orden y página viven en `CatalogoEstado`, **no** en la URL. La sincronización con la
    URL queda para T-061.
- **Motivo:** `docs/design.md` 4.3 proponía un filtro de marca separado, pero D-014 ya cerró la
  barra como texto/categoría/talle/color y una marca por producto suele tener pocos valores
  distintos: un `select` más agranda la barra sin agregar precisión. Para el stock, "últimas
  unidades" tiene que significar algo para el comprador; 3 unidades totales es el punto donde
  todavía puede decidir. Los filtros en el estado evitan reescribir la página cuando T-061 defina
  las rutas únicas.
- **Consecuencias:** el repositorio resuelve el texto con `nombre ILIKE ... OR marca ILIKE ...`; el
  servicio devuelve `stock_estado` y `stock_etiqueta` ya resueltos para que la página no compare
  números. Al no estar en la URL, recargar la página vuelve al catálogo sin filtros y el link no es
  compartible: eso se corrige en T-061.
- **Fecha:** 2026-10-28

