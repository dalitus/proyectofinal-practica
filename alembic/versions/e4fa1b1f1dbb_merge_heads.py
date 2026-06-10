"""Merge heads

Revision ID: e4fa1b1f1dbb
Revises: 5f9e50a827cb, b691ec95a347
Create Date: 2026-05-31 14:30:33.244575

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e4fa1b1f1dbb'
down_revision: Union[str, Sequence[str], None] = ('5f9e50a827cb', 'b691ec95a347')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
