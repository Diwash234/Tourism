#!/usr/bin/env bash
# One-command staging deployment gate. Every step must pass or the deploy
# stops; nothing here fabricates success. Designed to run on the staging
# host from the repository root (or locally for a full dry-run).
#
#   ./scripts/staging_deploy.sh [--skip-tests]
#
# Requirements on the host: python venv at $VENV (default /app/.venv),
# Node 20+ for the frontend build, environment variables per
# docs/PRODUCTION_OPERATIONS.md.
set -euo pipefail

VENV="${VENV:-/app/.venv}"
BACKEND_DIR="${BACKEND_DIR:-Tourism}"
FRONTEND_DIR="${FRONTEND_DIR:-frontend/Tourism}"
HEALTH_URL="${HEALTH_URL:-http://127.0.0.1:8000/api/v1/system/health/}"
SKIP_TESTS="${1:-}"

step() { echo; echo "==> $1"; }

step "1/8 Environment"
test -x "$VENV/bin/python" || { echo "FATAL: venv not found at $VENV"; exit 1; }
"$VENV/bin/python" --version

step "2/8 Migrations"
(cd "$BACKEND_DIR" && "$VENV/bin/python" manage.py migrate --noinput)

step "3/8 Static files"
(cd "$BACKEND_DIR" && "$VENV/bin/python" manage.py collectstatic --noinput)

step "4/8 Django checks + pending-migration guard"
(cd "$BACKEND_DIR" && "$VENV/bin/python" manage.py check)
(cd "$BACKEND_DIR" && "$VENV/bin/python" manage.py makemigrations --check --dry-run) \
  || { echo "FATAL: uncommitted model changes — run makemigrations and commit first"; exit 1; }

step "5/8 Production configuration validation (fails loudly, never prints secrets)"
(cd "$BACKEND_DIR" && "$VENV/bin/python" manage.py validate_production_config)

step "6/8 Frontend build"
(cd "$FRONTEND_DIR" && npm ci && npx eslint src/ --max-warnings=9999 && npm run build)

if [ "$SKIP_TESTS" != "--skip-tests" ]; then
  step "7/8 Backend test suite + E2E smoke"
  (cd "$BACKEND_DIR" && "$VENV/bin/python" manage.py test tourist)
  (cd "$FRONTEND_DIR" && npm run test:e2e)
else
  echo "==> 7/8 SKIPPED (--skip-tests)"
fi

step "8/8 Health poll (60 s)"
for i in $(seq 1 12); do
  code=$(curl -s -o /dev/null -w "%{http_code}" "$HEALTH_URL" || true)
  if [ "$code" = "200" ]; then echo "health OK after ${i}x5s"; exit 0; fi
  sleep 5
done
echo "FATAL: health endpoint did not return 200 within 60 s"
exit 1
