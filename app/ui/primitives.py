"""Primitive components: Button, Input, Card, Alert.

Every visual decision (colour, spacing, radius, state) comes from
``app.ui.tokens`` through the classes defined in ``app.ui.styles``. Pages compose
these components; they never restyle them.

States are implemented, not documented: ``styles.py`` carries the ``:hover``,
``:focus-visible``, ``[disabled]`` and ``[aria-invalid]`` rules.
"""

from __future__ import annotations

import itertools
from typing import Any

import reflex as rx

BUTTON_VARIANTS = ("primary", "secondary", "ghost", "danger")
ALERT_TONES = ("info", "success", "error")

_INPUT_IDS = itertools.count(1)


def _join(*class_names: str | None) -> str:
    """Join class names, dropping the empty ones."""
    return " ".join(name for name in class_names if name)


def _any_true(*values: Any) -> Any:
    """OR booleans or Reflex Vars into a single expression."""
    if not any(isinstance(value, rx.Var) for value in values):
        return any(bool(value) for value in values)
    expression = rx.Var.create(False)
    for value in values:
        expression = expression | value
    return expression


def Button(
    label: Any = None,
    *,
    variant: str = "primary",
    loading: Any = False,
    disabled: Any = False,
    type: str = "button",
    class_name: str | None = None,
    **props: Any,
) -> rx.Component:
    """Primary action button.

    Args:
        label: Text or Var rendered inside the button.
        variant: One of ``primary``, ``secondary``, ``ghost``, ``danger``.
        loading: When true, shows a spinner and disables the button.
        disabled: Disables the button without a spinner.

    Docs: docs/design.md 4.2 (variants, normal/hover/focus/disabled/loading).
    """
    if variant not in BUTTON_VARIANTS:
        raise ValueError(
            f"Unknown button variant {variant!r}; expected one of {BUTTON_VARIANTS}"
        )

    spinner = rx.cond(
        loading,
        rx.el.span(
            class_name="ui-btn__spinner",
            **{"aria-hidden": "true"},
        ),
        rx.fragment(),
    )

    return rx.el.button(
        spinner,
        label,
        type=type,
        class_name=_join("ui-btn", f"ui-btn--{variant}", class_name),
        disabled=_any_true(disabled, loading),
        **props,
    )


def Input(
    *,
    label: Any = None,
    value: Any = None,
    on_change: Any = None,
    error: Any = None,
    type: str = "text",
    placeholder: str | None = None,
    name: str | None = None,
    disabled: Any = False,
    required: bool = False,
    input_id: str | None = None,
    class_name: str | None = None,
    **props: Any,
) -> rx.Component:
    """Labelled text input with inline error text.

    The label is always visible (docs/design.md 7: no placeholder-as-label) and
    ``aria-invalid`` follows ``error`` so the border and the screen reader agree.
    """
    element_id = input_id or f"ui-input-{next(_INPUT_IDS)}"

    if error is None:
        invalid = False
        error_text: Any = ""
    elif isinstance(error, rx.Var):
        invalid = error != ""
        error_text = error
    else:
        invalid = bool(error)
        error_text = error

    fields: list[Any] = []
    if label is not None:
        fields.append(
            rx.el.label(
                label,
                **{"html_for": element_id},
                class_name="ui-field__label",
            )
        )
    fields.append(
        rx.el.input(
            id=element_id,
            type=type,
            name=name,
            value=value,
            on_change=on_change,
            placeholder=placeholder,
            disabled=disabled,
            required=required,
            class_name=_join("ui-input", class_name),
            **{"aria-invalid": invalid},
            **props,
        )
    )
    fields.append(
        rx.cond(
            error_text != "",
            rx.el.span(error_text, class_name="ui-field__error", role="alert"),
            rx.fragment(),
        )
    )

    return rx.el.div(*fields, class_name="ui-field")


def Card(
    *children: Any,
    clickable: bool = False,
    class_name: str | None = None,
    **props: Any,
) -> rx.Component:
    """Content block: white surface, 1px border, no shadow (design.md 1.4).

    ``clickable`` only adds the hover affordance. Keyboard users still need a
    real link or button inside, so it never pretends to be one.
    """
    return rx.el.div(
        *children,
        class_name=_join("ui-card", "ui-card--clickable" if clickable else None, class_name),
        **props,
    )


def Alert(
    *,
    title: Any,
    description: Any = None,
    tone: str = "info",
    class_name: str | None = None,
    **props: Any,
) -> rx.Component:
    """Inline message for a page-level state (never a replacement for field errors).

    The tone paints only the left border: the wording always says what happened,
    so meaning is not carried by colour alone (design.md 7).
    """
    if tone not in ALERT_TONES:
        raise ValueError(f"Unknown alert tone {tone!r}; expected one of {ALERT_TONES}")

    children: list[Any] = [
        rx.el.span(title, class_name="ui-alert__title"),
    ]
    if description is not None:
        children.append(
            rx.el.span(description, class_name="ui-alert__description"),
        )

    return rx.el.div(
        *children,
        class_name=_join("ui-alert", f"ui-alert--{tone}", class_name),
        role="alert" if tone == "error" else "status",
        **props,
    )
