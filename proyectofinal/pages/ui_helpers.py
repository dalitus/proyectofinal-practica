import reflex as rx

from proyectofinal.ui.tokens import COLORS, RADIUS

# Reusable styled buttons and card wrappers to keep UI consistent

def PrimaryButton(label: str, on_click=None, **props) -> rx.Component:
    # Merge defaults with props, letting caller override safely
    local = props.copy()
    color = local.pop("color_scheme", "blue")
    size = local.pop("size", "3")
    border_radius = local.pop("border_radius", "md")
    # include variant only if provided by caller
    variant = local.pop("variant", None)
    kwargs = {"color_scheme": color, "size": size, "border_radius": border_radius}
    if variant is not None:
        kwargs["variant"] = variant
    return rx.button(label, on_click=on_click, **kwargs, **local)


def SecondaryButton(label: str, on_click=None, **props) -> rx.Component:
    local = props.copy()
    color = local.pop("color_scheme", "gray")
    size = local.pop("size", "3")
    border_radius = local.pop("border_radius", "md")
    variant = local.pop("variant", "outline")
    kwargs = {"color_scheme": color, "variant": variant, "size": size, "border_radius": border_radius}
    return rx.button(label, on_click=on_click, **kwargs, **local)


def DangerButton(label: str, on_click=None, **props) -> rx.Component:
    local = props.copy()
    color = local.pop("color_scheme", "red")
    size = local.pop("size", "3")
    border_radius = local.pop("border_radius", "md")
    kwargs = {"color_scheme": color, "size": size, "border_radius": border_radius}
    return rx.button(label, on_click=on_click, **kwargs, **local)


def Card(content, **props) -> rx.Component:
    return rx.box(
        content,
        padding="12px",
        border=f"1px solid {COLORS['border']}",
        border_radius=RADIUS["card"],
        background_color=COLORS["card"],
        **props,
    )


def PageHeader(title: str, subtitle: str = "") -> rx.Component:
    return rx.vstack(
        rx.heading(title, size="2", margin_bottom="6px"),
        rx.text(subtitle, color="gray.600", font_size="sm")
    )
