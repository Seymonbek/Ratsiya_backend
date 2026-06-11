#!/bin/sh
set -e

export PYTHONPATH=/app

WORKERS=${UVICORN_WORKERS:-1}

echo "Database tayyor bo'lishini kutmoqda..."
until python -c "import socket; s=socket.socket(); s.connect(('db', 5432))" 2>/dev/null; do
  echo "  PostgreSQL hali tayyor emas, 1 soniya kutilmoqda..."
  sleep 1
done
echo "Database tayyor."

echo "Migratsiyalar qo'llanmoqda..."
alembic upgrade head

echo "Server ishga tushmoqda (workers=$WORKERS)..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers "$WORKERS"
