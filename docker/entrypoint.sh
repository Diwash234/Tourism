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
      echo "entrypoint: installing the published SQLite seed database"
      python manage.py install_public_seed_db
    else
      echo "entrypoint: no SQLite seed bundled; running migrations only"
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

  # Post-seed enrichment is best-effort: one missing data file must never
  # abort the boot (set -e would kill daphne and fail the whole deploy).
  echo "entrypoint: repairing external cover-image paths"
  python manage.py repair_cover_image_urls \
    || echo "entrypoint: WARNING - cover-image repair skipped"
  
  # Import OSM destinations (adds new destinations from OpenStreetMap)
  echo "entrypoint: importing OSM destinations"
  python manage.py import_osm_destinations || echo "entrypoint: WARNING - OSM destinations import skipped"
  
  # Import hotels, hospitals, police from CSV (idempotent: skips existing by name)
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
  
  # Post-seed enrichment is best-effort: one missing data file must never
  # abort the boot (set -e would kill daphne and fail the whole deploy).
  echo "entrypoint: repairing external cover-image paths"
  python manage.py repair_cover_image_urls \
    || echo "entrypoint: WARNING - cover-image repair skipped"
  
  # Import OSM destinations (adds new destinations from OpenStreetMap)
  echo "entrypoint: importing OSM destinations"
  python manage.py import_osm_destinations || echo "entrypoint: WARNING - OSM destinations import skipped"
  
  # Import hotels, hospitals, police from CSV (idempotent: skips existing by name)
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
  
  # Post-seed enrichment is best-effort: one missing data file must never
  # abort the boot (set -e would kill daphne and fail the whole deploy).
  echo "entrypoint: repairing external cover-image paths"
  python manage.py repair_cover_image_urls \
    || echo "entrypoint: WARNING - cover-image repair skipped"
  
  # Import OSM destinations (adds new destinations from OpenStreetMap)
  echo "entrypoint: importing OSM destinations"
  python manage.py import_osm_destinations || echo "entrypoint: WARNING - OSM destinations import skipped"
  
  # Import hotels, hospitals, police from CSV (idempotent: skips existing by name)
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
  
  # Post-seed enrichment is best-effort: one missing data file must never
  # abort the boot (set -e would kill daphne and fail the whole deploy).
  echo "entrypoint: repairing external cover-image paths"
  python manage.py repair_cover_image_urls \
    || echo "entrypoint: WARNING - cover-image repair skipped"