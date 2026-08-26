#!/usr/bin/env bash
# =============================================================================
# Nepal Tourism Platform — unified dev runner
# Starts the Django API and the React Vite dev server together.
#
# Usage:
#   chmod +x run.sh
#   ./run.sh              # create venv, install deps, migrate, start both servers
#   ./run.sh --no-install # skip dependency installation
# =============================================================================
set -euo pipefail
cd "$(dirname "$0")"

INSTALL=1
if [ "${1:-}" = "--no-install" ]; then INSTALL=0; fi

echo "=================================================================="
echo "  Nepal Tourism Platform"
echo "=================================================================="

# 1. Python virtual environment
VENV_DIR=".venv"
if [ ! -d "$VENV_DIR" ]; then
  echo ""
  echo ">> Creating Python virtual environment in $VENV_DIR ..."
  python3 -m venv "$VENV_DIR"
  INSTALL=1
fi
# shellcheck disable=SC1091
source "$VENV_DIR/bin/activate"

PY_PKGS="django djangorestframework django-cors-headers django-filter Pillow requests whitenoise drf-spectacular python-decouple djangorestframework-simplejwt django-phonenumber-field[phonenumbers] gunicorn python-dotenv pandas numpy scikit-learn joblib networkx fastapi uvicorn python-multipart"

if [ "$INSTALL" = "1" ]; then
  echo ""
  echo ">> Installing Python dependencies in venv..."
  pip install --quiet --upgrade pip
  pip install --quiet $PY_PKGS
fi

# 2. Database
echo ""
echo ">> Running database migrations..."
(cd Tourism && python manage.py migrate --noinput)

# 3. Frontend dependencies
if [ "$INSTALL" = "1" ] && [ ! -d frontend/Tourism/node_modules ]; then
  echo ""
  echo ">> Installing frontend dependencies..."
  (cd frontend/Tourism && npm install --silent)
fi

# 4. Start both servers and clean up on exit
echo ""
echo ">> Starting Django API on http://localhost:8000"
echo ">> Starting React app   on http://localhost:5173"
echo ""

cleanup() {
  echo ""
  echo ">> Shutting down..."
  kill "$DJANGO_PID" 2>/dev/null || true
  kill "$VITE_PID" 2>/dev/null || true
  wait 2>/dev/null || true
}
trap cleanup EXIT INT TERM

(cd Tourism && python manage.py runserver 0.0.0.0:8000) &
DJANGO_PID=$!

(cd frontend/Tourism && npm run dev -- --host 0.0.0.0) &
VITE_PID=$!

wait
