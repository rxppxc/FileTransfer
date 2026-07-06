@echo off
REM ════════════════════════════════════════════════════════════════════════════
REM FileTransfer SNM — Arranque PRODUCCIÓN
REM   - Sin --reload (estabilidad y CPU)
REM   - Múltiples workers (ajustar al hardware)
REM   - Logs sin acceso a colores ANSI (mejor en archivos)
REM Antes de ejecutar verificar que `.env` tenga APP_ENV=production
REM ════════════════════════════════════════════════════════════════════════════
REM SEGURIDAD: --forwarded-allow-ips define QUÉ orígenes pueden falsear la IP
REM del cliente vía X-Forwarded-For. Con "*" cualquiera puede spoofear su IP y
REM evadir el rate limit de /login y /download, además de ensuciar la auditoría.
REM Poné aquí la IP REAL del reverse proxy (IIS/nginx). Si el proxy corre en el
REM mismo servidor, 127.0.0.1 es correcto. Sobrescribible con la variable de
REM entorno FORWARDED_ALLOW_IPS.
if not defined FORWARDED_ALLOW_IPS set FORWARDED_ALLOW_IPS=127.0.0.1
cd /d %~dp0backend
call venv\Scripts\activate
uvicorn app.main:aplicacion ^
  --host 0.0.0.0 ^
  --port 8000 ^
  --workers 4 ^
  --proxy-headers ^
  --forwarded-allow-ips=%FORWARDED_ALLOW_IPS% ^
  --no-server-header
pause
