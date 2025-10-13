# Backend Dockerfile for Django RAG system
# ---------------------------------------
# Multi-stage builds are not essential here, but we keep the image slim by
# basing it on python:3.12-slim and installing only the required system deps.

FROM python:3.12-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# System dependencies required for building some Python packages (mysqlclient, pillow, etc.)
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
       build-essential \
       default-libmysqlclient-dev \
       libjpeg62-turbo-dev \
       zlib1g-dev \
       libpq-dev \
       curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies first to leverage Docker layer caching
COPY requirements.txt ./
RUN pip install --upgrade pip \
    && pip install -r requirements.txt

# Copy project files into the image
COPY . /app

# Ensure environment files and credentials are present in the container
# NOTE: embedding secrets in images is insecure; prefer runtime secrets in production.
COPY .env /app/.env
COPY credentials.json /app/credentials.json

# Collect static assets during build so the runtime container is ready to serve them
RUN DJANGO_SETTINGS_MODULE=core.build_settings python manage.py collectstatic --noinput

# Entrypoint script handles migrations and starts Gunicorn
COPY docker/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

EXPOSE 8000

CMD ["/entrypoint.sh"]
