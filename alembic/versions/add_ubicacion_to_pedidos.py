"""Add ubicacion fields to pedidos table

Revision ID: add_ubicacion_pedidos
Revises: 
Create Date: 2026-02-03 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_ubicacion_pedidos'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add new columns to pedidos table
    op.add_column('pedidos', sa.Column('direccion', sa.String(length=255), nullable=True))
    op.add_column('pedidos', sa.Column('numero', sa.String(length=50), nullable=True))
    op.add_column('pedidos', sa.Column('departamento', sa.String(length=100), nullable=True))
    op.add_column('pedidos', sa.Column('codigo_postal', sa.String(length=20), nullable=True))
    op.add_column('pedidos', sa.Column('ciudad', sa.String(length=100), nullable=True))
    op.add_column('pedidos', sa.Column('provincia', sa.String(length=100), nullable=True))


def downgrade() -> None:
    # Remove columns from pedidos table
    op.drop_column('pedidos', 'provincia')
    op.drop_column('pedidos', 'ciudad')
    op.drop_column('pedidos', 'codigo_postal')
    op.drop_column('pedidos', 'departamento')
    op.drop_column('pedidos', 'numero')
    op.drop_column('pedidos', 'direccion')