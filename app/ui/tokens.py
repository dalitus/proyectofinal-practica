"""Tokens de diseño. Fuente: docs/design.md.

Ninguna página debe declarar colores, espacios ni radios propios:
se importan desde acá.
"""

COLORS = {
    "bg": "#FFFFFF",
    "surface": "#F7F7F5",
    # Contraste deliberado: la app se pinta en `page` y las tarjetas en
    # `card`, así el bloque blanco se despega del fondo sin sombras.
    "page": "#F7F7F5",
    "card": "#FFFFFF",
    "border": "#E5E5E5",
    "text": "#111111",
    "muted": "#6B6B6B",
    "accent": "#111111",
    "accent_text": "#FFFFFF",
    "danger": "#B42318",
    "success": "#067647",
}

SPACE = {
    "xs": "4px",
    "sm": "8px",
    "md": "16px",
    "lg": "24px",
    "xl": "32px",
    "2xl": "48px",
}

RADIUS = {
    "card": "8px",
    "control": "6px",
    "pill": "9999px",
}

FONT = "'Inter', system-ui, sans-serif"
