"""drop the temporary consultas_compra_backup table

``b3c9e2d5a1f7`` moved the historical "Compra realizada" consultas to a backup
table and said the table could be dropped once the cleanup was validated. The
rows are not needed anymore (D-006) and the leftover table makes
``alembic check`` detect schema drift, which stops ``reflex run --env prod``
with "Detected database schema changes".

Revision ID: e6f1a4c8b2d9
Revises: c4d8f1a9e2b6
Create Date: 2026-11-06 00:00:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel


# revision identifiers, used by Alembic.
revision: str = "e6f1a4c8b2d9"
down_revision: Union[str, Sequence[str], None] = "c4d8f1a9e2b6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Drop the temporary backup table created by the cleanup migration."""
    op.drop_table("consultas_compra_backup")


def downgrade() -> None:
    """Recreate the empty table so the previous revision finds it."""
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
