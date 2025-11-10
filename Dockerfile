# Backend-only Dockerfile for Digital Ocean deployment
# Frontend is deployed separately to Heroku
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    DJANGO_SETTINGS_MODULE=core.settings \
    PORT=8000

WORKDIR /app

# Install system dependencies
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
       build-essential \
       default-libmysqlclient-dev \
       libjpeg62-turbo-dev \
       zlib1g-dev \
       libpq-dev \
       curl \
    && rm -rf /var/lib/apt/lists/*

# Install dependencies first (layer caching)
COPY backend/requirements.txt ./
RUN pip install --upgrade pip \
    && pip install -r requirements.txt

# Copy backend source code
COPY backend/ /app/

# Collect static assets (Django admin only, no frontend)
RUN DJANGO_SETTINGS_MODULE=core.build_settings python manage.py collectstatic --noinput

EXPOSE 8000

# Run migrations and start Gunicorn directly
CMD python manage.py migrate --noinput && \
    gunicorn core.wsgi:application \
    --bind 0.0.0.0:${PORT:-8000} \
    --workers ${GUNICORN_WORKERS:-2} \
    --timeout ${GUNICORN_TIMEOUT:-300} \
    --access-logfile - \
    --error-logfile - \
    --log-level info
