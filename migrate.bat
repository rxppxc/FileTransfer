@echo off
echo === SNMTransfer - Migraciones de base de datos ===
REM ════════════════════════════════════════════════════════════════════════════
REM Reparto de migraciones (leer antes de tocar):
REM   - Alembic (versions/) crea las tablas base: users, transfers, transfer_files
REM     y sus índices. Se aplican UNA vez con `alembic upgrade head`.
REM   - El resto del esquema (carpetas, puertos, permisos, roles, usuarios_puertos
REM     y ALTERs) lo aplican las migraciones runtime idempotentes en
REM     app/infrastructure/migraciones.py, que corren solas al arrancar la app.
REM
REM NO usar `alembic revision --autogenerate` aquí: como las migraciones runtime
REM ya modificaron el esquema, el autogenerate detecta "drift" y genera revisiones
REM espurias/conflictivas. Para un cambio estructural real, crear la revisión a
REM mano y revisarla.
REM ════════════════════════════════════════════════════════════════════════════
cd /d %~dp0backend
call venv\Scripts\activate
alembic upgrade head
echo === Listo ===
pause
