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

- **Estado:** lista · **Prioridad:** P0 · **Épica:** 03
- **Archivos:** `pages/users_page.py:142-168`, `pages/andmin_page.py`,
  `state/users_state.py:57-97`, `state/catalogo_state.py:89-91`
- **Problema:** login de usuario y de admin están separados y con campos distintos
  (`password` vs `contrasenia`); las redirecciones apuntan a rutas duplicadas; no hay retorno a
  la página original.
- **Decisión (D-018):** login único en `/login`, registro abierto de compradores, sin verificación
  ni recuperación por email.
- **AC propuestos:**
  - [x] Un solo contrato de credenciales (`email` + `password`).
  - [ ] Al loguearse, el usuario vuelve a la página que intentaba ver (o al catálogo).
  - [ ] Errores de credenciales son claros y no revelan si el email existe.
  - [ ] Logout redirige y limpia carrito visible.
  - [x] El registro crea solo compradores; nunca administradores.
  - [x] Sin verificación de email ni recuperación automática.
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

- **Estado:** en curso · **Prioridad:** P0 · **Épica:** 03
- **Archivos:** `app/service/sesion_servicio.py`, `tests/test_sesion_rol.py`, `app/app.py`
  (registro de rutas, todavía sin tocar)
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
- **AC propuestos:**
  - [ ] `on_load` valida sesión y rol en cada ruta protegida.
        **Pendiente:** la guarda existe en el servicio; falta el estado base y las rutas de admin
        (T-051/T-052).
  - [ ] Invitado → login; usuario sin permiso → página 403; admin OK.
        **Pendiente:** falta la página 403 y el registro de rutas en `app/app.py`.
  - [x] La validación es server-side (no solo ocultar botones).
        → `rol()` consulta la base en cada llamada; no hay ninguna var de rol en el cliente.
  - [ ] Tests manuales con URL directa para cada rol.
        **Pendiente:** no hay ruta protegida que probar todavía.
  - [ ] El admin tiene su panel y no ve carrito/checkout.
        **Pendiente:** el panel de admin es T-051/T-052; las páginas viejas se borraron en T-060.
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
