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

- **Estado:** lista · **Prioridad:** P0 · **Épica:** 03
- **Archivos:** `repository/users_repository.py:39-42`, `model/users_model.py:18`,
  `model/gerente_model.py:10`
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
  - [ ] Registro propio crea `LocalUser` + `UserProfile` en una transacción.
    - Pendiente de la Fase 4: el registro propio (con `UserProfile`) todavía no existe; el
      formulario del plugin solo crea `LocalUser`.
- **Verificación del spike (2026-10-28, rama `spike/local-auth`):**
  - `uv add reflex-local-auth==0.5.0` resolvió sin conflictos sobre Reflex 0.10.1 / Pydantic 2.14.1
    (agrega `bcrypt==5.0.0`). `reflex compile --dry` → `Success` con las páginas `/login` y
    `/register` del plugin montadas.
  - Registro real desde el navegador: `localuser` quedó con `username=spike@example.com`,
    `enabled=1` y hash `$2b$12$…`. Login real: `localauthsession` creó la fila con vencimiento a
    7 días y el token quedó en `localStorage` como `_auth_token`.
  - `LocalUser` hereda de `SQLModel` (no de `rx.Model`) y expone `hash_password()` / `verify()`:
    no arrastra la deprecación de `reflex.Model`.
  - No verificado en el spike: logout desde UI, `require_login` y la sincronización del token al
    recargar (necesita un `AuthState` propio que consuma `LocalAuthState`, es la Fase 4).
  - Las tablas `localuser` y `localauthsession` se crearon a mano en `zapateria_db` para la prueba
    y se borraron después: la migración de la Fase 3 las genera.
- **Grill / preguntas abiertas:**
  - Ninguna: cerrado en D-019 y D-020.
- **Depende de:** T-021

---

## T-023 · Guardas de rutas por rol

- **Estado:** lista · **Prioridad:** P0 · **Épica:** 03
- **Archivos:** `proyectofinal/proyectofinal.py:21-33`, `pages/adnmin_shouder_page.py:239`,
  `pages/pedidos_admin_page.py:144`, `pages/consulta_admin_page.py:132`,
  `pages/pedidos_page.py:65`, `pages/carrito_page.py:149`
- **Problema:** cualquier visitante puede abrir `/admin_dashboard`, `/pedidos_admin` y
  `/consulta_admin` por URL. Las páginas de usuario no exigen login de forma consistente.
- **Decisión (D-021):** invitado → login con `redirect_to`; sin permiso → 403; chequeo server-side.
- **AC propuestos:**
  - [x] `on_load` valida sesión y rol en cada ruta protegida.
  - [x] Invitado → login; usuario sin permiso → página 403; admin OK.
  - [x] La validación es server-side (no solo ocultar botones).
  - [ ] Tests manuales con URL directa para cada rol.
  - [x] El admin tiene su panel y no ve carrito/checkout.
- **Grill / preguntas abiertas:**
  - Ninguna: cerrado en D-021.
- **Depende de:** T-020

---

## T-024 · Cuenta única de administrador y bootstrap

- **Estado:** lista · **Prioridad:** P1 · **Épica:** 03
- **Archivos:** `service/users_service.py:80-93`, `seed.py` (nuevo), `model/user_profile.py` (nuevo)
- **Problema:** no hay un proceso claro para crear el admin inicial ni para garantizar que sea único.
- **Decisión (D-013/D-019):** seed idempotente desde `ADMIN_EMAIL`/`ADMIN_PASSWORD`; crea
  `LocalUser` (username = email) + `UserProfile(is_admin=True)`; sin cambio obligatorio en el
  primer login.
- **AC propuestos:**
  - [x] Comando/seed idempotente crea el admin si no existe (credenciales por `.env`).
  - [x] El formulario público no permite crear admins.
  - [x] No se puede borrar al último admin.
  - [x] El admin puede cambiar su contraseña.
  - [x] No se fuerza el cambio de contraseña en el primer login.
- **Grill / preguntas abiertas:**
  - Ninguna: cerrado en D-013.
- **Depende de:** T-011, T-022
