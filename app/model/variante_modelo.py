from typing import TYPE_CHECKING, Optional

from sqlmodel import CheckConstraint, Field, Relationship, SQLModel, UniqueConstraint

if TYPE_CHECKING:
    from app.model.producto_modelo import Producto


class Stocks(SQLModel, table=True):
    """Variante de un producto: (producto, color, talle) con stock propio (D-009).

    La tabla conserva el nombre `stocks` por compatibilidad con la base actual;
    el renombre de archivos y clases llega con T-075.
    """

    __tablename__ = "stocks"
    __table_args__ = (
        UniqueConstraint(
            "producto_id",
            "color",
            "talle",
            name="uq_stock_producto_color_talle",
        ),
        CheckConstraint(
            "cantidad_disponible >= 0",
            name="ck_stock_cantidad_no_negativa",
        ),
    )

    id_stock: Optional[int] = Field(default=None, primary_key=True)
    producto_id: int = Field(foreign_key="productos.id", index=True)
    color: str
    talle: str
    cantidad_disponible: int = Field(default=0, ge=0)

    producto: Optional["Producto"] = Relationship(back_populates="stocks")
