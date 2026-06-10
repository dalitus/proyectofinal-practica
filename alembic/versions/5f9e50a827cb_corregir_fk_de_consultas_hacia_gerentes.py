"""Corregir FK de consultas hacia gerentes

Revision ID: 5f9e50a827cb
Revises: b7bb9f50bc07
Create Date: 2026-05-31 14:17:42.212583

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision = '5f9e50a827cb'
down_revision = 'b7bb9f50bc07'
branch_labels = None
depends_on = None

def upgrade() -> None:
    # Corregir FK de consultas hacia gerentes
    op.drop_constraint('consultas_ibfk_2', 'consultas', type_='foreignkey')
    op.create_foreign_key(
        'fk_consultas_gerentes',
        'consultas',
        'gerentes',
        ['id_gerente'],
        ['id_gerente']
    )

def downgrade() -> None:
    op.drop_constraint('fk_consultas_gerentes', 'consultas', type_='foreignkey')
    op.create_foreign_key(
        'consultas_ibfk_2',
        'consultas',
        'gerentes',
        ['id_gerente'],
        ['id']
    )

