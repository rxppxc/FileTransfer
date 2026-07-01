@echo off
REM ════════════════════════════════════════════════════════════════════════════
REM FileTransfer SNM — Arranque PRODUCCIÓN
REM   - Sin --reload (estabilidad y CPU)
REM   - Múltiples workers (ajustar al hardware)
REM   - Logs sin acceso a colores ANSI (mejor en archivos)
REM Antes de ejecutar verificar que `.env` tenga APP_ENV=production
REM ════════════════════════════════════════════════════════════════════════════
cd /d %~dp0backend
call venv\Scripts\activate
uvicorn app.main:aplicacion ^
  --host 0.0.0.0 ^
  --port 8000 ^
  --workers 4 ^
  --proxy-headers ^
  --forwarded-allow-ips=* ^
  --no-server-header
pause
