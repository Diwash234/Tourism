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
COPY Tourism/ /app/Tourism/

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

# Run migrations and start Gunicorn
CMD ["sh", "-c", "python manage.py migrate --noinput && exec gunicorn Tourism.wsgi:application --bind 0.0.0.0:$PORT --workers ${WEB_CONCURRENCY:-2} --timeout 120"]
