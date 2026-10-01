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

  if [ "$DATA_EXISTS" = "0" ]; then
    echo "entrypoint: PostgreSQL destination catalogue is empty - loading seed data"
    if [ -f "/app/Tourism/load.json" ]; then
      python manage.py loaddata /app/Tourism/load.json
    elif [ -f "/app/Tourism/dataset/data.json" ]; then
      python manage.py convert_dataset_to_fixture --output /tmp/tourism-load.json
      python manage.py loaddata /tmp/tourism-load.json
      rm -f /tmp/tourism-load.json
    elif [ -f "/app/downloads/nepal-tourism-seed.sqlite3.gz" ]; then
      python manage.py import_public_seed_postgres
    else
      echo "entrypoint: WARNING - no tourism seed data found"
    fi
  else
    echo "entrypoint: PostgreSQL already contains $DATA_EXISTS destinations - preserving catalogue"
  fi

  # Always attempt missing legacy users. This is independent of the
  # destination seed condition so a partially seeded production DB can still
  # receive the historical accounts without replacing anything.
  if [ -f "/app/downloads/nepal-tourism-database.sqlite3.gz" ]; then
    echo "entrypoint: checking for missing legacy user accounts"
    python manage.py import_legacy_users
  fi
  echo "entrypoint: importing sourced emergency and nearby-service records"
  python manage.py import_emergency_services
  python manage.py seed_district_services
  echo "entrypoint: repairing explicitly curated destination media"
  python manage.py repair_curated_media

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
print(
    f"entrypoint: PostgreSQL verification: "
    f"destinations={destinations}, images={images}, usable_images={usable_images}, users={users}"
)
if destinations == 0:
    raise SystemExit("Database verification failed: tourist_destination is empty")
PY
fi

exec "$@"
