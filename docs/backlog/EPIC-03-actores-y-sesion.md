# EPIC 03 — Actores, autenticación y sesión

**Objetivo:** que cada usuario tenga su propia sesión, que las rutas estén protegidas por rol y
que las contraseñas no se guarden en texto plano.

---

## T-020 · Reemplazar `app_globals` por `AuthState` por sesión

- **Estado:** lista · **Prioridad:** P0 · **Épica:** 03
- **Archivos:** `state/app_globals.py:2`, `state/users_state.py:32-92`,
  `state/catalogo_state.py:56`, `state/carrito_state.py:63-185`, `pages/andmin_page.py:18`
- **Problema:** `current_user_id` es una variable global de módulo compartida por todos los
  navegadores. Dos usuarios mezclan carrito/pedidos/consultas y el último login de admin aplica a todos.
- **Decisión (D-019/D-020):** `LocalAuthState` del plugin guarda el usuario autenticado; la
  sesión persiste 7 días en `LocalAuthSession` + `localStorage`; varias sesiones permitidas.
- **AC propuestos:**
  - [x] No existe `app_globals` ni estado de usuario en variables de módulo.
  - [x] La app usa `LocalAuthState` (o un substate) y `UserProfile` para `user_id`, `rol`, `logeado`.
  - [x] Dos sesiones simultáneas (dos navegadores) ven carritos distintos.
  - [x] Logout borra las sesiones del token y limpia el estado de la app.
  - [x] Los demás estados leen la sesión con `await self.get_state(...)`.
  - [x] La sesión persiste 7 días y sobrevive reinicios del servidor.
- **Grill / preguntas abiertas:**
  - Ninguna: cerrado en D-019 y D-020.
- **Depende de:** T-010, T-011

---

## T-021 · Flujo de login/logout/registro y redirecciones

- **Estado:** hecha · **Prioridad:** P0 · **Épica:** 03
- **Archivos:** `app/state/login_estado.py`, `app/state/sesion_estado.py`,
  `app/pages/cuenta_menu.py`, `app/pages/login_pagina.py`
- **Problema:** login de usuario y de admin están separados y con campos distintos
  (`password` vs `contrasenia`); las redirecciones apuntan a rutas duplicadas; no hay retorno a
  la página original.
- **Decisión (D-018):** login único en `/login`, registro abierto de compradores, sin verificación
  ni recuperación por email.
- **AC propuestos:**
  - [x] Un solo contrato de credenciales (`email` + `password`).
  - [x] Al loguearse, el usuario vuelve a la página que intentaba ver (o al catálogo).
        → `?next=` se lee de `router.url` (`app/state/parametros.py`) y solo se aceptan rutas
        internas; verificado a mano: `/admin/pedidos` como invitado → login → vuelve a
        `/admin/pedidos`.
  - [x] Errores de credenciales son claros y no revelan si el email existe.
        → `ErrorDeAcceso.MENSAJE_CREDENCIALES` es el mismo para email inexistente, contraseña
        equivocada y cuenta deshabilitada; verificado en el navegador con un email que no existe.
  - [x] Logout redirige y limpia carrito visible.
        → `SesionEstado.cerrar_sesion` borra la fila de `localauthsession`, vacía `auth_token` y
        llama a `CarritoEstado.limpiar_visible`; verificado: el token queda vacío en
        `localStorage`, la tabla no tiene sesiones de ese usuario y vuelve al catálogo.
  - [x] El registro crea solo compradores; nunca administradores.
  - [x] Sin verificación de email ni recuperación automática.
- **Qué se hizo (2026-10-31, UI de sesión):**
  - `SesionEstado(cuenta)` es una var calculada con la caché del plugin: nombre, rol y bandera de
    sesión, sin que cada página cargue un estado extra. Un token muerto (usuario borrado, sesión
    vencida) cuenta como invitado.
  - `app/pages/cuenta_menu.py` arma el área de cuenta del header: con sesión muestra el nombre, el
    acceso al panel si el rol es admin y "Salir"; sin sesión, "Iniciar sesión" y "Crear cuenta".
    Toda página usa `nav_de_cuenta()`.
  - **Trampa encontrada:** el plugin `do_logout()` borra las filas de la base pero deja el token en
    el navegador (`self.auth_token = self.auth_token`, un no-op). Acá se limpia a mano.
  - **Trampa encontrada:** cada substado de `LocalAuthState` tiene su propia copia de
    `auth_token`; tras el login el header seguía mostrando al usuario anterior hasta el refresco
    de 10 minutos. `LoginEstado.enviar` le pasa el token nuevo a `SesionEstado`.
- **Grill / preguntas abiertas:**
  - Ninguna: cerrado en D-018.
- **Depende de:** T-020

---

## T-022 · Autenticación con `reflex-local-auth`

- **Estado:** hecha · **Prioridad:** P0 · **Épica:** 03
- **Archivos:** `service/auth_servicio.py`, `model/perfil_modelo.py`, `tests/test_auth_servicio.py`
- **Problema:** las contraseñas se guardan y comparan en texto plano; no hay token de sesión ni
  hashing.
- **Decisión (D-019/D-020):** `reflex-local-auth` para todos; `LocalUser` + `UserProfile`;
  sesión persistente 7 días.
- **AC propuestos:**
  - [x] Contraseñas hasheadas con bcrypt y verificación con el hash (`LocalUser`).
  - [x] No se puede leer el hash desde la API/estado (`model_dump` lo oculta).
  - [x] Sesión persistida en `LocalAuthSession` con token en `localStorage` y vencimiento 7 días.
  - [x] No hay contraseñas en texto plano ni migración de hashes (la DB se recrea).
  - [x] `reflex-local-auth` convive con Reflex 0.10.1 y Pydantic 2 (smoke test).
  - [x] Registro propio crea `LocalUser` + `UserProfile` en una transacción.
- **Verificación del spike (2026-10-28, rama `spike/local-auth`):**
  - `uv add reflex-local-auth==0.5.0` resolvió sin conflictos sobre Reflex 0.10.1 / Pydantic 2.14.1
    (agrega `bcrypt==5.0.0`). `reflex compile --dry` → `Success` con las páginas `/login` y
    `/register` del plugin montadas.
  - Registro real desde el navegador: `localuser` quedó con `username=spike@example.com`,
    `enabled=1` y hash `$2b$12$…`. Login real: `localauthsession` creó la fila con vencimiento a
    7 días y el token quedó en `localStorage` como `_auth_token`.
  - `LocalUser` hereda de `SQLModel` (no de `rx.Model`) y expone `hash_password()` / `verify()`:
    no arrastra la deprecación de `reflex.Model`.
  - No verificado en el spike: logout desde UI y `require_login` (necesitan el `AuthState` propio
    y las páginas nuevas; es la Fase 4-5).
- **Verificación del registro propio (2026-10-28, `wip/esquema`):**
  - `service/auth_servicio.py:registrar_comprador` normaliza el email, exige 8 caracteres de
    contraseña y crea `LocalUser` (`username` = email, `enabled=True`, hash bcrypt) más
    `UserProfile` con `is_admin=False` en una sola transacción; si el email se repite, hace
    `rollback` y no deja filas huérfanas.
  - `tests/test_auth_servicio.py` (8 casos) verifica hash/verify, que `model_dump()` no exponga
    el hash, email duplicado con distinta capitalización, datos inválidos y que el alta pública
    nunca cree un admin. Corren contra `zapateria_test`.
- **Corrección (2026-10-28, `wip/esquema`):** el AC "registro propio crea `LocalUser` +
  `UserProfile` en una transacción" estaba marcado por el **servicio**, pero la UI seguía montando
  la página `/register` del plugin. `RegistrationState._register_user` crea `LocalUser` por su
  cuenta y **no** toca `UserProfile`: un registro desde el navegador dejaba la cuenta sin perfil
  (verificado: `localuser` con fila, `user_profiles` vacía, 1 huérfano). Se agregó
  `app/pages/registro_pagina.py` + `app/state/registro_estado.py`, que llaman a
  `registrar_comprador()`, y se dejó de montar la página del plugin. Verificado en el navegador:
  alta real → dos filas, `localuser sin perfil = 0`; login con esa cuenta → token y redirect a `/`.
- **Grill / preguntas abiertas:**
  - Ninguna: cerrado en D-019 y D-020.
- **Depende de:** T-021

---

## T-023 · Guardas de rutas por rol

- **Estado:** hecha · **Prioridad:** P0 · **Épica:** 03
- **Archivos:** `app/service/sesion_servicio.py`, `tests/test_sesion_rol.py`,
  `app/state/admin_estado.py`, `app/pages/no_autorizado_pagina.py`, `app/app.py`
- **Problema:** cualquier visitante puede abrir las rutas del admin por URL. Las páginas de usuario
  no exigen login de forma consistente.
- **Decisión (D-021):** invitado → login con `redirect_to`; sin permiso → 403; chequeo server-side.
- **Qué se hizo (2026-10-30, backend):**
  - `sesion_servicio.rol(token)` devuelve `invitado`, `comprador` o `admin` leyendo el token vivo y
    el perfil en cada llamada (no se confía en una var del cliente).
  - `es_admin(token)` y `usuario_con_rol(token, *roles)` son la guarda que van a usar los estados:
    devuelven el id cuando el rol está permitido y `None` cuando hay que redirigir.
  - Un `LocalUser` sin fila en `UserProfile` cuenta como comprador: nunca se deduce admin de la
    ausencia de perfil.
  - `tests/test_sesion_rol.py` (8 tests): sin token, token desconocido, sesión vencida, comprador,
    admin, guarda por rol, guarda sin roles y cuenta sin perfil.
- **Qué se hizo (2026-10-31, UI y guardas):**
  - `AdminEstado` es la base de las cuatro pantallas del panel: `_iniciar` resuelve el rol antes de
    pintar y `_exigir_admin` se repite en cada acción que escribe (cambiar estado, responder,
    eliminar), así una sesión vencida con la página abierta no puede operar.
  - **Trampa encontrada:** en Reflex un `EventHandler` heredado queda atado a la clase que lo
    define (`EventHandler.state`). El `on_load` de la base corría sobre una instancia de
    `AdminEstado` y llamaba al `_cargar` base (`NotImplementedError`); el detalle quedaba vacío.
    Cada subclase declara su `on_load`/`reintentar` sobre `_iniciar`. `tests/test_arquitectura.py`
    lo verifica sobre el AST.
  - Invitado → `/login?next=<ruta>`; comprador → `/403`; admin → la pantalla. Verificado a mano con
    las tres cuentas.
  - El header del panel no muestra el carrito (`nav_de_cuenta(cart=False)`) y sí el acceso a las
    secciones y el "Salir" de T-021.
- **AC propuestos:**
  - [x] `on_load` valida sesión y rol en cada ruta protegida.
        → `AdminEstado._iniciar`, declarado en `PedidosAdminEstado`, `PedidoAdminEstado`,
        `ConsultasAdminEstado` y `ConsultaAdminEstado`.
  - [x] Invitado → login; usuario sin permiso → página 403; admin OK.
        → verificado en el navegador: invitado en `/admin/pedidos` termina en
        `/login?next=/admin/pedidos`; el comprador demo en `/403`; el admin ve el listado.
  - [x] La validación es server-side (no solo ocultar botones).
        → `rol()` consulta la base en cada llamada; no hay ninguna var de rol en el cliente.
  - [x] Tests manuales con URL directa para cada rol.
        → las tres cuentas sobre `/admin/pedidos` y `/admin/pedidos/1`.
  - [x] El admin tiene su panel y no ve carrito/checkout.
        → `/admin/pedidos`, `/admin/pedidos/[id]`, `/admin/consultas`,
        `/admin/consultas/[id]`, sin link al carrito.
- **Nota (corrección 2026-10-30):** los AC de esta tarea estaban marcados `[x]` sobre las páginas
  anteriores al rediseño. Esas páginas ya no existen (T-060), así que hoy no hay ninguna ruta
  protegida: se destildó lo que no se puede verificar en el código actual.
- **Grill / preguntas abiertas:**
  - Ninguna: cerrado en D-021.
- **Depende de:** T-020

---

## T-024 · Cuenta única de administrador y bootstrap

- **Estado:** en curso · **Prioridad:** P1 · **Épica:** 03
- **Archivos:** `seed.py`, `service/auth_servicio.py`, `model/perfil_modelo.py`, `.env.example`
- **Problema:** no hay un proceso claro para crear el admin inicial ni para garantizar que sea único.
- **Decisión (D-013/D-019):** seed idempotente desde `ADMIN_EMAIL`/`ADMIN_PASSWORD`; crea
  `LocalUser` (username = email) + `UserProfile(is_admin=True)`; sin cambio obligatorio en el
  primer login.
- **AC propuestos:**
  - [x] Comando/seed idempotente crea el admin si no existe (credenciales por `.env`).
  - [x] El formulario público no permite crear admins.
  - [ ] No se puede borrar al último admin.
  - [ ] El admin puede cambiar su contraseña.
  - [x] No se fuerza el cambio de contraseña en el primer login.
- **Grill / preguntas abiertas:**
  - Ninguna: cerrado en D-013.
- **Verificación (2026-10-28, `wip/esquema`):** `seed.py` reescrito sobre el esquema nuevo.
  `crear_admin_si_no_existe` es idempotente (segunda corrida devuelve `False` y no duplica) y toma
  las credenciales de `ADMIN_EMAIL`/`ADMIN_PASSWORD`; si faltan, corta con un mensaje claro en vez
  de usar un default. Corrida real contra `zapateria_test`: admin + perfil `is_admin=1`, 6
  categorías, 6 productos y 14 variantes; la segunda corrida no creó nada. Las dos AC pendientes
  necesitan la pantalla de cuenta y el borrado de usuarios, que llegan con el panel del admin.
- **Depende de:** T-011, T-022
