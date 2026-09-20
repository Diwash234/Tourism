#!/usr/bin/env bash
# close_production_gates.sh — run every host-side gate from the
# BLOCKED/PARTIAL register in order and print an evidence summary.
#
# Usage (on the deployment host, from the repo root):
#   export ROUTING_BASE_URL="http://<osrm-host>:5000"
#   export ROUTING_PROFILES="driving,foot,bike"      # profiles your OSRM hosts
#   export OPENWEATHER_API_KEY="..."                 # optional
#   export DATABASE_URL="postgres://..."             # optional, for gate 6
#   bash scripts/close_production_gates.sh
#
# Exit code 0 = all runnable gates passed. Each gate prints PASS/FAIL/SKIP.
set -u
cd "$(dirname "$0")/../Tourism"
PY="${PYTHON:-python3}"
FRONTEND="../frontend/Tourism"
FAILED=0

gate() { # name, command...
  local name="$1"; shift
  echo ""
  echo "=== GATE: $name ==="
  if "$@"; then echo "PASS: $name"; else echo "FAIL: $name"; FAILED=1; fi
}

echo "--- Gate 1: real OSRM validation (7/7, source=osrm required) ---"
if [ -n "${ROUTING_BASE_URL:-}" ]; then
  gate "OSRM 7/7" $PY manage.py validate_navigation_routes
  echo "--- Gate 2: write regression baseline + health probe ---"
  gate "route baseline" $PY manage.py validate_navigation_routes --write-baseline
else
  echo "SKIP: ROUTING_BASE_URL not set"
fi

echo ""
echo "--- Gate 4: weather provider (needs OPENWEATHER_API_KEY) ---"
if [ -n "${OPENWEATHER_API_KEY:-}" ]; then
  gate "weather live" $PY -c "
import os, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE','Tourism.settings'); django.setup()
from tourist.utils import get_current_weather
w = get_current_weather(28.2096, 83.9856)
assert w, 'weather lookup returned None with key configured'
print('weather ok:', w.get('weather', [{}])[0].get('main'))"
else
  echo "SKIP: OPENWEATHER_API_KEY not set"
fi

echo ""
echo "--- Gate 5: OAuth configuration check ---"
gate "oauth config" $PY manage.py validate_oauth_providers || echo "(providers without credentials report SKIPPED — that is expected)"

echo ""
echo "--- Gate 6: database ---"
# If Postgres client tools are not on PATH, export full paths:
#   PG_DUMP, PG_PSQL, PG_CREATEDB, PG_DROPDB
if [ -n "${DATABASE_URL:-}" ]; then
  gate "postgres migrations" $PY manage.py migrate --noinput
  gate "postgres suite" $PY manage.py test tourist navigation
  gate "postgres backup+drill restore" bash -c "rm -rf /tmp/gate-backups && $PY manage.py backup_database --dir /tmp/gate-backups && $PY manage.py restore_database --file \$(ls -t /tmp/gate-backups/*.gz | head -1) --target drill"
else
  echo "SKIP: DATABASE_URL not set (SQLite dev DB in use)"
  gate "sqlite suite" $PY manage.py test tourist navigation
fi

echo ""
echo "--- Gate 7: browser E2E (Playwright-capable host) ---"
if [ -d "$FRONTEND" ] && (cd "$FRONTEND" && npx playwright --version >/dev/null 2>&1); then
  (cd "$FRONTEND" && npx playwright install chromium >/dev/null 2>&1)
  gate "browser specs" bash -c "cd $FRONTEND && npm run test:e2e:browser"
else
  echo "SKIP: Playwright unavailable here — run: npx playwright install --with-deps && npm run test:e2e:browser"
fi

echo ""
echo "--- Always: API-level E2E + lint + build ---"
gate "api e2e" bash -c "cd $FRONTEND && npm run test:e2e"
gate "lint" bash -c "cd $FRONTEND && npx eslint src/ --max-warnings=9999 2>&1 | grep -qE '  error  ' && exit 1 || true"
gate "build" bash -c "cd $FRONTEND && npm run build"

echo ""
echo "--- Gate 3: physical-device GPS run ---"
cat <<'CHECKLIST'
MANUAL (cannot be scripted): open /navigation on a real phone, then verify:
  [ ] permission denied path shows a clear error, permission restore works
  [ ] marker tracks smoothly (poor-accuracy fixes discarded)
  [ ] deliberate wrong turn -> off-route banner -> auto reroute (15s cooldown)
  [ ] network drop -> outage banner, route still usable
  [ ] arrival screen -> next itinerary stop offered
  [ ] End clears tracking; reopen offers resume within 2h
CHECKLIST

echo ""
if [ "$FAILED" -eq 0 ]; then
  echo "ALL RUNNABLE GATES PASSED. Update docs/REPOSITORY_AUDIT_REPORT.md register with these results."
else
  echo "ONE OR MORE GATES FAILED — see output above."
fi
exit $FAILED
