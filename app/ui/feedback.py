"""Feedback components: Skeleton, Toast, Drawer, ConfirmDialog.

Same rules as ``primitives.py``: styling comes from ``app.ui.styles`` and these
components own no colour. Drawer and ConfirmDialog sit on the Radix primitives
that ship with Reflex (Vaul/Radix) only to get focus trap, Escape handling and
``role`` semantics right; their look is ours.
"""

from __future__ import annotations

from typing import Any

import reflex as rx

from app.ui.primitives import BUTTON_VARIANTS, Button

SKELETON_VARIANTS = ("line", "block", "card")
TOAST_TONES = ("success", "error")


def _join(*class_names: str | None) -> str:
    return " ".join(name for name in class_names if name)


def Skeleton(
    variant: str = "line",
    *,
    count: int = 1,
    width: str | None = None,
    height: str | None = None,
    class_name: str | None = None,
) -> rx.Component:
    """Loading placeholder shaped like the content it replaces.

    Never a full-page spinner (docs/design.md 6). Placeholders are decorative, so
    they are hidden from assistive technology: announce the load on the region
    that is actually loading.
    """
    if variant not in SKELETON_VARIANTS:
        raise ValueError(
            f"Unknown skeleton variant {variant!r}; expected one of {SKELETON_VARIANTS}"
        )

    bars = []
    style = {}
    if width is not None:
        style["width"] = width
    if height is not None:
        style["height"] = height

    for _ in range(count):
        bar_props: dict[str, Any] = {
            "class_name": _join("ui-skeleton", f"ui-skeleton--{variant}", class_name),
            "aria-hidden": "true",
        }
        if style:
            bar_props["style"] = dict(style)
        bars.append(rx.el.div(**bar_props))

    if count == 1:
        return bars[0]

    return rx.el.div(*bars, class_name="ui-stack")


def Toast(message: Any, tone: str = "success", **options: Any) -> Any:
    """Build the toast event to yield from a handler.

    Usage: ``return Toast("Pedido creado")``. Toast copy is short and sentence
    case; technical detail belongs in the log (T-064).
    """
    if tone not in TOAST_TONES:
        raise ValueError(f"Unknown toast tone {tone!r}; expected one of {TOAST_TONES}")

    options.setdefault("duration", 4000)
    if tone == "error":
        return rx.toast.error(message, **options)
    return rx.toast.success(message, **options)


def Drawer(
    *,
    trigger: rx.Component,
    title: Any,
    content: rx.Component | None = None,
    description: Any = None,
    side: str = "right",
    open: Any = None,
    on_open_change: Any = None,
    class_name: str | None = None,
) -> rx.Component:
    """Side panel for creating/editing, opened from ``trigger``.

    The body is a single ``content`` component (usually a form stack) so the
    call site cannot pass children after keyword arguments by mistake.
    ``open``/``on_open_change`` are optional: without them the panel manages its
    own state, which covers the admin forms. Pass them when the page needs to
    close the panel from a handler.
    """
    if side not in ("left", "right"):
        raise ValueError(f"Unknown drawer side {side!r}; expected 'left' or 'right'")

    props: dict[str, Any] = {}
    if open is not None:
        props["open"] = open
    if on_open_change is not None:
        props["on_open_change"] = on_open_change

    body: list[Any] = [
        rx.el.div(
            rx.drawer.title(title, class_name="ui-drawer__title"),
            rx.drawer.close(Button("Cerrar", variant="ghost")),
            class_name="ui-drawer__header",
        ),
    ]
    if description is not None:
        body.append(rx.el.p(description, class_name="ui-dialog__description"))
    if content is not None:
        body.append(content)

    return rx.drawer.root(
        rx.drawer.trigger(trigger),
        rx.drawer.portal(
            rx.drawer.overlay(class_name="ui-overlay"),
            rx.drawer.content(
                *body,
                class_name=_join(
                    "ui-drawer__content",
                    "ui-drawer__content--left" if side == "left" else None,
                    class_name,
                ),
            ),
        ),
        direction=side,
        **props,
    )


def ConfirmDialog(
    *,
    trigger: rx.Component,
    title: Any,
    description: Any = None,
    confirm_label: str = "Confirmar",
    cancel_label: str = "Cancelar",
    on_confirm: Any = None,
    tone: str = "danger",
    class_name: str | None = None,
) -> rx.Component:
    """Ask before a destructive action and nothing else (design.md 6).

    ``on_confirm`` runs on click and the dialog closes itself; cancelling needs no
    handler. It never closes on outside click, so the decision stays explicit.
    """
    if tone not in BUTTON_VARIANTS:
        raise ValueError(f"Unknown tone {tone!r}; expected one of {BUTTON_VARIANTS}")

    body: list[Any] = [
        rx.alert_dialog.title(title, class_name="ui-dialog__title"),
    ]
    if description is not None:
        body.append(
            rx.alert_dialog.description(
                description,
                class_name="ui-dialog__description",
            )
        )
    body.append(
        rx.el.div(
            rx.alert_dialog.cancel(Button(cancel_label, variant="ghost")),
            rx.alert_dialog.action(Button(confirm_label, variant=tone, on_click=on_confirm)),
            class_name="ui-dialog__actions",
        )
    )

    return rx.alert_dialog.root(
        rx.alert_dialog.trigger(trigger),
        rx.alert_dialog.content(
            *body,
            class_name=_join("ui-dialog__content", class_name),
        ),
    )


__all__ = ["ConfirmDialog", "Drawer", "Skeleton", "Toast"]
