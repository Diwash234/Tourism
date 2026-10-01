#!/bin/sh
# Production database bootstrap for Render/PostgreSQL and local SQLite.
set -e
cd /app/Tourism

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
      python manage.py install_public_seed_db
    else
      python manage.py migrate --noinput
    fi
  else
    python manage.py migrate --noinput
  fi
  # Fill any destination columns the seed left empty (distances, nearest
  # city/airport, city names, addresses, cited elevations, honest entry fee).
  # Idempotent: only empty values are ever written.
  echo "entrypoint: filling missing destination data"
  python manage.py enrich_destinations \
    || echo "entrypoint: WARNING - destination enrichment skipped"
else
  echo "entrypoint: PostgreSQL detected - running migrations"
  python manage.py migrate --noinput

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

  # ALWAYS load all seed sources - no SEEDED flag to prevent multiple loads
  if [ "$DATA_EXISTS" = "0" ]; then
    echo "entrypoint: PostgreSQL destination catalogue is empty - loading ALL seed data sources"

    # 1. Canonical verified snapshot (tracked in git): destinations WITH
    #    categories, hotels, hospitals, police stations, restaurants, OSM
    #    services and published CMS pages.
    if [ -f "/app/Tourism/dataset/verified_tourism_data.json" ]; then
      echo "entrypoint: loading verified snapshot (destinations + services + CMS)"
      python manage.py import_verified_snapshot /app/Tourism/dataset/verified_tourism_data.json || echo "entrypoint: WARNING - verified snapshot load failed"
    fi

    # 2. Local prebuilt fixture (not in git; present only on custom images).
    if [ -f "/app/Tourism/load.json" ]; then
      echo "entrypoint: loading prebuilt load.json fixture"
      python manage.py loaddata /app/Tourism/load.json || echo "entrypoint: WARNING - load.json load failed"
    fi

    # 3. Convert the tracked dataset catalogue (embeds the category table so
    #    destination FKs always resolve on a fresh migrated database).
    if [ -f "/app/Tourism/dataset/data.json" ]; then
      echo "entrypoint: converting dataset/data.json to a fixture"
      python manage.py convert_dataset_to_fixture --output /tmp/tourism-load.json \
        && python manage.py loaddata /tmp/tourism-load.json \
        || echo "entrypoint: WARNING - dataset conversion/load failed"
      rm -f /tmp/tourism-load.json
    fi

    # 4. Published seed SQLite archive.
    if [ -f "/app/downloads/nepal-tourism-seed.sqlite3.gz" ]; then
      echo "entrypoint: importing published seed archive"
      python manage.py import_public_seed_postgres || echo "entrypoint: WARNING - seed archive import failed"
    fi
  else
    echo "entrypoint: PostgreSQL already contains $DATA_EXISTS destinations - preserving catalogue"
  fi

  # ALWAYS import additional data sources (idempotent: only adds missing records)
  # These run regardless of whether data was seeded above
  echo "entrypoint: importing OSM destinations"
  python manage.py import_osm_destinations || echo "entrypoint: WARNING - OSM destinations import skipped"

  echo "entrypoint: importing hotels from hotel.csv"
  python manage.py import_hotels_csv || echo "entrypoint: WARNING - hotel CSV import skipped"
  
  echo "entrypoint: importing hospital directory"
  python manage.py import_hospital --csv dataset/hospital_cleaned.csv \
    || echo "entrypoint: WARNING - hospital CSV import skipped"
  
  echo "entrypoint: importing police directory"
  python manage.py import_police --csv dataset/nearbypolice.csv \
    || echo "entrypoint: WARNING - police CSV import skipped"
  
  echo "entrypoint: importing risk data"
  python manage.py import_risk \
    || echo "entrypoint: WARNING - risk CSV import skipped"

  # Reconcile the destination budget table on every deploy. The importer is
  # idempotent (update_or_create) and makes the tracked CSV usable on Render
  # instead of depending on the optional ML process being online.
  echo "entrypoint: importing verified destination budget dataset"
  python manage.py import_budget \
    || echo "entrypoint: WARNING - budget dataset import skipped"

  echo "entrypoint: importing sourced emergency and nearby-service records"
  python manage.py import_emergency_services \
    || echo "entrypoint: WARNING - emergency services import skipped"
  python manage.py seed_district_services \
    || echo "entrypoint: WARNING - district services seed skipped"

  # Import additional bundled datasets
  echo "entrypoint: importing bundled hotel, hospital, police and risk datasets"
  python manage.py import_hotels_csv --csv dataset/hotel.csv \
    || echo "entrypoint: WARNING - hotel CSV import skipped"
  python manage.py import_hospital --csv dataset/hospital.csv \
    || echo "entrypoint: WARNING - hospital CSV import skipped"
  python manage.py import_police --csv dataset/nearbypolice.csv \
    || echo "entrypoint: WARNING - police CSV import skipped"
  python manage.py import_risk \
    || echo "entrypoint: WARNING - risk CSV import skipped"
  
  # Import risk data
  echo "entrypoint: importing risk data"
  python manage.py import_risk \
    || echo "entrypoint: WARNING - risk CSV import skipped"
  
  # Post-seed enrichment is best-effort: one missing data file must never
  # abort the boot (set -e would kill daphne and fail the whole deploy).
  echo "entrypoint: repairing external cover-image paths"
  python manage.py repair_cover_image_urls \
    || echo "entrypoint: WARNING - cover-image repair skipped"
  
  # Import OSM destinations (adds new destinations from OpenStreetMap)
  echo "entrypoint: importing OSM destinations"
  python manage.py import_osm_destinations || echo "entrypoint: WARNING - OSM destinations import skipped"

  echo "entrypoint: backfilling missing destination media from verified seed"
  python manage.py sync_seed_media_postgres \
    || echo "entrypoint: WARNING - media backfill skipped"
  # Reconcile the destination budget table on every deploy. The importer is
  # idempotent (update_or_create) and makes the tracked CSV usable on Render
  # instead of depending on the optional ML process being online.
  echo "entrypoint: importing verified destination budget dataset"
  python manage.py import_budget \
    || echo "entrypoint: WARNING - budget dataset import skipped"

  echo "entrypoint: importing sourced emergency and nearby-service records"
  python manage.py import_emergency_services \
    || echo "entrypoint: WARNING - emergency services import skipped"
  python manage.py seed_district_services \
    || echo "entrypoint: WARNING - district services seed skipped"
  echo "entrypoint: importing bundled hotel, hospital, police and risk datasets"
  python manage.py import_hotels_csv --csv dataset/hotel.csv \
    || echo "entrypoint: WARNING - hotel CSV import skipped"
  python manage.py import_hospital --csv dataset/hospital.csv \
    || echo "entrypoint: WARNING - hospital CSV import skipped"
  python manage.py import_police --csv dataset/nearbypolice.csv \
    || echo "entrypoint: WARNING - police CSV import skipped"
  python manage.py import_risk \
    || echo "entrypoint: WARNING - risk CSV import skipped"
  echo "entrypoint: auditing service coverage"
  python manage.py audit_service_coverage --radius 50 \
    || echo "entrypoint: WARNING - service coverage audit skipped"

  echo "entrypoint: repairing explicitly curated destination media"
  python manage.py repair_curated_media \
    || echo "entrypoint: WARNING - curated media repair skipped"

  # Fill empty destination columns from coordinates/CSVs after every seed
  # path (snapshot, fixture, dataset, archive).  Idempotent - only empty
  # values are written - so re-running on an existing catalogue is safe.
  echo "entrypoint: filling missing destination data (distances, nearest city/airport, city names)"
  python manage.py enrich_destinations \
    || echo "entrypoint: WARNING - destination enrichment skipped"

  # Recompute nearest hospital/police/hotel proximity from the service tables
  # - only right after a fresh seed, so curated values on later boots are
  # never overwritten.
  if [ "$SEEDED" = "1" ]; then
    echo "entrypoint: computing nearest hospital/police/hotel for seeded destinations"
    python manage.py enrich_destination_nearby_services \
      || echo "entrypoint: WARNING - nearby-service enrichment skipped"
  fi

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
    # These counts are intentionally runtime diagnostics: they make a Render
    # deployment visibly fail its data audit instead of looking healthy while
    # one of the public catalogue tables stayed empty.
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

# ML microservice (budget estimates, itinerary planning, safety scoring) as a
# background uvicorn on 127.0.0.1:8001 -- Django talks to it at
# ML_SERVICE_URL. Deferred 20s so its pandas/sklearn import spike (~300MB)
# never overlaps the migration/seed python processes on Render's 512MB free
# instance (an OOM there fails the health check and blocks every deploy);
# Django's honest fallbacks cover the first seconds. Never aborts the boot.
if [ -f /app/ml_service/app.py ]; then
  echo "entrypoint: scheduling ML service on 127.0.0.1:8001 (starts in 20s)"
  nohup sh -c 'sleep 20; cd /app/ml_service && exec python -m uvicorn app:app --host 127.0.0.1 --port 8001' >> /tmp/ml-service.log 2>&1 &
else
  echo "entrypoint: WARNING - ml_service/app.py missing; budget/itinerary/safety will degrade"
fi

exec "$@"
