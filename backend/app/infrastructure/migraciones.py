"""Migraciones SQL idempotentes aplicadas al arrancar la aplicación.

Cada bloque puede ejecutarse N veces sin efectos secundarios: usa IF NOT EXISTS,
ON CONFLICT DO NOTHING, o validaciones previas en information_schema.

Cuando se necesite hacer cambios estructurales mayores se recomienda migrar a
Alembic. Por ahora este enfoque es suficiente y elimina dependencias externas.
"""
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncConnection

from app.infrastructure.database import motor_bd


async def _limpiar_columnas_legado(conn: AsyncConnection) -> None:
    """Elimina la columna `role` y el enum `rolusuario` que ya no se usan.

    El rol del usuario ahora se determina exclusivamente por `rol_id` que
    apunta a la tabla `roles`. Mantener la columna vieja causaba confusión.
    """
    await conn.execute(text("ALTER TABLE users DROP COLUMN IF EXISTS role"))
    await conn.execute(text("DROP TYPE IF EXISTS rolusuario"))


async def _crear_tabla_carpetas(conn: AsyncConnection) -> None:
    await conn.execute(text("""
        CREATE TABLE IF NOT EXISTS carpetas (
            id          SERIAL PRIMARY KEY,
            nombre      VARCHAR(255) UNIQUE NOT NULL,
            descripcion TEXT,
            created_at  TIMESTAMPTZ DEFAULT NOW()
        )
    """))
    await conn.execute(text("""
        DO $$ BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns
                 WHERE table_name = 'transfers' AND column_name = 'carpeta_id'
            ) THEN
                ALTER TABLE transfers
                    ADD COLUMN carpeta_id INTEGER REFERENCES carpetas(id) ON DELETE SET NULL;
                CREATE INDEX ix_transfers_carpeta_id ON transfers(carpeta_id);
            END IF;
        END $$
    """))


async def _crear_tabla_puertos(conn: AsyncConnection) -> None:
    await conn.execute(text("""
        CREATE TABLE IF NOT EXISTS puertos (
            id          SERIAL PRIMARY KEY,
            nombre      VARCHAR(255) UNIQUE NOT NULL,
            descripcion TEXT,
            created_at  TIMESTAMPTZ DEFAULT NOW()
        )
    """))
    await conn.execute(text("""
        DO $$ BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns
                 WHERE table_name = 'carpetas' AND column_name = 'puerto_id'
            ) THEN
                ALTER TABLE carpetas
                    ADD COLUMN puerto_id INTEGER REFERENCES puertos(id) ON DELETE SET NULL;
                CREATE INDEX ix_carpetas_puerto_id ON carpetas(puerto_id);
            END IF;
        END $$
    """))
    await conn.execute(text("""
        DO $$ BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns
                 WHERE table_name = 'transfers' AND column_name = 'puerto_id'
            ) THEN
                ALTER TABLE transfers
                    ADD COLUMN puerto_id INTEGER REFERENCES puertos(id) ON DELETE SET NULL;
                CREATE INDEX ix_transfers_puerto_id ON transfers(puerto_id);
            END IF;
        END $$
    """))


async def _agregar_marino_transfers(conn: AsyncConnection) -> None:
    await conn.execute(text("""
        DO $$ BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns
                 WHERE table_name = 'transfers' AND column_name = 'marino'
            ) THEN
                ALTER TABLE transfers ADD COLUMN marino VARCHAR(255);
            END IF;
        END $$
    """))


async def _crear_tablas_permisos_y_roles(conn: AsyncConnection) -> None:
    await conn.execute(text("""
        CREATE TABLE IF NOT EXISTS permisos (
            id          SERIAL PRIMARY KEY,
            codigo      VARCHAR(50) UNIQUE NOT NULL,
            nombre      VARCHAR(150) NOT NULL,
            descripcion TEXT,
            created_at  TIMESTAMPTZ DEFAULT NOW()
        )
    """))
    await conn.execute(text("CREATE INDEX IF NOT EXISTS ix_permisos_codigo ON permisos(codigo)"))

    await conn.execute(text("""
        CREATE TABLE IF NOT EXISTS roles (
            id          SERIAL PRIMARY KEY,
            nombre      VARCHAR(100) UNIQUE NOT NULL,
            descripcion TEXT,
            es_sistema  BOOLEAN NOT NULL DEFAULT FALSE,
            created_at  TIMESTAMPTZ DEFAULT NOW()
        )
    """))
    await conn.execute(text("CREATE INDEX IF NOT EXISTS ix_roles_nombre ON roles(nombre)"))

    await conn.execute(text("""
        CREATE TABLE IF NOT EXISTS roles_permisos (
            id         SERIAL PRIMARY KEY,
            rol_id     INTEGER NOT NULL REFERENCES roles(id) ON DELETE CASCADE,
            permiso_id INTEGER NOT NULL REFERENCES permisos(id) ON DELETE CASCADE,
            CONSTRAINT uq_roles_permisos_rol_permiso UNIQUE (rol_id, permiso_id)
        )
    """))
    await conn.execute(text("CREATE INDEX IF NOT EXISTS ix_roles_permisos_rol_id     ON roles_permisos(rol_id)"))
    await conn.execute(text("CREATE INDEX IF NOT EXISTS ix_roles_permisos_permiso_id ON roles_permisos(permiso_id)"))

    await conn.execute(text("""
        DO $$ BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns
                 WHERE table_name = 'users' AND column_name = 'rol_id'
            ) THEN
                ALTER TABLE users
                    ADD COLUMN rol_id INTEGER REFERENCES roles(id) ON DELETE SET NULL;
                CREATE INDEX ix_users_rol_id ON users(rol_id);
            END IF;
        END $$
    """))

    # Rol Administrador siempre disponible
    await conn.execute(text("""
        INSERT INTO roles (nombre, descripcion, es_sistema)
        VALUES ('Administrador', 'Rol con acceso administrativo total al sistema.', TRUE)
        ON CONFLICT (nombre) DO NOTHING
    """))


async def _agregar_snapshots_transfers(conn: AsyncConnection) -> None:
    """Columnas snapshot que preservan los datos originales enviados por la naviera."""
    await conn.execute(text("""
        DO $$ BEGIN
            IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                            WHERE table_name='transfers' AND column_name='titulo_original') THEN
                ALTER TABLE transfers ADD COLUMN titulo_original VARCHAR(255);
            END IF;
            IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                            WHERE table_name='transfers' AND column_name='mensaje_original') THEN
                ALTER TABLE transfers ADD COLUMN mensaje_original TEXT;
            END IF;
            IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                            WHERE table_name='transfers' AND column_name='destinatario_original') THEN
                ALTER TABLE transfers ADD COLUMN destinatario_original VARCHAR(255);
            END IF;
        END $$
    """))


async def _agregar_metadatos_archivos(conn: AsyncConnection) -> None:
    """Marca quién subió cada archivo y si es original o agregado en corrección."""
    await conn.execute(text("""
        DO $$ BEGIN
            IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                            WHERE table_name='transfer_files' AND column_name='subido_por_id') THEN
                ALTER TABLE transfer_files
                    ADD COLUMN subido_por_id INTEGER REFERENCES users(id) ON DELETE SET NULL;
                CREATE INDEX ix_transfer_files_subido_por_id ON transfer_files(subido_por_id);
            END IF;
            IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                            WHERE table_name='transfer_files' AND column_name='es_original') THEN
                ALTER TABLE transfer_files
                    ADD COLUMN es_original BOOLEAN NOT NULL DEFAULT TRUE;
            END IF;
        END $$
    """))


async def _convertir_status_a_varchar(conn: AsyncConnection) -> None:
    """Migra el enum `estadotransferencia` a VARCHAR(20) manteniendo los valores.

    El enum almacenaba los NAMES Python (ACTIVA, EXPIRADA…). Los convertimos a
    los valores en español lowercase usados por el código actual.
    """
    await conn.execute(text("""
        DO $$
        DECLARE
            col_type TEXT;
        BEGIN
            SELECT data_type INTO col_type
              FROM information_schema.columns
             WHERE table_name='transfers' AND column_name='status';
            IF col_type = 'USER-DEFINED' THEN
                ALTER TABLE transfers ALTER COLUMN status DROP DEFAULT;
                ALTER TABLE transfers
                    ALTER COLUMN status TYPE VARCHAR(20)
                    USING (
                        CASE status::TEXT
                            WHEN 'ACTIVA'    THEN 'active'
                            WHEN 'EXPIRADA'  THEN 'expired'
                            WHEN 'ELIMINADA' THEN 'deleted'
                            WHEN 'BORRADOR'  THEN 'draft'
                            ELSE lower(status::TEXT)
                        END
                    );
                ALTER TABLE transfers ALTER COLUMN status SET DEFAULT 'active';
                ALTER TABLE transfers ALTER COLUMN status SET NOT NULL;
                DROP TYPE IF EXISTS estadotransferencia;
            END IF;
        END $$
    """))
    await conn.execute(text("CREATE INDEX IF NOT EXISTS ix_transfers_status_varchar ON transfers(status)"))


async def _agregar_observaciones_transfers(conn: AsyncConnection) -> None:
    """Notas internas del Sector Pacífico (motivo de devolución, etc.)."""
    await conn.execute(text("""
        DO $$ BEGIN
            IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                            WHERE table_name='transfers' AND column_name='observaciones') THEN
                ALTER TABLE transfers ADD COLUMN observaciones TEXT;
            END IF;
        END $$
    """))


async def _sembrar_permisos_y_roles_flujo(conn: AsyncConnection) -> None:
    """Permisos del flujo Naviera / Sector Pacífico + roles asociados."""
    await conn.execute(text("""
        INSERT INTO permisos (codigo, nombre, descripcion) VALUES
            ('T-CREAR-BASICA',     'Crear borrador',
             'Sube archivos con título/mensaje/destinatario. No completa puerto/naviera/marino. Queda en borrador.'),
            ('T-PROCESAR-PACIFICO','Procesar cola',
             'Ve cola de borradores, asigna puerto/naviera/marino, edita y reenvía.'),
            ('T-CREAR-COMPLETA',   'Crear envío directo',
             'Crea transferencia directamente con todos los campos y dispara correo.')
        ON CONFLICT (codigo) DO NOTHING
    """))
    # Normalización de nombres legacy a versiones más cortas
    await conn.execute(text(
        "UPDATE permisos SET nombre = 'Crear borrador'      WHERE codigo = 'T-CREAR-BASICA'      AND nombre = 'Crear transferencia básica'"
    ))
    await conn.execute(text(
        "UPDATE permisos SET nombre = 'Procesar cola'        WHERE codigo = 'T-PROCESAR-PACIFICO' AND nombre = 'Procesar transferencias en cola'"
    ))
    await conn.execute(text(
        "UPDATE permisos SET nombre = 'Crear envío directo' WHERE codigo = 'T-CREAR-COMPLETA'    AND nombre = 'Crear transferencia completa'"
    ))

    await conn.execute(text("""
        INSERT INTO roles (nombre, descripcion, es_sistema) VALUES
            ('Naviera',
             'Sube archivos en estado borrador con título/mensaje/destinatario para que el Sector Pacífico complete los datos.',
             TRUE),
            ('Sector Pacífico',
             'Procesa los borradores enviados por las navieras: asigna puerto/naviera/marino, edita archivos y reenvía con notificación al destinatario.',
             TRUE)
        ON CONFLICT (nombre) DO NOTHING
    """))
    await conn.execute(text("""
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


async def _crear_tabla_usuarios_puertos(conn: AsyncConnection) -> None:
    """Tabla puente para asignar puertos a operadores del muelle.

    Un operador (usuario con permiso T-PROCESAR-MUELLE) solo ve en su bandeja
    las transferencias cuyos puertos estén en esta lista. El permiso y el rol
    se crean manualmente desde /admin/roles; esta tabla es la infraestructura
    que se necesita antes de que el admin pueda asignar puertos.
    """
    await conn.execute(text("""
        CREATE TABLE IF NOT EXISTS usuarios_puertos (
            usuario_id INTEGER REFERENCES users(id)    ON DELETE CASCADE,
            puerto_id  INTEGER REFERENCES puertos(id) ON DELETE CASCADE,
            PRIMARY KEY (usuario_id, puerto_id)
        )
    """))
    await conn.execute(text(
        "CREATE INDEX IF NOT EXISTS ix_usuarios_puertos_usuario ON usuarios_puertos(usuario_id)"
    ))
    await conn.execute(text(
        "CREATE INDEX IF NOT EXISTS ix_usuarios_puertos_puerto  ON usuarios_puertos(puerto_id)"
    ))


async def aplicar_migraciones() -> None:
    """Aplica todas las migraciones en orden. Idempotente."""
    async with motor_bd.begin() as conn:
        await _limpiar_columnas_legado(conn)
        await _crear_tabla_carpetas(conn)
        await _crear_tabla_puertos(conn)
        await _agregar_marino_transfers(conn)
        await _crear_tablas_permisos_y_roles(conn)
        await _agregar_snapshots_transfers(conn)
        await _agregar_metadatos_archivos(conn)
        await _convertir_status_a_varchar(conn)
        await _agregar_observaciones_transfers(conn)
        await _sembrar_permisos_y_roles_flujo(conn)
        await _crear_tabla_usuarios_puertos(conn)
