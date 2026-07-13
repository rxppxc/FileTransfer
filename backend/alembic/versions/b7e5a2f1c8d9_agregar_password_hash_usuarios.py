"""agregar_password_hash_usuarios

Agrega `users.password_hash`, usada únicamente por los usuarios LOCAL de
prueba creados desde /admin/usuarios/local (atajo temporal para probar
roles/permisos sin Active Directory — ver ServicioAutenticacion.login).
Se elimina junto con ese flujo antes de pasar el sistema a producción.

Revision ID: b7e5a2f1c8d9
Revises: a1f3c9d7e2b4
Create Date: 2026-07-13

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'b7e5a2f1c8d9'
down_revision: Union[str, None] = 'a1f3c9d7e2b4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('users', sa.Column('password_hash', sa.String(length=255), nullable=True))


def downgrade() -> None:
    op.drop_column('users', 'password_hash')
