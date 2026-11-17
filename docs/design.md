# Sistema de diseño — Tienda

**Objetivo:** una UI simple, intuitiva y sin ruido visual. Este documento es la referencia
obligatoria para todo el desarrollo de interfaz. Si una pantalla no cumple estas reglas, no está
terminada.

**Referencias visuales:** [SaaS Starter](https://reflex.dev/templates/saas-starter/) (vidriera),
[Order Management System](https://reflex.dev/templates/order-management-system/) (pedidos),
[Retail Inventory Manager](https://reflex.dev/templates/retail-inventory-manager/) (productos/stock).
No se copian estilos: se copian **patrones de layout**.

**Estado:** v1 — 2026-10-27.

---

## 1. Principios

1. **Una decisión por pantalla.** Catálogo = elegir producto. Detalle = elegir talle.
   Carrito = revisar. Checkout = pagar. Si una pantalla pide dos decisiones, se parte.
2. **Jerarquía por tamaño y espacio, no por color.** El color se reserva para acción y estado.
3. **Un solo acento.** Fondo neutro, texto oscuro, un acento. Nada más.
4. **Borde en lugar de sombra.** `1px solid` reemplaza `box-shadow`.
5. **Cuatro estados por componente:** normal, hover/focus, vacío, error. Sin excepción.
6. **Mobile primero.** Si no entra en 360px, no está terminado.

---

## 2. Tokens

### 2.1 Color

| Token | Valor | Uso |
|---|---|---|
| `page` | `#EBF2FA` | Fondo de la aplicación (el lienzo), con un celeste tenue |
| `card` | `#FFFFFF` | Fondo de tarjetas, tablas y bloques de contenido |
| `bg` | `#FFFFFF` | Alias histórico de `card` |
| `surface` | `#F7F7F5` | Inputs, header de tabla, zonas de imagen |
| `border` | `#E5E5E5` | Bordes de card, input, tabla |
| `text` | `#111111` | Texto principal |
| `muted` | `#6B6B6B` | Metadatos, labels secundarios |
| `accent` | `#111111` | Botón primario, link activo |
| `accent_text` | `#FFFFFF` | Texto sobre acento |
| `danger` | `#B42318` | Solo error y acción destructiva |
| `success` | `#067647` | Solo stock disponible / pedido entregado |

**Prohibido:** fondos de color saturados (`#ADD8E6` es el ejemplo de lo que no se usa, no un
valor válido), `color_scheme` de Radix sin criterio, más de un color de acento activo por
pantalla. El único fondo con tinte es `page`, y siempre como token del sistema (D-053).

**Contraste lienzo/tarjeta:** la app se pinta con `page` y cada tarjeta con `card` + borde de
`border`. El bloque blanco se despega del lienzo celeste sin necesidad de sombra: 1.13:1 entre
ambos, y el texto `muted` conserva 4.72:1 sobre el lienzo. Nunca dos superficies del mismo color
encimadas.

**Modo claro obligatorio:** la UI no tiene variante oscura. `rxconfig.py` fija
`default_color_mode="light"` y el `App` fuerza `light` en `localStorage` antes de hidratar, así
un sistema operativo en modo oscuro no pinta texto claro sobre fondos claros.

### 2.2 Tipografía

- **Familia única:** Inter (fallback `system-ui`).
- **Pesos:** `400` (cuerpo) y `600` (títulos y precios). Nada de `700+`.
- **Escala:**

| Rol | Tamaño | Peso | Line-height |
|---|---|---|---|
| `display` | 32px | 600 | 1.2 |
| `h1` | 24px | 600 | 1.3 |
| `h2` | 18px | 600 | 1.4 |
| `body` | 16px | 400 | 1.5 |
| `small` | 14px | 400 | 1.5 |
| `caption` | 12px | 400 | 1.4 |

### 2.3 Espaciado, radios y sombras

- **Escala de espacio:** `4 · 8 · 16 · 24 · 32 · 48 · 64`. Solo esos valores.
- **Radios:** `8px` cards · `6px` inputs y botones · `full` chips y badges.
- **Sombras:** ninguna por defecto. Excepción permitida: `0 1px 2px rgba(0,0,0,0.06)` en
  elementos flotantes (drawer, popover, resumen sticky).
- **Bordes:** `1px solid border`.

---

## 3. Layout

```
AppShell
├── TopNav        (64px, sticky, border-bottom)
│   logo · buscador · carrito (n) · cuenta
├── Main          (max-width 1200px, padding 24px, margin auto)
└── Footer        (mínimo, 1 línea, texto muted)
```

- **Grillas por página:**

| Página | Columnas desktop | Tablet | Mobile |
|---|---|---|---|
| Catálogo | `repeat(4, 1fr)` | `2` | `1` |
| Detalle | `3fr 2fr` | `1fr` | `1fr` |
| Carrito | `2fr 1fr` (resumen sticky) | `1fr` | `1fr` |
| Admin | tabla full-width + filtros arriba | igual | tabla con scroll horizontal |

- **Contenedor de lectura:** texto de párrafo nunca supera `65ch`.
- **Separación vertical entre bloques:** `32px`; dentro de un bloque, `16px`.

---

## 4. Componentes

Cada componente vive en `app/ui/<nombre>.py` y se exporta desde
`app/ui/__init__.py`. Ninguna página define estilos inline propios: usa estos.

### 4.1 Estructura

| Componente | Responsabilidad | Estados |
|---|---|---|
| `AppShell` | Nav + main + footer | — |
| `TopNav` | Logo, buscador, carrito, cuenta | logueado / invitado |
| `Container` | Ancho máximo y padding | — |
| `PageHeader` | Título + subtítulo + acciones | — |
| `Footer` | Una línea | — |

### 4.2 Primitivos

| Componente | Variantes | Estados |
|---|---|---|
| `Button` | `primary` `secondary` `ghost` `danger` | normal, hover, focus, disabled, loading |
| `Input` | texto, email, número | normal, focus, error, disabled |
| `Select` | — | normal, focus, error |
| `SizeChip` | seleccionado / no | normal, selected, disabled (sin stock) |
| `Badge` | `stock` `pedido` | según valor |
| `Card` | — | normal, hover (solo si es clickeable) |
| `EmptyState` | — | título, texto, acción opcional |
| `Alert` | `info` `success` `error` | normal (mensaje en línea, no reemplaza el error de campo) |
| `Skeleton` | línea, bloque, card | — |
| `Toast` | éxito, error | devuelve el evento de `rx.toast`; se usa desde handlers |
| `Drawer` | edición lateral | abierto, cerrado |
| `ConfirmDialog` | acción destructiva | abierto, cerrado |

### 4.3 Dominio

| Componente | Contenido | Reglas |
|---|---|---|
| `ProductCard` | imagen 3:4, nombre (2 líneas), precio, `StockBadge`, CTA | un solo CTA primario |
| `ProductGrid` | grilla responsive | renderiza `Skeleton` × 8 al cargar |
| `PriceTag` | precio formateado ARS | `Decimal`, separador de miles |
| `StockBadge` | `Disponible` / `Últimas N` / `Sin stock` | color solo en el punto, texto en `muted` |
| `SizePicker` | chips de talle | deshabilita sin stock |
| `QuantityStepper` | − / n / + | tope = stock disponible |
| `CartLine` | miniatura, nombre, talle, precio, stepper, quitar | quitar es `ghost` |
| `OrderSummary` | subtotal, envío, total, CTA | sticky en desktop |
| `AddressForm` | campos de entrega | error por campo |
| `OrdersTable` | pedidos con `Badge` de estado | búsqueda + filtro |
| `ProductsTable` | productos con stock | edición en `Drawer` |

---

## 5. Patrones por página

### Catálogo (`/`)
1. `PageHeader` con título y contador de resultados.
2. Barra de búsqueda + filtros (marca, categoría, talle, color) en una sola fila.
3. `ProductGrid`. Click en card → detalle. CTA secundario "Agregar" solo si está logueado.
4. Invitado que agrega → redirect a login con retorno (ver `docs/backlog/EPIC-03`).

### Detalle (`/producto/[id]`)
1. Imagen grande a la izquierda (proporción 3:4, fondo `surface`).
2. Info a la derecha: marca, nombre, precio, `SizePicker`, `StockBadge`, CTA primario.
3. Nada de descripción larga arriba: va debajo de la línea de compra.

### Carrito (`/carrito`)
1. Lista de `CartLine`.
2. `OrderSummary` sticky.
3. Un único CTA: `Ir a pagar`.
4. Vacío → `EmptyState` con acción "Ver catálogo".

### Checkout (`/checkout`)
1. Una página, dos bloques: `AddressForm` + `OrderSummary` sticky.
2. Sin wizard de varios pasos.
3. Errores junto al campo, nunca en toast.

### Admin (`/admin_dashboard`)
1. `PageHeader` + tabs (Productos · Pedidos · Consultas).
2. Filtros arriba, tabla abajo, paginación al pie.
3. Alta/edición en `Drawer`; borrado con `ConfirmDialog`.

---

## 6. Reglas de interacción

- **Un CTA primario por vista.** El resto `secondary` o `ghost`.
- **Área de click mínima 44px** (incluye padding, no solo el texto).
- **Focus visible:** `outline: 2px solid accent; offset: 2px`. Nunca `outline: none` sin reemplazo.
- **Errores junto al campo**, con texto en `danger` y `caption`.
- **Navegación máximo 2 niveles** desde catálogo a compra.
- **Loading:** skeleton con la forma del contenido. Prohibido spinner de página completa.
- **Confirmación:** solo para acciones destructivas. Nada de "¿estás seguro?" en navegación.
- **Copy:** sentence case, sin signos de exclamación, sin emojis.

---

## 7. Accesibilidad

- Contraste mínimo **AA** (4.5:1 texto normal, 3:1 texto grande).
- Toda imagen con `alt`; decorativas con `alt=""`.
- Todo input con `label` visible (no placeholder como label).
- Navegación completa por teclado; `Tab` en orden lógico.
- Estados no comunicados solo por color: siempre texto o ícono además.

---

## 8. Do / Don't

| ✅ Hacer | ❌ Evitar |
|---|---|
| Fondo blanco, card con borde | Fondo `#ADD8E6`, card con sombra |
| Botón negro, uno por pantalla | Botones azules/grises mezclados |
| Precio en `600` y 18px | Precio con `font-size="md"` genérico |
| Imagen 3:4 con `object-fit: cover` | `object-fit: contain` con fondo aleatorio |
| `Skeleton` al cargar | `rx.spinner` de pantalla completa |
| Grid responsive con `minmax` | Cards de `220px` fijos en `hstack` |
| Texto plano en botones | `👤 Perfil`, `🔒 Login` |
| Tokens centralizados | Hex sueltos en cada página |

---

## 9. Implementación

### 9.1 Estructura de archivos

```
app/
└── ui/
    ├── __init__.py        # re-exporta todo
    ├── tokens.py          # colores, espacio, tipografía, radios
    ├── styles.py          # tokens → variables CSS + :hover, :focus-visible y media queries
    ├── layout.py          # AppShell, TopNav, Container, PageHeader, Footer
    ├── primitives.py      # Button, Input, Card, Alert...
    ├── feedback.py        # Skeleton, Toast, Drawer, ConfirmDialog
    └── domain/
        ├── product.py     # ProductCard, ProductGrid, PriceTag, StockBadge, SizePicker
        ├── cart.py        # CartLine, QuantityStepper, OrderSummary
        └── order.py       # OrdersTable, ProductsTable, AddressForm
```

`styles.py` existe porque el prop `style` de Reflex se serializa como estilo inline y no
puede expresar `:hover`, `:focus-visible` ni `@media`. Los valores literales siguen viviendo
solo en `tokens.py`: el stylesheet los emite como variables CSS y las clases las consumen.
Se inyecta una vez desde `app/app.py`, así que toda pantalla lo hereda.

### 9.2 Tokens en código

```python
# app/ui/tokens.py
COLORS = {
    "bg": "#FFFFFF",
    "surface": "#F7F7F5",
    "page": "#EBF2FA",
    "card": "#FFFFFF",
    "border": "#E5E5E5",
    "text": "#111111",
    "muted": "#6B6B6B",
    "accent": "#111111",
    "accent_text": "#FFFFFF",
    "danger": "#B42318",
    "success": "#067647",
}

SPACE = {"xs": "4px", "sm": "8px", "md": "16px", "lg": "24px", "xl": "32px", "2xl": "48px"}
RADIUS = {"card": "8px", "control": "6px", "pill": "9999px"}
TYPE = {"display": {...}, "h1": {...}, "h2": {...}, "body": {...}, "small": {...}, "caption": {...}}
FONT = "'Inter', system-ui, sans-serif"
```

### 9.3 Regla de uso en páginas

```python
# Correcto
from app.ui import ProductGrid, PageHeader

# Prohibido en páginas
rx.box(..., box_shadow="0px 2px 5px rgba(0,0,0,0.06)", background_color="#ADD8E6")
```

Si una página necesita un estilo nuevo, **primero** se agrega como variante del componente.
Nunca se escribe un hex suelto en una página.

---

## 10. Checklist de PR de UI

- [ ] No hay hex, `box_shadow` ni `color_scheme` sueltos en `pages/`.
- [ ] La pantalla usa solo componentes de `app/ui/`.
- [ ] Existen los estados vacío, carga y error.
- [ ] Funciona a 360px, 768px y 1280px.
- [ ] Un solo CTA primario visible.
- [ ] Teclado: se puede completar el flujo sin mouse.
- [ ] Contraste AA verificado en textos sobre `page`, `surface` y `accent`.
- [ ] Sin emojis en la UI.

---

## 11. Decisiones

| Fecha | Decisión | Motivo |
|---|---|---|
| 2026-10-27 | Paleta neutra con acento negro; se elimina `#ADD8E6` | El fondo celeste competía con el producto y no es una referencia de tienda |
| 2026-11-11 | El lienzo (`page`) pasa a celeste tenue `#EBF2FA` | Las tarjetas blancas se despegan mejor del fondo sin que el tinte compita con la foto del producto (D-053) |
| 2026-10-27 | Sin sombras; borde `1px` | Menos ruido, más consistencia entre card, tabla e input |
| 2026-10-27 | Una sola familia tipográfica, dos pesos | La jerarquía se resuelve por tamaño, no por cantidad de fuentes |
| 2026-10-27 | Componentes en `app/ui/`, no en `pages/` | Evita duplicación; `ui_helpers.py` queda obsoleto y se reemplaza |
| 2026-10-27 | Compra solo para usuarios registrados | Cierra T-041 del backlog; el CTA de invitado redirige a login con retorno |
