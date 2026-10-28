"""Global stylesheet for the UI primitives.

Reflex cannot express pseudo-classes (``:hover``, ``:focus-visible``) or media
queries through the inline ``style`` prop, so the component states required by
``docs/design.md`` live in a single stylesheet keyed by class name. Component
modules (``layout.py``, ``primitives.py``) only add class names; no page writes
CSS.

Every colour, space and radius is emitted below as a CSS custom property built
from ``app.ui.tokens``: that file stays the only place with literal values.
"""

import reflex as rx

from app.ui.tokens import COLORS, FONT, RADIUS, SPACE, TYPE

_FONT_URL = "https://fonts.googleapis.com/css2?family=Inter:wght@400;600&display=swap"


def _css_vars() -> str:
    """Render the token dicts as ``--color-*``, ``--space-*``... custom properties."""
    lines = []
    for name, value in COLORS.items():
        lines.append(f"  --color-{name.replace('_', '-')}: {value};")
    for name, value in SPACE.items():
        lines.append(f"  --space-{name}: {value};")
    for name, value in RADIUS.items():
        lines.append(f"  --radius-{name}: {value};")
    for name, spec in TYPE.items():
        lines.append(f"  --text-{name}: {spec['size']};")
        lines.append(f"  --leading-{name}: {spec['line_height']};")
    lines.append(f"  --font-ui: {FONT};")
    return "\n".join(lines)


_BASE = """
* { box-sizing: border-box; }

body {
  margin: 0;
  background: var(--color-page);
  color: var(--color-text);
  font-family: var(--font-ui);
}

/* Keyboard focus is visible everywhere; mouse clicks keep the native ring off.
   The class selectors are listed first on purpose: they score (0,2,0) and beat
   third-party resets such as Radix's `.rt-reset:where(:focus){outline:none}`. */
.ui-btn:focus-visible,
.ui-input:focus-visible,
.ui-topnav__brand:focus-visible,
.ui-topnav__link:focus-visible,
.ui-card--clickable:focus-visible,
:where(a, button, input, select, textarea, [tabindex]):focus-visible {
  outline: 2px solid var(--color-accent);
  outline-offset: 2px;
}
"""

_SHELL = """
.ui-shell {
  display: flex;
  flex-direction: column;
  min-height: 100vh;
  background: var(--color-page);
  font-family: var(--font-ui);
  color: var(--color-text);
}

.ui-main { flex: 1; width: 100%; }

.ui-container {
  width: 100%;
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 var(--space-md);
}

.ui-topnav {
  position: sticky;
  top: 0;
  z-index: 20;
  background: var(--color-card);
  border-bottom: 1px solid var(--color-border);
}

.ui-topnav__inner {
  display: flex;
  align-items: center;
  gap: var(--space-md);
  width: 100%;
  max-width: 1200px;
  min-height: 64px;
  margin: 0 auto;
  padding: 0 var(--space-md);
}

.ui-topnav__brand {
  font-size: var(--text-h2);
  font-weight: 600;
  color: var(--color-text);
  text-decoration: none;
  white-space: nowrap;
}

.ui-topnav__search { flex: 1; }

.ui-topnav__nav {
  display: flex;
  align-items: center;
  gap: var(--space-md);
  margin-left: auto;
}

.ui-topnav__link {
  display: inline-flex;
  align-items: center;
  min-height: 44px;
  font-size: var(--text-small);
  color: var(--color-muted);
  text-decoration: none;
}

.ui-topnav__link:hover { color: var(--color-text); }

.ui-page-header {
  display: flex;
  flex-wrap: wrap;
  align-items: flex-end;
  justify-content: space-between;
  gap: var(--space-md);
  margin: var(--space-xl) 0 var(--space-lg);
}

.ui-page-header__text { display: flex; flex-direction: column; gap: var(--space-xs); }

.ui-page-header__title {
  margin: 0;
  font-size: var(--text-h1);
  font-weight: 600;
  line-height: var(--leading-h1);
  color: var(--color-text);
}

.ui-page-header__subtitle {
  margin: 0;
  font-size: var(--text-small);
  color: var(--color-muted);
}

.ui-page-header__actions {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-sm);
}

.ui-footer { border-top: 1px solid var(--color-border); margin-top: var(--space-2xl); }

.ui-footer__inner {
  max-width: 1200px;
  margin: 0 auto;
  padding: var(--space-lg) var(--space-md);
  font-size: var(--text-caption);
  color: var(--color-muted);
}

/* Single-column reading width for forms and auth screens. */
.ui-column { width: 100%; max-width: 420px; margin: 0 auto; }

/* Layout helpers: a page composes blocks, it does not invent spacing. */
.ui-stack { display: flex; flex-direction: column; gap: var(--space-md); }
.ui-row { display: flex; flex-wrap: wrap; align-items: center; gap: var(--space-sm); }
.ui-text {
  margin: 0;
  font-size: var(--text-body);
  line-height: var(--leading-body);
  color: var(--color-text);
}
.ui-text--muted { color: var(--color-muted); }
.ui-text--small { font-size: var(--text-small); }

@media (min-width: 768px) {
  .ui-container { padding: 0 var(--space-lg); }
  .ui-topnav__inner { padding: 0 var(--space-lg); }
  .ui-footer__inner { padding: var(--space-lg); }
}

/* The header keeps only brand + account on narrow screens: the catalog shows
   its own search field in the page body instead of squeezing it into 360px. */
@media (max-width: 767px) {
  .ui-topnav__search { display: none; }
}
"""

_PRIMITIVES = """
.ui-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: var(--space-sm);
  min-height: 44px;
  padding: 0 var(--space-lg);
  border: 1px solid transparent;
  border-radius: var(--radius-control);
  font-family: var(--font-ui);
  font-size: var(--text-body);
  font-weight: 600;
  line-height: var(--leading-body);
  text-decoration: none;
  cursor: pointer;
  transition: background-color 0.15s ease, border-color 0.15s ease,
    color 0.15s ease, opacity 0.15s ease;
}

.ui-btn[disabled] { cursor: not-allowed; opacity: 0.5; }

.ui-btn--primary {
  background: var(--color-accent);
  border-color: var(--color-accent);
  color: var(--color-accent-text);
}

.ui-btn--primary:hover:not([disabled]) { opacity: 0.85; }

.ui-btn--secondary {
  background: var(--color-card);
  border-color: var(--color-border);
  color: var(--color-text);
}

.ui-btn--secondary:hover:not([disabled]) { background: var(--color-surface); }

.ui-btn--ghost {
  background: transparent;
  border-color: transparent;
  color: var(--color-text);
}

.ui-btn--ghost:hover:not([disabled]) { background: var(--color-surface); }

.ui-btn--danger {
  background: var(--color-danger);
  border-color: var(--color-danger);
  color: var(--color-accent-text);
}

.ui-btn--danger:hover:not([disabled]) { opacity: 0.85; }

.ui-btn__spinner {
  width: 16px;
  height: 16px;
  border: 2px solid currentColor;
  border-right-color: transparent;
  border-radius: var(--radius-pill);
  animation: ui-spin 0.7s linear infinite;
}

@keyframes ui-spin { to { transform: rotate(360deg); } }

.ui-field { display: flex; flex-direction: column; gap: var(--space-xs); width: 100%; }

.ui-field__label {
  font-size: var(--text-small);
  font-weight: 600;
  color: var(--color-text);
}

.ui-field__error { font-size: var(--text-caption); color: var(--color-danger); }

.ui-input {
  width: 100%;
  min-height: 44px;
  padding: 0 var(--space-md);
  background: var(--color-card);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-control);
  font-family: var(--font-ui);
  font-size: var(--text-body);
  line-height: var(--leading-body);
  color: var(--color-text);
  transition: border-color 0.15s ease;
}

.ui-input::placeholder { color: var(--color-muted); }

.ui-input:hover:not([disabled]) { border-color: var(--color-muted); }

.ui-input:focus { border-color: var(--color-accent); }

.ui-input[aria-invalid="true"] { border-color: var(--color-danger); }

.ui-input[disabled] {
  background: var(--color-surface);
  color: var(--color-muted);
  cursor: not-allowed;
}

.ui-card {
  background: var(--color-card);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-card);
  padding: var(--space-lg);
}

.ui-card--clickable { cursor: pointer; transition: border-color 0.15s ease; }

.ui-card--clickable:hover { border-color: var(--color-muted); }

.ui-alert {
  display: flex;
  flex-direction: column;
  gap: var(--space-xs);
  width: 100%;
  padding: var(--space-md);
  background: var(--color-card);
  border: 1px solid var(--color-border);
  border-left-width: 3px;
  border-radius: var(--radius-card);
}

.ui-alert--info { border-left-color: var(--color-accent); }
.ui-alert--success { border-left-color: var(--color-success); }
.ui-alert--error { border-left-color: var(--color-danger); }

.ui-alert__title {
  font-size: var(--text-small);
  font-weight: 600;
  color: var(--color-text);
}

.ui-alert__description { font-size: var(--text-small); color: var(--color-muted); }
"""

_MOTION = """
@media (prefers-reduced-motion: reduce) {
  .ui-btn, .ui-input, .ui-card--clickable { transition: none; }
  .ui-btn__spinner { animation-duration: 2s; }
}
"""

APP_CSS = "\n".join(
    [
        ":root {",
        _css_vars(),
        "}",
        _BASE,
        _SHELL,
        _PRIMITIVES,
        _MOTION,
    ]
)

FONT_HEAD_COMPONENTS = [
    rx.el.link(rel="preconnect", href="https://fonts.googleapis.com"),
    rx.el.link(rel="stylesheet", href=_FONT_URL),
]
