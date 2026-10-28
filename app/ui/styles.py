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

from app.ui.tokens import COLORS, FONT, RADIUS, SHADOW, SPACE, TYPE

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
    for name, value in SHADOW.items():
        lines.append(f"  --shadow-{name}: {value};")
    lines.append(f"  --font-ui: {FONT};")
    # Scrim of overlays: the text colour with alpha, derived so the palette
    # still has a single source.
    lines.append(f"  --scrim: {_rgba(COLORS['text'], 0.35)};")
    return "\n".join(lines)


def _rgba(hex_color: str, alpha: float) -> str:
    """Turn ``#111111`` into ``rgba(17, 17, 17, alpha)``."""
    channels = [int(hex_color[index : index + 2], 16) for index in (1, 3, 5)]
    red, green, blue = channels
    return f"rgba({red}, {green}, {blue}, {alpha})"


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

/* Select: native control for free keyboard support, our border and a chevron
   drawn with borders so the indicator needs no extra asset or hex value. */
.ui-select-wrap { position: relative; width: 100%; }

.ui-select-wrap::after {
  content: "";
  position: absolute;
  top: 50%;
  right: var(--space-md);
  width: 8px;
  height: 8px;
  border-right: 1.5px solid var(--color-muted);
  border-bottom: 1.5px solid var(--color-muted);
  transform: translateY(-70%) rotate(45deg);
  pointer-events: none;
}

.ui-select { appearance: none; padding-right: var(--space-2xl); cursor: pointer; }

.ui-badge {
  display: inline-flex;
  align-items: center;
  gap: var(--space-xs);
  padding: var(--space-xs) var(--space-sm);
  background: var(--color-card);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-pill);
  font-family: var(--font-ui);
  font-size: var(--text-caption);
  font-weight: 600;
  line-height: var(--leading-caption);
  color: var(--color-text);
  white-space: nowrap;
}

/* Colour lives in the dot; the label always says the state in words. */
.ui-badge__dot {
  width: 8px;
  height: 8px;
  flex: none;
  border-radius: var(--radius-pill);
  background: var(--color-muted);
}

.ui-badge--success .ui-badge__dot { background: var(--color-success); }
.ui-badge--danger .ui-badge__dot { background: var(--color-danger); }
.ui-badge--info .ui-badge__dot { background: var(--color-accent); }

.ui-chip {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 44px;
  min-height: 44px;
  padding: 0 var(--space-md);
  background: var(--color-card);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-pill);
  font-family: var(--font-ui);
  font-size: var(--text-small);
  font-weight: 600;
  color: var(--color-text);
  cursor: pointer;
  transition: border-color 0.15s ease, background-color 0.15s ease, color 0.15s ease;
}

.ui-chip:hover:not([disabled]) { border-color: var(--color-muted); }

.ui-chip--selected {
  background: var(--color-accent);
  border-color: var(--color-accent);
  color: var(--color-accent-text);
}

.ui-chip[disabled] {
  opacity: 0.5;
  cursor: not-allowed;
  text-decoration: line-through;
}

.ui-empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: var(--space-md);
  padding: var(--space-2xl) var(--space-lg);
  background: var(--color-card);
  border: 1px dashed var(--color-border);
  border-radius: var(--radius-card);
  text-align: center;
}

.ui-empty__title {
  margin: 0;
  font-size: var(--text-h2);
  font-weight: 600;
  line-height: var(--leading-h2);
  color: var(--color-text);
}

.ui-empty__text {
  margin: 0;
  max-width: 65ch;
  font-size: var(--text-small);
  color: var(--color-muted);
}
"""

_FEEDBACK = """
.ui-skeleton {
  display: block;
  background: var(--color-surface);
  border-radius: var(--radius-control);
  animation: ui-pulse 1.2s ease-in-out infinite alternate;
}

.ui-skeleton--line { height: var(--text-body); }
.ui-skeleton--block { height: 96px; border-radius: var(--radius-card); }
.ui-skeleton--card { height: 280px; border-radius: var(--radius-card); }

@keyframes ui-pulse { from { opacity: 0.55; } to { opacity: 1; } }

/* Vaul (the primitive behind rx.drawer) hardcodes `inset: 0` on the panel and
   `rgba(0,0,0,.5)` on the scrim, so these rules carry the `body` prefix to win
   the cascade: specificity 0,1,1 against their 0,1,0. */
body .ui-overlay {
  background: var(--scrim);
}

body .ui-drawer__content {
  top: 0;
  right: 0;
  bottom: 0;
  left: auto;
  display: flex;
  flex-direction: column;
  gap: var(--space-md);
  width: min(420px, 100%);
  height: 100%;
  padding: var(--space-lg);
  overflow-y: auto;
  background: var(--color-card);
  border-left: 1px solid var(--color-border);
  box-shadow: var(--shadow-floating);
  font-family: var(--font-ui);
  color: var(--color-text);
}

body .ui-drawer__content--left {
  left: 0;
  right: auto;
  border-left: none;
  border-right: 1px solid var(--color-border);
}

.ui-drawer__header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--space-md);
}

.ui-drawer__title {
  margin: 0;
  font-size: var(--text-h2);
  font-weight: 600;
  line-height: var(--leading-h2);
  color: var(--color-text);
}

/* Radix positions the dialog box; these two selectors carry `body` so they win
   over `.rt-BaseDialogContent` (same specificity, loaded later in the head). */
body .ui-dialog__content {
  width: min(440px, calc(100% - 2 * var(--space-md)));
  padding: var(--space-lg);
  background: var(--color-card);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-card);
  box-shadow: var(--shadow-floating);
  font-family: var(--font-ui);
  color: var(--color-text);
}

.ui-dialog__title {
  margin: 0;
  font-size: var(--text-h2);
  font-weight: 600;
  line-height: var(--leading-h2);
  color: var(--color-text);
}

.ui-dialog__description {
  margin: 0;
  font-size: var(--text-small);
  line-height: var(--leading-small);
  color: var(--color-muted);
}

.ui-dialog__actions {
  display: flex;
  flex-wrap: wrap;
  justify-content: flex-end;
  gap: var(--space-sm);
  margin-top: var(--space-sm);
}
"""

_MOTION = """
@media (prefers-reduced-motion: reduce) {
  .ui-btn, .ui-input, .ui-card--clickable, .ui-chip { transition: none; }
  .ui-btn__spinner { animation-duration: 2s; }
  .ui-skeleton { animation: none; opacity: 0.7; }
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
        _FEEDBACK,
        _MOTION,
    ]
)

FONT_HEAD_COMPONENTS = [
    rx.el.link(rel="preconnect", href="https://fonts.googleapis.com"),
    rx.el.link(rel="stylesheet", href=_FONT_URL),
]
