# Backend Dockerfile Optimizado para Producción
# Multi-stage build para reducir tamaño de imagen final

FROM python:3.12-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# System dependencies
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
       build-essential \
       default-libmysqlclient-dev \
       libpq-dev \
       curl \
       ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt ./
RUN pip install --upgrade pip \
    && pip install -r requirements.txt \
    && pip install psycopg2-binary gunicorn whitenoise \
    && rm -rf /root/.cache/pip

# Copy project files
COPY . /app/

# Create necessary directories
RUN mkdir -p /app/data/documents /app/data/processed /app/chroma_db /app/staticfiles

# Collect static files
RUN python manage.py collectstatic --noinput --settings=core.production_settings || true

# Make entrypoint executable
RUN chmod +x /app/docker/entrypoint.sh

# Create non-root user
RUN useradd -m -u 1000 django && chown -R django:django /app
USER django

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
  CMD curl -f http://localhost:8000/api/health/ || exit 1

CMD ["/app/docker/entrypoint.sh"]

