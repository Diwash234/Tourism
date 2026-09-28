#!/bin/sh
set -eu
cd /app/Tourism
python manage.py migrate --noinput
exec gunicorn Tourism.wsgi:application --bind "0.0.0.0:${PORT:-8000}" --workers "${WEB_CONCURRENCY:-2}" --timeout 120
