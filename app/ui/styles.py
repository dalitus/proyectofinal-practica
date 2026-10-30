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
    # Soft tints of the alert backgrounds: derived from the tone colour, so a
    # new tone never needs another literal (docs/design.md 4.4).
    lines.append(f"  --color-danger-soft: {_rgba(COLORS['danger'], 0.06)};")
    lines.append(f"  --color-success-soft: {_rgba(COLORS['success'], 0.06)};")
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
  align-items: flex-start;
  gap: var(--space-sm);
  width: 100%;
  padding: var(--space-md);
  background: var(--color-card);
  border: 1px solid var(--color-border);
  border-left-width: 3px;
  border-radius: var(--radius-card);
}

/* The icon and the tinted background repeat what the tone already says in
   words: colour is never the only signal (docs/design.md 7). */
.ui-alert__body {
  display: flex;
  flex-direction: column;
  gap: var(--space-xs);
  min-width: 0;
}

.ui-alert__icon { flex: 0 0 auto; width: 18px; height: 18px; }

.ui-alert--info { border-left-color: var(--color-accent); }
.ui-alert--info .ui-alert__icon { color: var(--color-accent); }

.ui-alert--success {
  border-left-color: var(--color-success);
  background: var(--color-success-soft);
}
.ui-alert--success .ui-alert__icon { color: var(--color-success); }

.ui-alert--error {
  border-left-color: var(--color-danger);
  background: var(--color-danger-soft);
}
.ui-alert--error .ui-alert__icon { color: var(--color-danger); }

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

/* StockBadge (design.md 4.3): the dot carries the tone, the label stays muted. */
.ui-badge--quiet { color: var(--color-muted); }

/* Announces a change to screen readers without adding a visible line. */
.ui-visually-hidden {
  position: absolute;
  width: 1px;
  height: 1px;
  margin: -1px;
  padding: 0;
  overflow: hidden;
  clip: rect(0 0 0 0);
  white-space: nowrap;
  border: 0;
}

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

_CATALOGO = """
/* Catalog page (design.md 4.3): 4 columns on desktop, 2 on tablet, 1 on phone. */
.ui-filters {
  display: flex;
  flex-direction: column;
  gap: var(--space-md);
  padding: var(--space-lg);
  background: var(--color-card);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-card);
}

.ui-filters__fields {
  display: grid;
  gap: var(--space-md);
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  align-items: end;
}

.ui-filters__actions {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-sm);
  justify-content: flex-end;
}

.ui-grid {
  display: grid;
  gap: var(--space-lg);
  grid-template-columns: 1fr;
}

@media (min-width: 768px) {
  .ui-grid { grid-template-columns: repeat(2, 1fr); }
}

@media (min-width: 1024px) {
  .ui-grid { grid-template-columns: repeat(4, 1fr); }
}

/* The card is the product: the image bleeds to the edges. */
.ui-product { padding: 0; overflow: hidden; }

.ui-product__media { aspect-ratio: 3 / 4; background: var(--color-surface); }

.ui-product__image { display: block; width: 100%; height: 100%; object-fit: cover; }

.ui-product__placeholder {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 100%;
  font-family: var(--font-ui);
  font-size: var(--text-small);
  color: var(--color-muted);
}

.ui-product__body {
  display: flex;
  flex-direction: column;
  gap: var(--space-xs);
  padding: var(--space-md);
}

.ui-product__name {
  display: -webkit-box;
  -webkit-box-orient: vertical;
  -webkit-line-clamp: 2;
  overflow: hidden;
  margin: 0;
  font-size: var(--text-body);
  font-weight: 600;
  line-height: var(--leading-body);
  color: var(--color-text);
}

.ui-product__price {
  margin: 0;
  font-size: var(--text-h2);
  font-weight: 600;
  line-height: var(--leading-h2);
  color: var(--color-text);
}

.ui-pagination {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: center;
  gap: var(--space-md);
}
"""

_DETALLE = """
/* Product detail (design.md 4.4): 3:4 image left, purchase line right. */
.ui-back {
  display: inline-flex;
  align-items: center;
  min-height: 44px;
  font-size: var(--text-small);
  color: var(--color-muted);
  text-decoration: none;
}

.ui-back:hover { color: var(--color-text); }

.ui-detail {
  display: grid;
  grid-template-columns: minmax(0, 1fr);
  gap: var(--space-lg);
  align-items: start;
}

@media (min-width: 768px) {
  .ui-detail {
    grid-template-columns: minmax(0, 1fr) minmax(0, 1fr);
    gap: var(--space-xl);
  }
}

@media (min-width: 1024px) {
  .ui-detail {
    grid-template-columns: minmax(0, 5fr) minmax(0, 6fr);
  }
}

.ui-detail__media {
  overflow: hidden;
  aspect-ratio: 3 / 4;
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-card);
}

.ui-detail__image { display: block; width: 100%; height: 100%; object-fit: cover; }

.ui-detail__placeholder {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 100%;
  font-size: var(--text-small);
  color: var(--color-muted);
}

.ui-detail__info {
  display: flex;
  flex-direction: column;
  gap: var(--space-md);
  min-width: 0;
}

.ui-detail__name {
  margin: 0;
  font-size: var(--text-h1);
  font-weight: 600;
  line-height: var(--leading-h1);
  color: var(--color-text);
}

.ui-detail__price {
  margin: 0;
  font-size: var(--text-h2);
  font-weight: 600;
  line-height: var(--leading-h2);
  color: var(--color-text);
}

.ui-detail__group { display: flex; flex-direction: column; gap: var(--space-sm); }

.ui-detail__group-label {
  margin: 0;
  font-size: var(--text-small);
  font-weight: 600;
  color: var(--color-text);
}

.ui-detail__chips { display: flex; flex-wrap: wrap; gap: var(--space-sm); }

/* Description goes below the purchase line, never above it (design.md 4.4). */
.ui-detail__description {
  margin: 0;
  padding-top: var(--space-md);
  border-top: 1px solid var(--color-border);
  font-size: var(--text-body);
  line-height: var(--leading-body);
  color: var(--color-muted);
  max-width: 60ch;
}

/* The purchase line: one primary action and the reason when it is disabled. */
.ui-detail__buy {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: var(--space-sm);
}

/* The whole card is the link to the detail. */
.ui-product-link {
  display: block;
  color: inherit;
  text-decoration: none;
  border-radius: var(--radius-card);
}

.ui-product-link:focus-visible {
  outline: 2px solid var(--color-accent);
  outline-offset: 2px;
}
"""

_CARRITO = """
.ui-cart {
  display: grid;
  grid-template-columns: minmax(0, 1fr);
  gap: var(--space-lg);
  align-items: start;
}

@media (min-width: 1024px) {
  .ui-cart {
    grid-template-columns: minmax(0, 1fr) 360px;
    gap: var(--space-xl);
  }
}

.ui-cart__lines { display: flex; flex-direction: column; gap: var(--space-md); }

.ui-cart__toolbar { display: flex; justify-content: flex-end; }

.ui-cart__line {
  display: grid;
  grid-template-columns: 88px minmax(0, 1fr);
  gap: var(--space-md);
  padding: var(--space-md);
  background: var(--color-card);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-card);
}

.ui-cart__thumb {
  overflow: hidden;
  aspect-ratio: 3 / 4;
  background: var(--color-surface);
  border-radius: var(--radius-control);
}

.ui-cart__image { display: block; width: 100%; height: 100%; object-fit: cover; }

.ui-cart__placeholder {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 100%;
  font-size: var(--text-caption);
  color: var(--color-muted);
}

.ui-cart__info {
  display: flex;
  flex-direction: column;
  gap: var(--space-xs);
  min-width: 0;
}

.ui-cart__name {
  font-size: var(--text-body);
  font-weight: 600;
  line-height: var(--leading-body);
  color: var(--color-text);
  text-decoration: none;
}

.ui-cart__name:hover { text-decoration: underline; }

/* The actions keep their own row on mobile so nothing has to shrink to fit. */
.ui-cart__footer {
  grid-column: 1 / -1;
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: space-between;
  gap: var(--space-md);
  padding-top: var(--space-sm);
  border-top: 1px solid var(--color-border);
}

@media (min-width: 768px) {
  .ui-cart__footer {
    grid-column: 2;
    padding-top: 0;
    border-top: none;
  }
}

.ui-stepper { display: inline-flex; align-items: center; gap: var(--space-xs); }

.ui-stepper__qty {
  min-width: 2ch;
  text-align: center;
  font-variant-numeric: tabular-nums;
  color: var(--color-text);
}

.ui-cart__subtotal { margin: 0; font-weight: 600; color: var(--color-text); }

.ui-cart__summary {
  display: flex;
  flex-direction: column;
  gap: var(--space-md);
  padding: var(--space-lg);
  background: var(--color-card);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-card);
}

@media (min-width: 1024px) {
  .ui-cart__summary {
    position: sticky;
    top: var(--space-lg);
    box-shadow: var(--shadow-floating);
  }
}

.ui-cart__summary-title {
  margin: 0;
  font-size: var(--text-h2);
  font-weight: 600;
  line-height: var(--leading-h2);
  color: var(--color-text);
}

.ui-cart__row {
  display: flex;
  justify-content: space-between;
  gap: var(--space-md);
  font-size: var(--text-body);
  color: var(--color-muted);
}

.ui-cart__row--total {
  padding-top: var(--space-sm);
  border-top: 1px solid var(--color-border);
  font-size: var(--text-h2);
  font-weight: 600;
  line-height: var(--leading-h2);
  color: var(--color-text);
}
"""

_CHECKOUT = """
.ui-checkout {
  display: grid;
  grid-template-columns: minmax(0, 1fr);
  gap: var(--space-lg);
  align-items: start;
}

@media (min-width: 1024px) {
  .ui-checkout {
    grid-template-columns: minmax(0, 1fr) 360px;
    gap: var(--space-xl);
  }
}

.ui-checkout__form {
  display: flex;
  flex-direction: column;
  gap: var(--space-md);
  margin-top: var(--space-md);
}

.ui-checkout__fields {
  display: grid;
  grid-template-columns: minmax(0, 1fr);
  gap: var(--space-md);
}

@media (min-width: 768px) {
  .ui-checkout__fields { grid-template-columns: repeat(2, minmax(0, 1fr)); }
}

/* Address, which needs the whole row, and nothing else. */
.ui-checkout__wide { grid-column: 1 / -1; }

.ui-checkout__title {
  margin: 0;
  font-size: var(--text-h2);
  font-weight: 600;
  line-height: var(--leading-h2);
  color: var(--color-text);
}

.ui-checkout__items {
  display: flex;
  flex-direction: column;
  gap: var(--space-sm);
  margin: 0;
  padding: 0 0 var(--space-sm);
  border-bottom: 1px solid var(--color-border);
  list-style: none;
}

.ui-checkout__item {
  display: flex;
  justify-content: space-between;
  gap: var(--space-md);
  font-size: var(--text-small);
  color: var(--color-muted);
}

.ui-checkout__note {
  margin: 0;
  font-size: var(--text-caption);
  line-height: var(--leading-caption);
  color: var(--color-muted);
}

.ui-checkout__success {
  display: flex;
  flex-direction: column;
  gap: var(--space-md);
  max-width: 560px;
}

.ui-checkout__order {
  margin: 0;
  font-size: var(--text-h1);
  font-weight: 600;
  line-height: var(--leading-h1);
  color: var(--color-text);
}

.ui-checkout__details {
  display: flex;
  flex-direction: column;
  gap: var(--space-sm);
  margin: 0;
}

.ui-checkout__details dt { margin: 0; }

.ui-checkout__details dd { margin: 0; text-align: right; color: var(--color-text); }
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
        _CATALOGO,
        _DETALLE,
        _CARRITO,
        _CHECKOUT,
        _MOTION,
    ]
)

FONT_HEAD_COMPONENTS = [
    rx.el.link(rel="preconnect", href="https://fonts.googleapis.com"),
    rx.el.link(rel="stylesheet", href=_FONT_URL),
]
