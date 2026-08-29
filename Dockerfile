# --- Build frontend ---
FROM node:20-alpine AS frontend
WORKDIR /app/frontend
COPY frontend/Tourism/package*.json ./
RUN npm ci
COPY frontend/Tourism/ ./
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
RUN python manage.py collectstatic --noinput 2>/dev/null || true

EXPOSE 8000
CMD ["gunicorn", "Tourism.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "3"]
