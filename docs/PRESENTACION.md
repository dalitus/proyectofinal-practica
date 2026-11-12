# Calzado Fermin — guía para la presentación

Tienda online de calzado con dos actores: **comprador** y **administrador**.
Todo el sistema está escrito en Python: una sola base de código para la pantalla y el servidor.

---

## 1. Tecnologías (lo que digo de memoria)

| Pieza | Qué es |
|---|---|
| **Reflex** | Framework full-stack en Python: el estado vive en el servidor y la UI se genera en React. |
| **MySQL 8** | Base de datos única de la tienda. |
| **SQLModel / SQLAlchemy** | Modelos y consultas tipadas. |
| **Alembic** | Migraciones versionadas del esquema. |
| **Reflex Local Auth** | Registro, login y sesión con token. |
| **Lucide** | Set de iconos del header. |
| **pytest + ruff** | 292 tests y lint/formato automático en cada commit. |

**Idea para decir:** "No hay dos proyectos: Python atiende la lógica y Reflex arma la interfaz."

---

## 2. Arquitectura en una línea

```
model → repository → service → state → pages
```

- **model:** las tablas.
- **repository:** las consultas SQL.
- **service:** las reglas del negocio (stock, totales, permisos).
- **state:** el estado de cada pantalla.
- **pages:** solo composición visual.

**Regla de oro:** una capa solo habla con la de al lado. La página nunca toca la base y el estado
nunca abre una conexión.

---

## 3. Flujos principales

### Comprador
1. **Catálogo** con búsqueda, filtros y detalle del producto.
2. **Se registra o inicia sesión** (comprar exige cuenta).
3. **Agrega al carrito** una variante concreta: color + talle.
4. El **badge del header** muestra cuántas unidades lleva, sin recargar.
5. **Checkout:** revisa el total y los datos de contacto. No hay pago online: el pedido queda
   registrado y el envío se coordina después.
6. Al confirmar se **descuenta el stock** y se genera el **pedido**. Si se cancela, el stock vuelve.
7. Puede seguir sus **pedidos** y hacer **consultas**.

### Administrador
1. Entra al **panel** (solo con rol admin).
2. Gestiona **productos, stock, pedidos y consultas**.
3. Puede **editar o dar de baja** un producto, pero no comprar.

---

## 4. Decisiones técnicas que conviene nombrar

1. **Comprar requiere cuenta.** No hay carrito de invitado: el carrito es del usuario en la base.
2. **El stock es por variante** (producto + color + talle), no por producto.
3. **El tope del carrito es el stock real**, no un máximo inventado.
4. **Los totales se calculan una sola vez** en el servicio: carrito, checkout y pedido muestran
   siempre el mismo número.
5. **El administrador no compra** (se rechaza también en el servidor, no solo en la pantalla).
6. **Los permisos se verifican en el servidor**: esconder un botón no es seguridad.
7. **El contador del carrito sale de una suma en la base**, no de una variable del navegador.
8. **Sistema de diseño propio**: tokens de color/espaciado y componentes reutilizables.

---

## 5. Guion corto para la demo (3 minutos)

1. Entrar como **comprador** y mostrar el catálogo con filtros.
2. Abrir un producto, elegir color y talle, **agregar al carrito**.
3. Señalar el **badge** del header y sumar otra unidad: cambia sin recargar.
4. Ir al carrito, mostrar subtotal y **finalizar la compra**.
5. Ver el **pedido** en "Mis pedidos".
6. Entrar como **admin**: panel, edición de stock y cambio de estado de un pedido.
7. Cerrar con la arquitectura por capas y los tests en verde.

---

## 6. Preguntas probables

- **¿Por qué Reflex?** Un solo lenguaje y un solo repositorio; el estado ya vive en el servidor.
- **¿Dónde está la seguridad?** En el servicio y en el estado del servidor: cada acción valida rol y
  dueño de los datos.
- **¿Qué pasa si no hay stock?** El servicio rechaza la operación y explica qué variante falta.
- **¿Cómo se prueba?** Tests de servicios y repositorios contra una base de test, más validaciones
  de accesibilidad, capas y estilo.
