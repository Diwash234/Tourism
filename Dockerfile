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
RUN pip install --no-cache-dir -r /app/Tourism/requirements.txt gunicorn pillow

COPY Tourism/ /app/Tourism/
COPY --from=frontend /app/frontend/dist /app/Tourism/staticfiles/

WORKDIR /app/Tourism
# Fail the image build on a real collectstatic error instead of hiding it.
RUN python manage.py collectstatic --noinput

EXPOSE 8000
CMD ["gunicorn", "Tourism.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "3"]
