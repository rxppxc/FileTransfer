@echo off
echo === SNMTransfer - Migraciones de base de datos ===
cd /d %~dp0backend
call venv\Scripts\activate
alembic revision --autogenerate -m "initial"
alembic upgrade head
echo === Listo ===
pause
