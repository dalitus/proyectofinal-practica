"""add fecha_cancelacion to pedidos

D-010 pide registrar cuando se cancela un pedido. La columna es nullable porque
solo se llena al cancelar.

Revision ID: 8d2f4c1a7b90
Revises: 61c05db43688
Create Date: 2026-10-30 00:00:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "8d2f4c1a7b90"
down_revision: Union[str, Sequence[str], None] = "61c05db43688"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add the cancellation timestamp (D-010)."""
    op.add_column(
        "pedidos",
        sa.Column("fecha_cancelacion", sa.DateTime(), nullable=True),
    )


def downgrade() -> None:
    """Drop the cancellation timestamp."""
    op.drop_column("pedidos", "fecha_cancelacion")
