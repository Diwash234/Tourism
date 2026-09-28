# Render production image: React build + Django API in one service.
FROM node:20-alpine AS frontend
WORKDIR /app/frontend
COPY frontend/Tourism/package*.json ./
RUN npm ci
COPY frontend/Tourism/ ./
ARG VITE_SITE_URL=""
ENV VITE_SITE_URL=$VITE_SITE_URL
RUN npm run build

FROM python:3.11-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends build-essential libjpeg-dev zlib1g-dev libpq-dev && rm -rf /var/lib/apt/lists/*
COPY Tourism/requirements.txt /app/Tourism/
RUN pip install --no-cache-dir -r /app/Tourism/requirements.txt
COPY Tourism/ /app/Tourism/
COPY --from=frontend /app/frontend/dist /app/Tourism/frontend_dist/
WORKDIR /app/Tourism
RUN mkdir -p /var/lib/tourism/media /var/lib/tourism/data && python manage.py collectstatic --noinput
EXPOSE 8000
CMD ["sh", "-c", "python manage.py migrate --noinput && exec gunicorn Tourism.wsgi:application --bind 0.0.0.0:$PORT --workers $WEB_CONCURRENCY --timeout 120"]
