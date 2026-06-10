"""Crear tabla consultas

Revision ID: b691ec95a347
Revises: 5f9e50a827cb
Create Date: 2026-05-31 14:24:25.632109

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'b691ec95a347'
down_revision = 'b7bb9f50bc07'   # ajusta según tu última migración aplicada
branch_labels = None
depends_on = None

def upgrade() -> None:
    op.create_table(
        "consultas",
        sa.Column("id_consulta", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("usuario_id", sa.Integer, sa.ForeignKey("users.id"), nullable=False),
        sa.Column("id_gerente", sa.Integer, sa.ForeignKey("gerentes.id_gerente"), nullable=True),
        sa.Column("asunto", sa.String(255), nullable=False),
        sa.Column("mensaje", sa.String(255), nullable=False),
        sa.Column("respuesta", sa.String(255), nullable=True),
        sa.Column("fecha_creacion", sa.String(255), nullable=True),
        sa.Column("fecha_respuesta", sa.String(255), nullable=True),
    )

def downgrade() -> None:
    op.drop_table("consultas")