"""clean historical "Compra realizada" consultas

The purchase used to also create a ``Consulta`` with the subject
``Compra realizada``; D-006 removed that path because the order is the single
source of truth. Rows written before the change are still in the table and show
up in the admin inbox, so this migration moves them to a backup table and then
deletes them.

The backup table is plain columns (no constraints) so restoring on downgrade
cannot fail because a user was deleted in the meantime. Once the cleanup is
validated the table can be dropped with a follow-up migration.

Revision ID: b3c9e2d5a1f7
Revises: 8d2f4c1a7b90
Create Date: 2026-10-30 00:30:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel


# revision identifiers, used by Alembic.
revision: str = "b3c9e2d5a1f7"
down_revision: Union[str, Sequence[str], None] = "8d2f4c1a7b90"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

ASUNTO = "Compra realizada"

COLUMNAS = (
    "id_consulta",
    "usuario_id",
    "respondido_por_id",
    "asunto",
    "mensaje",
    "respuesta",
    "fecha_creacion",
    "fecha_respuesta",
)

CONSULTAS = sa.table(
    "consultas",
    *[sa.column(nombre) for nombre in COLUMNAS],
)

BACKUP = sa.table(
    "consultas_compra_backup",
    *[sa.column(nombre) for nombre in COLUMNAS],
)


def upgrade() -> None:
    """Copy the automatic purchase consultas to the backup table and delete them."""
    op.create_table(
        "consultas_compra_backup",
        sa.Column("id_consulta", sa.Integer(), primary_key=True),
        sa.Column("usuario_id", sa.Integer(), nullable=False),
        sa.Column("respondido_por_id", sa.Integer(), nullable=True),
        sa.Column("asunto", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("mensaje", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("respuesta", sqlmodel.sql.sqltypes.AutoString(), nullable=True),
        sa.Column("fecha_creacion", sa.DateTime(), nullable=False),
        sa.Column("fecha_respuesta", sa.DateTime(), nullable=True),
    )

    op.execute(
        BACKUP.insert().from_select(
            list(COLUMNAS),
            sa.select(*[CONSULTAS.c[nombre] for nombre in COLUMNAS]).where(
                CONSULTAS.c.asunto == ASUNTO
            ),
        )
    )
    op.execute(CONSULTAS.delete().where(CONSULTAS.c.asunto == ASUNTO))


def downgrade() -> None:
    """Put the rows back and drop the backup table."""
    op.execute(
        CONSULTAS.insert().from_select(
            list(COLUMNAS),
            sa.select(*[BACKUP.c[nombre] for nombre in COLUMNAS]).where(
                BACKUP.c.id_consulta.not_in(sa.select(CONSULTAS.c.id_consulta))
            ),
        )
    )
    op.drop_table("consultas_compra_backup")
