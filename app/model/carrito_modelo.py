from sqlmodel import Field, SQLModel, UniqueConstraint


class Carrito(SQLModel, table=True):
    """Linea del carrito de un comprador registrado (D-002, D-009).

    Apunta a una variante concreta, no al producto: negro 38 y negro 39 son
    unidades distintas. Un comprador tiene a lo sumo una linea por variante.
    """

    __tablename__ = "carritos"
    __table_args__ = (
        UniqueConstraint("usuario_id", "variante_id", name="uq_carrito_usuario_variante"),
    )

    id_carrito: int | None = Field(default=None, primary_key=True)
    usuario_id: int = Field(foreign_key="localuser.id", index=True)
    variante_id: int = Field(foreign_key="stocks.id_stock", index=True)
    cantidad: int = Field(default=1, ge=1)
