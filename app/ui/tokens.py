"""Design tokens. Source: docs/design.md.

No page may declare its own colours, spacing or radii: import them from here.
Literal values exist only in this module; ``styles.py`` turns them into CSS
custom properties and components consume the derived classes.
"""

COLORS = {
    "bg": "#FFFFFF",
    "surface": "#F7F7F5",
    # Deliberate contrast: the app paints `page` and cards paint `card`, so the
    # white block separates from the grey canvas without any shadow.
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

# Role -> size / weight / line-height, from docs/design.md 2.2.
TYPE = {
    "display": {"size": "32px", "weight": "600", "line_height": "1.2"},
    "h1": {"size": "24px", "weight": "600", "line_height": "1.3"},
    "h2": {"size": "18px", "weight": "600", "line_height": "1.4"},
    "body": {"size": "16px", "weight": "400", "line_height": "1.5"},
    "small": {"size": "14px", "weight": "400", "line_height": "1.5"},
    "caption": {"size": "12px", "weight": "400", "line_height": "1.4"},
}

FONT = "'Inter', system-ui, sans-serif"
