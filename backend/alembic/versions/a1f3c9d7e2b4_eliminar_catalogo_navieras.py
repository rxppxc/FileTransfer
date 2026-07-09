"""eliminar_catalogo_navieras

La Naviera deja de ser un catálogo administrado (tabla `carpetas`, FK desde
`transfers.carpeta_id`) y pasa a ser texto libre que escribe Sector Pacífico,
igual que el campo `marino` que ya existía. Decisión del dueño del sistema:
las navieras no se asignan de una lista predefinida.

Antes de tocar el esquema, se migran los nombres existentes de
`carpetas.nombre` hacia la nueva columna `transfers.naviera` para no perder
el dato histórico. Luego se elimina la FK/columna `carpeta_id` y la tabla
`carpetas` por completo.

Revision ID: a1f3c9d7e2b4
Revises: 188d47e11db0
Create Date: 2026-07-09

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'a1f3c9d7e2b4'
down_revision: Union[str, None] = '188d47e11db0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('transfers', sa.Column('naviera', sa.String(length=255), nullable=True))

    op.execute(sa.text("""
        UPDATE transfers
        SET naviera = carpetas.nombre
        FROM carpetas
        WHERE transfers.carpeta_id = carpetas.id
    """))

    op.drop_index(op.f('ix_transfers_carpeta_id'), table_name='transfers')
    op.drop_constraint('transfers_carpeta_id_fkey', 'transfers', type_='foreignkey')
    op.drop_column('transfers', 'carpeta_id')

    op.drop_index(op.f('ix_carpetas_puerto_id'), table_name='carpetas')
    op.drop_index(op.f('ix_carpetas_id'), table_name='carpetas')
    op.drop_table('carpetas')


def downgrade() -> None:
    op.create_table(
        'carpetas',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('nombre', sa.String(length=255), nullable=False),
        sa.Column('descripcion', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('puerto_id', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['puerto_id'], ['puertos.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('nombre'),
    )
    op.create_index(op.f('ix_carpetas_id'), 'carpetas', ['id'], unique=False)
    op.create_index(op.f('ix_carpetas_puerto_id'), 'carpetas', ['puerto_id'], unique=False)

    op.add_column('transfers', sa.Column('carpeta_id', sa.Integer(), nullable=True))

    # Best-effort: recrea una carpeta por cada nombre de naviera distinto que
    # haya quedado como texto libre (sin puerto asignado — ese dato ya no existe
    # a nivel de naviera) y reconecta la FK por nombre.
    op.execute(sa.text("""
        INSERT INTO carpetas (nombre)
        SELECT DISTINCT naviera FROM transfers
        WHERE naviera IS NOT NULL AND naviera <> ''
    """))
    op.execute(sa.text("""
        UPDATE transfers
        SET carpeta_id = carpetas.id
        FROM carpetas
        WHERE transfers.naviera = carpetas.nombre
    """))

    op.create_index(op.f('ix_transfers_carpeta_id'), 'transfers', ['carpeta_id'], unique=False)
    op.create_foreign_key('transfers_carpeta_id_fkey', 'transfers', 'carpetas', ['carpeta_id'], ['id'], ondelete='SET NULL')

    op.drop_column('transfers', 'naviera')
