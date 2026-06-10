"""add stocks table

Revision ID: 0f65a31dd092
Revises: e4fa1b1f1dbb
Create Date: 2026-05-31 14:57:20.552570

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision: str = '0f65a31dd092'
down_revision: Union[str, Sequence[str], None] = 'e4fa1b1f1dbb'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    op.create_table(
        'stocks',
        sa.Column('id_stock', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('producto_id', sa.Integer(), sa.ForeignKey('productos.id'), nullable=False),
        sa.Column('color', sa.String(length=50)),
        sa.Column('cantidad_disponible', sa.Integer(), nullable=False)
    )


def downgrade():
    op.drop_table('stocks')
    # ### end Alembic commands ###
