# --- Build frontend ---
FROM node:20-alpine AS frontend
WORKDIR /app/frontend
COPY frontend/Tourism/package*.json ./
RUN npm ci
COPY frontend/Tourism/ ./
# Public https origin for canonical / Open Graph tags (omit to skip them --
# never falls back to another site's domain). e.g. --build-arg VITE_SITE_URL=https://nepalyatra.example
ARG VITE_SITE_URL=""
ENV VITE_SITE_URL=$VITE_SITE_URL
RUN npm run build

# --- Backend ---
FROM python:3.11-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential libjpeg-dev zlib1g-dev libpq-dev && \
    rm -rf /var/lib/apt/lists/*

COPY Tourism/requirements.txt /app/Tourism/
RUN pip install --no-cache-dir -r /app/Tourism/requirements.txt

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

WORKDIR /app/Tourism
# Fail the image build on a real collectstatic error instead of hiding it.
RUN python manage.py collectstatic --noinput

EXPOSE 8000
# ASGI (daphne) so the live-chat WebSocket at /ws/chat/<id>/ works; HTTP is
# the same Django app. CHANNEL_LAYERS is in-memory, so run ONE process per
# container (scale with more containers + a Redis channel layer).
ENTRYPOINT ["ny-entrypoint"]
CMD ["daphne", "-b", "0.0.0.0", "-p", "8000", "Tourism.asgi:application"]
