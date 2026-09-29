#!/bin/sh
# Container start-up: prepare the database, then run the given command.
#  * SQLite (default in docker-compose: /app/data/db.sqlite3 on the db_data
#    volume): on first start the published, privacy-safe seed database is
#    installed (checksum-verified, no user accounts). An existing database is
#    never overwritten.
#  * PostgreSQL (DATABASE_URL=postgres://...): schema migrations + data import.
# Both then run `migrate` so an upgraded image brings the schema up to date.
set -e
cd /app/Tourism

# Ensure media directory exists and is writable
mkdir -p /app/Tourism/media /var/lib/tourism/media /var/lib/tourism/data 2>/dev/null || true

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
    echo "entrypoint: no database at $DB_FILE - installing the published seed database"
    python manage.py install_public_seed_db
  else
    echo "entrypoint: existing SQLite database found - applying any pending migrations"
    python manage.py migrate --noinput
  fi
else
  # PostgreSQL: run migrations, then import data if the database is empty
  echo "entrypoint: PostgreSQL detected - running migrations"
  python manage.py migrate --noinput

  # Check if data already exists (destinations table)
  DATA_EXISTS=$(python - <<'PY'
import os
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "Tourism.settings")
import django
django.setup()
from django.db import connection
try:
    with connection.cursor() as cur:
        cur.execute("SELECT COUNT(*) FROM tourist_destination")
        count = cur.fetchone()[0]
        print(count)
except Exception:
    print(0)
PY
  )

  if [ "$DATA_EXISTS" = "0" ]; then
    echo "entrypoint: PostgreSQL database is empty - loading seed data"

    # Search for an exported fixture (data.json or load.json in standard locations)
    FIXTURE=""
    for candidate in /app/Tourism/data.json /app/Tourism/load.json /app/data.json /app/load.json data.json load.json; do
      if [ -f "$candidate" ]; then
        FIXTURE="$candidate"
        break
      fi
    done

    if [ -n "$FIXTURE" ]; then
      echo "entrypoint: loading data from $FIXTURE via import_render_data"
      python manage.py import_render_data "$FIXTURE" --noinput
    elif [ -f "/app/downloads/nepal-tourism-seed.sqlite3.gz" ]; then
      echo "entrypoint: no JSON fixture found, importing published seed database into PostgreSQL"
      python manage.py install_public_seed_db --skip-checksum
    else
      echo "entrypoint: WARNING - no seed data found. Database will be empty."
      echo "entrypoint: Run 'python manage.py export_render_data' locally and deploy data.json or load.json"
    fi
  else
    echo "entrypoint: PostgreSQL database already has $DATA_EXISTS destinations - ensuring sequences are synchronized"
    python manage.py import_render_data --noinput --sync-sequences-only 2>/dev/null || true
  fi
fi

exec "$@"
