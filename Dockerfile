# Render production image: React build + Django API in one service.

# ============================================================
# Stage 1: Build React frontend
# ============================================================
FROM node:20-alpine AS frontend

WORKDIR /app/frontend

COPY frontend/Tourism/package*.json ./
RUN npm ci

COPY frontend/Tourism/ ./

ARG VITE_SITE_URL=""
ENV VITE_SITE_URL=$VITE_SITE_URL

RUN npm run build


# ============================================================
# Stage 2: Django backend + production server
# ============================================================
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Install system dependencies required by Python packages
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libjpeg-dev \
    zlib1g-dev \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY Tourism/requirements.txt /app/Tourism/
RUN pip install --no-cache-dir -r /app/Tourism/requirements.txt

# Copy Django project
COPY Tourism/ /App/Tourism/
# The built SPA is served from the site root by WhiteNoise (WHITENOISE_ROOT):
# /, /assets/*, /sw.js, /manifest.webmanifest; deep links fall back to
# index.html via Tourism/spa.py.
COPY --from=frontend /app/frontend/dist /app/Tourism/frontend_dist/
# Published seed database (installed on first start by the entrypoint when the
# SQLite volume is empty) and the start-up script.
COPY downloads/nepal-tourism-seed.sqlite3.gz downloads/nepal-tourism-seed.sqlite3.gz.sha256 /app/downloads/
COPY docker/entrypoint.sh /usr/local/bin/ny-entrypoint
RUN chmod +x /usr/local/bin/ny-entrypoint

# Copy compiled React frontend into Django static directory
COPY --from=frontend /app/frontend/dist /app/Tourism/frontend_dist/

# Move into Django project
WORKDIR /app/Tourism

# Create directories required by the application
RUN mkdir -p /var/lib/tourism/media \
    /var/lib/tourism/data

# Collect Django static files
RUN python manage.py collectstatic --noinput

# Render exposes the PORT environment variable
EXPOSE 8000

# ASGI (daphne) so the live-chat WebSocket at /ws/chat/<id>/ works; HTTP is
# the same Django app. CHANNEL_LAYERS is in-memory, so run ONE process per
# container (scale with more containers + a Redis channel layer).
ENTRYPOINT ["ny-entrypoint"]
CMD ["daphne", "-b", "0.0.0.0", "-p", "8000", "Tourism.asgi:application"]
