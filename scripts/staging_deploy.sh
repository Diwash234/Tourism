#!/usr/bin/env bash
# =====================================================================
# Staging deployment pipeline (§19) — build → migrate → collect → check
# → tests → health. Every step fails the deploy loudly on error.
#
# Usage:  VENV=/srv/tourism/.venv ./scripts/staging_deploy.sh [--skip-tests]
# Run from the repository root on the staging host after pulling the
# release commit and refreshing the .env for that environment.
# =====================================================================
set -euo pipefail

VENV="${VENV:-.venv}"
PY="$VENV/bin/python"
SKIP_TESTS="${1:-}"
BACKEND_DIR="Tourism"
FRONTEND_DIR="frontend/Tourism"
HEALTH_URL="${HEALTH_URL:-http://127.0.0.1:8000/api/v1/system/health/}"

step() { echo; echo "==> $*"; }

step "1/8 Backend environment check"
[ -x "$PY" ] || { echo "FATAL: python not found at $PY (set VENV=...)"; exit 1; }
"$PY" --version

step "2/8 Database migrations"
( cd "$BACKEND_DIR" && "$PY" manage.py migrate --noinput )

step "3/8 Static files"
( cd "$BACKEND_DIR" && "$PY" manage.py collectstatic --noinput )

step "4/8 Django system + migration-drift checks"
( cd "$BACKEND_DIR" && "$PY" manage.py check )
( cd "$BACKEND_DIR" && "$PY" manage.py makemigrations --check --dry-run )

step "5/8 Production configuration validation"
# Fails (exit 1) if production-critical configuration is missing.
( cd "$BACKEND_DIR" && "$PY" manage.py validate_production_config )

step "6/8 Frontend build"
( cd "$FRONTEND_DIR" && npm ci --no-audit --no-fund && npm run build )

if [ "$SKIP_TESTS" != "--skip-tests" ]; then
  step "7/8 Backend test suite"
  ( cd "$BACKEND_DIR" && "$PY" manage.py test tourist chatbot booking admin_panel audit system_health --verbosity 1 )

  step "7b/8 E2E smoke suite (requires a running backend on :8000 and ML on :8001)"
  ( cd "$FRONTEND_DIR" && npm run test:e2e )
else
  echo "==> 7/8 tests SKIPPED (--skip-tests)"
fi

step "8/8 Health endpoint verification"
for i in $(seq 1 12); do
  if curl -sf "$HEALTH_URL" | grep -q '"ok": *true'; then
    echo "HEALTH OK: $HEALTH_URL"
    exit 0
  fi
  echo "  waiting for service ($i/12)..."
  sleep 5
done
echo "FATAL: health endpoint did not report ok within 60s"
exit 1
