@echo off
echo === SNMTransfer - Migraciones de base de datos ===
REM ════════════════════════════════════════════════════════════════════════════
REM Alembic es la única fuente de verdad del esquema (versions/). No hay
REM migraciones runtime aparte — todo el esquema (users, transfers, puertos,
REM roles, permisos, usuarios_puertos y sus ALTERs posteriores) vive en
REM backend/alembic/versions/. Este script solo corre `alembic upgrade head`.
REM
REM Para un cambio estructural nuevo: crear la revisión a mano (o con
REM `alembic revision --autogenerate` si el modelo ya cambió) y revisarla
REM antes de aplicarla.
REM ════════════════════════════════════════════════════════════════════════════
cd /d %~dp0backend
call venv\Scripts\activate
alembic upgrade head
echo === Listo ===
pause
