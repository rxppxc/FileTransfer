@echo off
REM ════════════════════════════════════════════════════════════════════════════
REM FileTransfer SNM — Arranque DESARROLLO (con --reload y 1 worker)
REM Para producción usar: start-backend-prod.bat
REM ════════════════════════════════════════════════════════════════════════════
cd /d %~dp0backend
call venv\Scripts\activate
uvicorn app.main:aplicacion --host 0.0.0.0 --port 8000 --reload
pause
