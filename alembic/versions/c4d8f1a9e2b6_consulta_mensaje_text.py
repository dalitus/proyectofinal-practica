"""widen consultas mensaje and respuesta to TEXT

A real question does not fit in 255 characters and MySQL raises error 1406
instead of truncating, so the buyer would lose what they wrote (D-048). The
service caps the answer at 2000 characters.

Revision ID: c4d8f1a9e2b6
Revises: b3c9e2d5a1f7
Create Date: 2026-10-30 00:45:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel


# revision identifiers, used by Alembic.
revision: str = "c4d8f1a9e2b6"
down_revision: Union[str, Sequence[str], None] = "b3c9e2d5a1f7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Widen both columns; existing values fit either way."""
    op.alter_column(
        "consultas",
        "mensaje",
        existing_type=sqlmodel.sql.sqltypes.AutoString(),
        type_=sa.Text(),
        existing_nullable=False,
    )
    op.alter_column(
        "consultas",
        "respuesta",
        existing_type=sqlmodel.sql.sqltypes.AutoString(),
        type_=sa.Text(),
        existing_nullable=True,
    )


def downgrade() -> None:
    """Back to VARCHAR(255): rows longer than that would fail, which is the point."""
    op.alter_column(
        "consultas",
        "respuesta",
        existing_type=sa.Text(),
        type_=sqlmodel.sql.sqltypes.AutoString(),
        existing_nullable=True,
    )
    op.alter_column(
        "consultas",
        "mensaje",
        existing_type=sa.Text(),
        type_=sqlmodel.sql.sqltypes.AutoString(),
        existing_nullable=False,
    )
