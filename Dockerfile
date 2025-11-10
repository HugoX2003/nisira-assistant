# Combined Dockerfile for deploying the full stack to Heroku or any single-container platform
# ------------------------------------------------------------------------------------------
# Stage 1: build the React frontend
FROM node:20-alpine AS frontend-build
WORKDIR /frontend

COPY frontend/package*.json ./
RUN npm install
COPY frontend/ ./

ARG REACT_APP_API_URL
ENV REACT_APP_API_URL=${REACT_APP_API_URL}
RUN npm run build

# Stage 2: build the Django backend with the compiled frontend assets
FROM python:3.12-slim AS backend

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    DJANGO_SETTINGS_MODULE=core.settings \
    PORT=8000

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
       build-essential \
       default-libmysqlclient-dev \
       libjpeg62-turbo-dev \
       zlib1g-dev \
       libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install dependencies first
COPY backend/requirements.txt ./
RUN pip install --upgrade pip \
    && pip install -r requirements.txt

# Copy backend source code
COPY backend/ /app/

# Copy credential files REMOVED - using GOOGLE_CREDENTIALS_JSON env var instead
# credentials.json will be created automatically from env var if needed

# Insert built frontend into Django static directory before collectstatic
RUN mkdir -p /app/core/static/frontend
COPY --from=frontend-build /frontend/build/ /app/core/static/frontend/

# Collect static assets so Gunicorn + WhiteNoise can serve them
RUN DJANGO_SETTINGS_MODULE=core.build_settings python manage.py collectstatic --noinput

COPY backend/docker/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

EXPOSE 8000
CMD ["/entrypoint.sh"]
