"""Renombrar id_users a usuario_id en consultas

Revision ID: b7bb9f50bc07
Revises: a78d5d50422d
Create Date: 2026-05-31 14:07:55.885648

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql


# revision identifiers, used by Alembic.
revision = 'b7bb9f50bc07'
down_revision = 'a78d5d50422d'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Renombrar columna id_users a usuario_id en consultas
    op.alter_column(
        'consultas',
        'id_users',
        new_column_name='usuario_id',
        existing_type=sa.Integer,      # 👈 tipo actual
        existing_nullable=False        # 👈 si era NOT NULL
    )


def downgrade() -> None:
    # Volver a renombrar usuario_id a id_users
    op.alter_column(
        'consultas',
        'usuario_id',
        new_column_name='id_users',
        existing_type=sa.Integer,
        existing_nullable=False
    )
