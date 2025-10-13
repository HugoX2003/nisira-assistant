#!/bin/sh
set -e

# Default runtime options
: "${PORT:=8000}"
: "${GUNICORN_WORKERS:=3}"
: "${GUNICORN_TIMEOUT:=300}"

# Display environment info for debugging (without leaking secrets)
echo "🛠️ Starting Django backend"
echo "📦 Running migrations..."
python manage.py migrate --noinput

# Optionally initialize the RAG system if requested
if [ "${INIT_RAG}" = "true" ]; then
  echo "🔄 Initializing RAG system"
  python manage.py rag_manage init || true
fi

echo "🚀 Launching Gunicorn on port ${PORT}"
exec gunicorn core.wsgi:application \
  --bind 0.0.0.0:${PORT} \
  --workers ${GUNICORN_WORKERS} \
  --timeout ${GUNICORN_TIMEOUT}
