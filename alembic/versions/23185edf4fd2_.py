"""empty message

Revision ID: 23185edf4fd2
Revises: 00d962f97ead
Create Date: 2026-04-08 09:57:23.595039

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql
import sqlmodel

# revision identifiers, used by Alembic.
revision: str = '23185edf4fd2'
down_revision: Union[str, Sequence[str], None] = '00d962f97ead'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # En productos ya no hay nada que modificar
    with op.batch_alter_table('productos', schema=None) as batch_op:
        pass

    # En stocks solo aseguramos la foreign key
    with op.batch_alter_table('stocks', schema=None) as batch_op:
        batch_op.create_foreign_key(None, 'productos', ['id_producto'], ['id_producto'])


def downgrade() -> None:
    """Downgrade schema."""
    with op.batch_alter_table('stocks', schema=None) as batch_op:
        batch_op.drop_constraint(None, type_='foreignkey')

    with op.batch_alter_table('productos', schema=None) as batch_op:
        batch_op.add_column(sa.Column('id_stock', mysql.INTEGER(), autoincrement=False, nullable=True))
        batch_op.create_foreign_key(batch_op.f('productos_ibfk_1'), 'stocks', ['id_stock'], ['id_stock'])
