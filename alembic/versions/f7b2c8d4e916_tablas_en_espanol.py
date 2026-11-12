"""rename tables to Spanish names

Three tables still carried English or run-together names: ``user_profiles``,
``pedido_items`` and the implicit ``ubicacionlocal`` that SQLModel derived from
the class name. D-055 sets table names in Spanish, so they become
``perfiles_usuario``, ``lineas_pedido`` and ``ubicaciones_locales``.

``stocks`` stays as is (accepted anglicism) and ``localuser`` /
``localauthsession`` belong to ``reflex_local_auth``, so they are not renamed.

The index names follow the table name, so each one is renamed with
``ALTER TABLE ... RENAME INDEX``: dropping and recreating them fails because
MySQL needs the index to support the foreign keys (error 1553).

Revision ID: f7b2c8d4e916
Revises: e6f1a4c8b2d9
Create Date: 2026-11-12 00:00:00.000000

"""

from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = "f7b2c8d4e916"
down_revision: Union[str, Sequence[str], None] = "e6f1a4c8b2d9"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Rename the tables and their indexes; no data moves."""
    op.execute(
        "ALTER TABLE user_profiles "
        "RENAME INDEX ix_user_profiles_email TO ix_perfiles_usuario_email, "
        "RENAME INDEX ix_user_profiles_is_admin TO ix_perfiles_usuario_is_admin, "
        "RENAME INDEX ix_user_profiles_local_user_id TO ix_perfiles_usuario_local_user_id"
    )
    op.rename_table("user_profiles", "perfiles_usuario")

    op.execute(
        "ALTER TABLE pedido_items "
        "RENAME INDEX ix_pedido_items_pedido_id TO ix_lineas_pedido_pedido_id, "
        "RENAME INDEX ix_pedido_items_variante_id TO ix_lineas_pedido_variante_id"
    )
    op.rename_table("pedido_items", "lineas_pedido")

    op.rename_table("ubicacionlocal", "ubicaciones_locales")


def downgrade() -> None:
    """Back to the English names; the indexes follow the table again."""
    op.rename_table("ubicaciones_locales", "ubicacionlocal")

    op.execute(
        "ALTER TABLE lineas_pedido "
        "RENAME INDEX ix_lineas_pedido_pedido_id TO ix_pedido_items_pedido_id, "
        "RENAME INDEX ix_lineas_pedido_variante_id TO ix_pedido_items_variante_id"
    )
    op.rename_table("lineas_pedido", "pedido_items")

    op.execute(
        "ALTER TABLE perfiles_usuario "
        "RENAME INDEX ix_perfiles_usuario_email TO ix_user_profiles_email, "
        "RENAME INDEX ix_perfiles_usuario_is_admin TO ix_user_profiles_is_admin, "
        "RENAME INDEX ix_perfiles_usuario_local_user_id TO ix_user_profiles_local_user_id"
    )
    op.rename_table("perfiles_usuario", "user_profiles")
