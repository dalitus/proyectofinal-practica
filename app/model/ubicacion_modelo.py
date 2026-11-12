from sqlmodel import Field, SQLModel


class UbicacionLocal(SQLModel, table=True):
    __tablename__ = "ubicaciones_locales"

    id: int = Field(default=1, primary_key=True)
    lat: float
    lng: float
