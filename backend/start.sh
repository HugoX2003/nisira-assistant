#!/bin/sh
set -e

echo "[INFO] Running database migrations..."
python manage.py migrate --noinput

echo "[INFO] Starting Gunicorn..."
exec gunicorn core.wsgi:application \
  --bind 0.0.0.0:${PORT:-8000} \
  --workers ${GUNICORN_WORKERS:-2} \
  --timeout ${GUNICORN_TIMEOUT:-300} \
  --access-logfile - \
  --error-logfile - \
  --log-level info
