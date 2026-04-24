#!/bin/sh
set -e

# Default runtime options
: "${PORT:=8000}"
: "${GUNICORN_WORKERS:=4}"
: "${GUNICORN_TIMEOUT:=300}"

# Display environment info for debugging
echo "[INFO] Starting Nisira Assistant Backend"
echo "[INFO] Port: ${PORT}"
echo "[INFO] Workers: ${GUNICORN_WORKERS}"
echo "[INFO] Timeout: ${GUNICORN_TIMEOUT}s"

# Wait for database to be ready
echo "[INFO] Waiting for database..."
until python -c "import sys; import psycopg2; psycopg2.connect('${DATABASE_URL}'); sys.exit(0)" 2>/dev/null; do
  echo "Database is unavailable - sleeping"
  sleep 2
done
echo "[OK] Database is ready"

# Run migrations
echo "[INFO] Running migrations..."
python manage.py migrate --noinput

# Create superuser if needed (only in development)
if [ "${CREATE_SUPERUSER}" = "true" ]; then
  echo "[INFO] Creating superuser..."
  python manage.py shell -c "
from django.contrib.auth import get_user_model;
User = get_user_model();
User.objects.filter(username='admin').exists() or User.objects.create_superuser('admin', 'admin@example.com', 'admin')
" || true
fi

# Initialize RAG system if requested
if [ "${INIT_RAG}" = "true" ]; then
  echo "[INFO] Initializing RAG system..."
  python manage.py rag_manage init || true
fi

# Collect static files
echo "[INFO] Collecting static files..."
mkdir -p /app/staticfiles || true
python manage.py collectstatic --noinput || true

echo "[INFO] Launching Gunicorn on port ${PORT}"
exec gunicorn core.wsgi:application \
  --bind 0.0.0.0:${PORT} \
  --workers ${GUNICORN_WORKERS} \
  --timeout ${GUNICORN_TIMEOUT} \
  --access-logfile - \
  --error-logfile - \
  --log-level info
