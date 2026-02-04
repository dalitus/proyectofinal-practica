"""empty message

Revision ID: 503db30c0e4d
Revises: add_ubicacion_pedidos, e3dba19ee6bb
Create Date: 2026-02-03 20:44:22.855141

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '503db30c0e4d'
down_revision: Union[str, Sequence[str], None] = ('add_ubicacion_pedidos', 'e3dba19ee6bb')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
