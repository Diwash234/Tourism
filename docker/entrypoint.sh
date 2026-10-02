#!/bin/sh
# Production database bootstrap for Render/PostgreSQL and local SQLite.
#
# SERVE FIRST, LOAD DATA AFTER. Render scans for a listening port the
# moment the container starts and kills the deploy when nothing binds
# ("No open ports detected ... Timed Out"). The catalogue imports and
# enrichment below take minutes on a cold database, so the boot order is
# strictly:
#
#   1. migrate (and install the bundled SQLite seed when the file is empty)
#   2. start Daphne on $PORT and wait until the port answers
#   3. run the idempotent data phase (best-effort, guarded, one copy only)
#   4. start the optional ML sidecar
#   5. wait for Daphne -- the container lives exactly as long as the server
#
# Every data step is guarded with `|| echo WARNING`: under `set -e` one
# missing CSV must never abort the boot (that used to kill Daphne before
# it bound the port and failed the whole deploy).
set -e
cd /app/Tourism

# Render injects $PORT; the image default (EXPOSE/CMD/HEALTHCHECK) is 8000.
APP_PORT="${PORT:-8000}"

# ------------------------------------------------------------------ helpers

# Only import a catalogue when its table is empty: existing Render
# databases must not rebuild large catalogues on every boot.
run_if_table_empty() {
  table="$1"; label="$2"; shift 2
  count=$(python - <<PY
import os
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "Tourism.settings")
import django
django.setup()
from django.db import connection
with connection.cursor() as cur:
    cur.execute("SELECT COUNT(*) FROM ${table}")
    print(cur.fetchone()[0])
PY
)
  if [ "$count" = "0" ]; then
    echo "entrypoint: $label table is empty - importing"
    "$@" || echo "entrypoint: WARNING - $label import skipped"
  else
    echo "entrypoint: $label already has $count rows - preserving"
  fi
}

# Gapped reference/service catalogues: imported once per table, then only
# refreshed manually. Cheap row-count probes on every boot.
load_catalogue_if_empty() {
  run_if_table_empty tourist_osmtourismplace "OSM tourism places" python manage.py import_osm_destinations
  run_if_table_empty tourist_hotel "hotels" python manage.py import_hotels_csv
  run_if_table_empty tourist_hospital "hospitals" python manage.py import_hospital --csv dataset/hospital_cleaned.csv
  run_if_table_empty tourist_policestation "police" python manage.py import_police --csv dataset/nearbypolice.csv
  run_if_table_empty tourist_riskincident "risk" python manage.py import_risk
}

# Idempotent gap-filling shared by both database backends. Each command
# only writes empty values (or re-derives projections of tracked files), so
# re-running on an existing catalogue is safe.
run_data_repairs() {
  # Repair external cover-image paths (media URLs rendered as local paths).
  echo "entrypoint: repairing external cover-image paths"
  python manage.py repair_cover_image_urls \
    || echo "entrypoint: WARNING - cover-image repair skipped"

  # Reconcile the destination budget projection from the tracked CSV
  # (cheap since the 5,018 unindexed name lookups were removed; leaving it
  # stale is what made the public estimator report a null total).
  echo "entrypoint: importing verified destination budget dataset"
  python manage.py import_budget \
    || echo "entrypoint: WARNING - budget dataset import skipped"

  echo "entrypoint: importing sourced emergency and nearby-service records"
  python manage.py import_emergency_services \
    || echo "entrypoint: WARNING - emergency services import skipped"
  python manage.py seed_district_services \
    || echo "entrypoint: WARNING - district services seed skipped"

  echo "entrypoint: auditing service coverage"
  python manage.py audit_service_coverage --radius 50 \
    || echo "entrypoint: WARNING - service coverage audit skipped"

  echo "entrypoint: repairing explicitly curated destination media"
  python manage.py repair_curated_media \
    || echo "entrypoint: WARNING - curated media repair skipped"

  # Fill empty destination columns from coordinates/CSVs (distances,
  # nearest city/airport, city names, addresses, elevations, entry fee).
  echo "entrypoint: filling missing destination data (distances, nearest city/airport, city names)"
  python manage.py enrich_destinations \
    || echo "entrypoint: WARNING - destination enrichment skipped"

  # Recompute nearest hospital/police/hotel proximity from the service
  # tables. Previously guarded by a `SEEDED` flag that was never set, so it
  # silently never ran and every destination's nearest-service fields stayed
  # empty in production; run it unconditionally now.
  echo "entrypoint: computing nearest hospital/police/hotel for destinations"
  python manage.py enrich_destination_nearby_services \
    || echo "entrypoint: WARNING - nearby-service enrichment skipped"

  # Hide OSM-CSV junk destinations (coverless, mojibake, type=node/way/
  # relation) from every public surface and re-pin the curated featured set
  # the homepage falls back to when the CMS FeaturedDestination table is
  # empty. Idempotent; never reactivates or unfeatures anything.
  echo "entrypoint: reconciling public catalogue (OSM junk rows + featured set)"
  python manage.py reconcile_catalogue \
    || echo "entrypoint: WARNING - catalogue reconcile skipped"
}

# ------------------------------------------------- 1. schema / seed file
# (the only phase that must finish before serving: Daphne would serve 500s
# from an un-migrated schema, and a SQLite seed install replaces the file)

DB_FILE=$(python - <<'PY'
import os
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "Tourism.settings")
import django
django.setup()
from django.db import connection
print(connection.settings_dict["NAME"] if connection.vendor == "sqlite" else "")
PY
)

if [ -n "$DB_FILE" ]; then
  mkdir -p "$(dirname "$DB_FILE")"
  if [ ! -s "$DB_FILE" ]; then
    echo "entrypoint: SQLite database is empty"
    if [ -f "/app/downloads/nepal-tourism-seed.sqlite3.gz" ]; then
      echo "entrypoint: installing the published SQLite seed database"
      python manage.py install_public_seed_db
    else
      echo "entrypoint: no SQLite seed bundled; running migrations only"
      python manage.py migrate --noinput
    fi
  else
    python manage.py migrate --noinput
  fi
else
  echo "entrypoint: PostgreSQL detected - running migrations"
  python manage.py migrate --noinput
fi

# ---------------------------------------------------------- 2. serve first
# Re-pin the image CMD to the runtime port so the port Render scans for and
# the socket Daphne binds can never disagree (image default: 8000).
if [ "$#" -eq 0 ] || [ "$1" = "daphne" ]; then
  set -- daphne -b 0.0.0.0 -p "$APP_PORT" Tourism.asgi:application
fi
echo "entrypoint: starting application server on 0.0.0.0:$APP_PORT"
"$@" &
SERVER_PID=$!
trap 'kill "$SERVER_PID" 2>/dev/null || true' EXIT INT TERM

bound=0
waited=0
while [ "$waited" -lt 60 ]; do
  if ! kill -0 "$SERVER_PID" 2>/dev/null; then
    echo "entrypoint: ERROR - server process exited before binding a port" >&2
    wait "$SERVER_PID" 2>/dev/null || true
    exit 1
  fi
  if python -c "import socket; socket.create_connection(('127.0.0.1', $APP_PORT), 1).close()" 2>/dev/null; then
    bound=1
    break
  fi
  waited=$((waited + 1))
  sleep 1
done
if [ "$bound" != "1" ]; then
  echo "entrypoint: ERROR - server did not bind port $APP_PORT within 60s" >&2
  exit 1
fi
echo "entrypoint: server is accepting connections - loading catalogue data"

# ------------------------------------------------------------ 3. data phase
# Runs while the app is already healthy; Render's port scan is satisfied and
# every step below is best-effort, so a slow or failing importer can no
# longer fail the deploy by delaying the port.

if [ -n "$DB_FILE" ]; then
  # SQLite (local compose / fresh clone): the bundled seed installed above
  # already carries destinations, images and services; fill the gaps.
  load_catalogue_if_empty
  run_data_repairs
else
  # PostgreSQL (Render).
  DATA_EXISTS=$(python - <<'PY'
import os
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "Tourism.settings")
import django
django.setup()
from django.db import connection
with connection.cursor() as cur:
    cur.execute("SELECT COUNT(*) FROM tourist_destination")
    print(cur.fetchone()[0])
PY
  )

  # Existing PostgreSQL catalogues must not be bulk-reimported on every web
  # restart. The old path ran every OSM/CSV import plus enrichment on each
  # deploy, competing with Daphne and causing 502/OOM on the 512 MiB plan.
  load_catalogue_if_empty

  # The legacy-user importer is idempotent: it creates only missing emails and
  # preserves existing passwords. Run this lightweight account sync on every
  # boot so a Render database that already has destinations but is missing one
  # of the 22 legacy traveller accounts is repaired too.
  if [ -f "/app/downloads/nepal-tourism-database.sqlite3.gz" ]; then
    echo "entrypoint: reconciling legacy user accounts (missing only)"
    python manage.py import_legacy_users       || echo "entrypoint: WARNING - legacy user import skipped"
  fi

  # Heavy enrichment and media repair are deliberately opt-in on the small
  # Render web instance. They can be run as a one-off task on a larger worker
  # without competing with the public server.
  if [ "${RUN_DATA_REPAIRS_ON_BOOT:-0}" = "1" ]; then
    run_data_repairs
  else
    echo "entrypoint: heavy data repairs disabled on normal web boot"
    run_if_table_empty tourist_budgetestimation "budget" python manage.py import_budget
    echo "entrypoint: repairing public visibility for approved seed media"
    python manage.py repair_public_media_visibility \
      || echo "entrypoint: WARNING - public media visibility repair skipped"
    python manage.py repair_destination_names \
      || echo "entrypoint: WARNING - destination name repair skipped"
  fi

  # Data audit: intentionally fails the deploy instead of looking healthy
  # while a public catalogue table stayed empty.
  python - <<'PY'
import os
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "Tourism.settings")
import django
django.setup()
from django.db import connection
with connection.cursor() as cur:
    cur.execute("SELECT COUNT(*) FROM tourist_destination")
    destinations = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM tourist_destinationimage")
    images = cur.fetchone()[0]
    cur.execute("""SELECT COUNT(*) FROM tourist_destinationimage
                   WHERE COALESCE(external_url, '') <> ''
                      OR COALESCE(image_path, '') <> ''
                      OR image IS NOT NULL""")
    usable_images = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM tourist_user")
    users = cur.fetchone()[0]
    tables = {
        "hotels": "tourist_hotel",
        "hospitals": "tourist_hospital",
        "police": "tourist_policestation",
        "emergency_contacts": "tourist_emergencycontact",
        "osm_services": "tourist_osmessentialservice",
        "budget_rows": "tourist_budgetestimation",
        "risk_incidents": "tourist_riskincident",
    }
    counts = {}
    for label, table in tables.items():
        try:
            cur.execute(f"SELECT COUNT(*) FROM {table}")
            counts[label] = cur.fetchone()[0]
        except Exception:
            counts[label] = "table-unavailable"
print(
    f"entrypoint: PostgreSQL verification: "
    f"destinations={destinations}, images={images}, usable_images={usable_images}, users={users}, "
    f"hotels={counts['hotels']}, hospitals={counts['hospitals']}, police={counts['police']}, "
    f"emergency_contacts={counts['emergency_contacts']}, osm_services={counts['osm_services']}, "
    f"budget_rows={counts['budget_rows']}, risk_incidents={counts['risk_incidents']}"
)
if destinations == 0:
    raise SystemExit("Database verification failed: tourist_destination is empty")
PY
fi

# ------------------------------------------------------- 4. ML sidecar
# Budget estimates, itinerary planning and safety scoring: Django talks to
# it at ML_SERVICE_URL (127.0.0.1:8001). Started AFTER migrations and the
# data phase so its pandas/sklearn import spike (~300MB) never overlaps
# other Python processes on Render's 512 MiB free instance. render.yaml
# sets START_ML_SERVICE=1; Django's deterministic CSV/database fallbacks
# cover the service whenever it is off or still importing.
START_ML_SERVICE="${START_ML_SERVICE:-0}"
if [ "$START_ML_SERVICE" = "1" ] && [ -f /app/ml_service/app.py ]; then
  echo "entrypoint: starting ML service on 127.0.0.1:8001"
  nohup sh -c 'cd /app/ml_service && exec python -m uvicorn app:app --host 127.0.0.1 --port 8001 --workers 1' >> /tmp/ml-service.log 2>&1 &
else
  echo "entrypoint: ML sidecar disabled (START_ML_SERVICE=$START_ML_SERVICE); Django CSV/database fallbacks remain active"
fi

# ---------------------------------------------------------- 5. supervise
# The container lives exactly as long as the application server.
wait "$SERVER_PID"
