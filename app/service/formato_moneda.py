"""Single price formatter (D-003, T-032).

Every screen shows the same string for the same amount: ARS, es-AR separators
(thousands with `.`, decimals with `,`) and two decimals. Formatting lives in the
service layer so the pages only render the string; no page re-implements it.
"""

from __future__ import annotations

from decimal import Decimal, InvalidOperation

SIMBOLO = "$"
MONEDA = "ARS"
_CENTAVOS = Decimal("0.01")


def formatear_precio(valor: Decimal | int | float | str | None) -> str:
    """Return ``$ 1.234,56`` for the amount, or an empty string when invalid."""
    if valor is None or valor == "":
        return ""

    try:
        monto = Decimal(str(valor)).quantize(_CENTAVOS)
    except (InvalidOperation, ValueError):
        return ""

    # `f"{monto:,.2f}"` is en-US; swap the separators in place. The sentinel is
    # a character that formatted numbers can never contain.
    texto = f"{monto:,.2f}".replace(",", "_").replace(".", ",").replace("_", ".")
    return f"{SIMBOLO} {texto}"
