"""sembrar_roles_y_permisos

Datos semilla del flujo Naviera → Sector Pacífico → Muelle: rol Administrador,
roles Naviera / Sector Pacífico y sus permisos base. Sin esto, un ambiente
nuevo creado solo con `alembic upgrade head` queda sin ningún rol — nadie
podría llegar a ser Administrador. Esta migración es lo único que reemplaza
a las antiguas migraciones runtime (`_crear_tablas_permisos_y_roles` y
`_sembrar_permisos_y_roles_flujo` en infrastructure/migraciones.py, retirado).

El permiso T-PROCESAR-MUELLE y el rol Muelle/Operador se siguen creando a
mano desde /admin/roles — es a propósito (ver CLAUDE.md), no se siembran acá.

Revision ID: 188d47e11db0
Revises: d93ac0ca2d1c
Create Date: 2026-07-06

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '188d47e11db0'
down_revision: Union[str, None] = 'd93ac0ca2d1c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(sa.text("""
        INSERT INTO roles (nombre, descripcion, es_sistema)
        VALUES ('Administrador', 'Rol con acceso administrativo total al sistema.', TRUE)
        ON CONFLICT (nombre) DO NOTHING
    """))

    op.execute(sa.text("""
        INSERT INTO permisos (codigo, nombre, descripcion) VALUES
            ('T-CREAR-BASICA',     'Crear borrador',
             'Sube archivos con título/mensaje/destinatario. No completa puerto/naviera/marino. Queda en borrador.'),
            ('T-PROCESAR-PACIFICO','Procesar cola',
             'Ve cola de borradores, asigna puerto/naviera/marino, edita y reenvía.'),
            ('T-CREAR-COMPLETA',   'Crear envío directo',
             'Crea transferencia directamente con todos los campos y dispara correo.')
        ON CONFLICT (codigo) DO NOTHING
    """))

    op.execute(sa.text("""
        INSERT INTO roles (nombre, descripcion, es_sistema) VALUES
            ('Naviera',
             'Sube archivos en estado borrador con título/mensaje/destinatario para que el Sector Pacífico complete los datos.',
             TRUE),
            ('Sector Pacífico',
             'Procesa los borradores enviados por las navieras: asigna puerto/naviera/marino, edita archivos y reenvía con notificación al destinatario.',
             TRUE)
        ON CONFLICT (nombre) DO NOTHING
    """))

    op.execute(sa.text("""
        INSERT INTO roles_permisos (rol_id, permiso_id)
        SELECT r.id, p.id
          FROM roles r
          JOIN permisos p ON (
                   (r.nombre = 'Administrador'    AND p.codigo IN ('T-CREAR-BASICA','T-PROCESAR-PACIFICO','T-CREAR-COMPLETA'))
                OR (r.nombre = 'Naviera'          AND p.codigo = 'T-CREAR-BASICA')
                OR (r.nombre = 'Sector Pacífico'  AND p.codigo = 'T-PROCESAR-PACIFICO')
              )
         ON CONFLICT ON CONSTRAINT uq_roles_permisos_rol_permiso DO NOTHING
    """))


def downgrade() -> None:
    op.execute(sa.text("""
        DELETE FROM roles_permisos
         WHERE rol_id IN (SELECT id FROM roles WHERE nombre IN ('Administrador', 'Naviera', 'Sector Pacífico'))
    """))
    op.execute(sa.text("DELETE FROM permisos WHERE codigo IN ('T-CREAR-BASICA', 'T-PROCESAR-PACIFICO', 'T-CREAR-COMPLETA')"))
    op.execute(sa.text("DELETE FROM roles WHERE nombre IN ('Administrador', 'Naviera', 'Sector Pacífico')"))
