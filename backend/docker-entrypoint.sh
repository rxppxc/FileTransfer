#!/usr/bin/env bash
set -euo pipefail

echo "==> Aplicando migraciones Alembic..."
alembic upgrade head

echo "==> Iniciando uvicorn..."
exec uvicorn app.main:aplicacion --host 0.0.0.0 --port 8000
