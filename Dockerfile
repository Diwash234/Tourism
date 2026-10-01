# Render production image: React build + Django API in one service.

# ============================================================
# Stage 1: Build React frontend
# ============================================================
FROM node:20-alpine AS frontend

WORKDIR /app/frontend

COPY frontend/Tourism/package.json ./package.json
COPY frontend/Tourism/package-lock.json ./package-lock.json

# Keep the build deterministic. npm 10 + lockfile v3 is supported by Node 20.
RUN npm --version && node --version && npm ci --no-audit --no-fund

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
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY Tourism/requirements.txt /app/Tourism/
RUN pip install --no-cache-dir -r /app/Tourism/requirements.txt

# Copy Django project
COPY Tourism/ /app/Tourism/

# The built SPA is served from the site root by WhiteNoise (WHITENOISE_ROOT):
# /, /assets/*, /sw.js, /manifest.webmanifest; deep links fall back to
# index.html via Tourism/spa.py.
COPY --from=frontend /app/frontend/dist /app/Tourism/frontend_dist/

# Published seed database (installed on first start by the entrypoint when the
# SQLite volume is empty) and the start-up script.
COPY downloads/nepal-tourism-seed.sqlite3.gz downloads/nepal-tourism-seed.sqlite3.gz.sha256 /app/downloads/
COPY docker/entrypoint.sh /usr/local/bin/ny-entrypoint
RUN chmod +x /usr/local/bin/ny-entrypoint

# Move into Django project
WORKDIR /app/Tourism

# Create directories required by the application.
# MEDIA_ROOT defaults to <BASE_DIR>/media = /app/Tourism/media (settings.py);
# the health check reports it unwritable and 503s every Render deploy if this
# directory is missing. /var/lib/tourism/* is kept for configs that point
# MEDIA_ROOT/MEDIA at those paths via env.
RUN mkdir -p /app/Tourism/media \
    /var/lib/tourism/media \
    /var/lib/tourism/data

# ML microservice source, models and data: budget estimator (budget_model.joblib),
# itinerary/recommendation/safety engines, and the OSM amenity CSV that
# import_emergency_services reads (hospitals, clinics, pharmacies, police).
# None of ml_service/ was in the image before -- so budget/itinerary said
# "not available" in production and the emergency import crashed the boot.
# Its Python deps (fastapi/uvicorn/sklearn/pandas/networkx) are already in
# Tourism/requirements.txt; the entrypoint starts uvicorn on :8001 in the
# background, which is where ML_SERVICE_URL points.
COPY ml_service/ /app/ml_service/

# Collect Django static files
RUN python manage.py collectstatic --noinput

# Render exposes the PORT environment variable
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/health/ || exit 1

ENTRYPOINT ["ny-entrypoint"]
CMD ["daphne", "-b", "0.0.0.0", "-p", "8000", "Tourism.asgi:application"]
