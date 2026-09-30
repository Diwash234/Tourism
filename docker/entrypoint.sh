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
mkdir -p /app/Tourism/media /app/Tourism/staticfiles /var/lib/tourism/media /var/lib/tourism/data 2>/dev/null || true

# Determine whether PostgreSQL or SQLite is the active database engine
IS_POSTGRES=0
if [ -n "$DATABASE_URL" ] && echo "$DATABASE_URL" | grep -qE '^postgres(ql)?://'; then
  IS_POSTGRES=1
elif [ "$DB_ENGINE" = "postgres" ] || [ "$DB_ENGINE" = "postgresql" ]; then
  IS_POSTGRES=1
fi

if [ "$IS_POSTGRES" = "1" ]; then
  # PostgreSQL: wait for connection, run migrations, then import data if database is empty
  echo "entrypoint: PostgreSQL detected - waiting for database connection to be ready..."
  MAX_RETRIES=30
  COUNT=0
  until python - <<'PY' 2>/dev/null
import os, sys
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "Tourism.settings")
import django
django.setup()
from django.db import connection
try:
    connection.ensure_connection()
    sys.exit(0)
except Exception:
    sys.exit(1)
PY
  do
    COUNT=$((COUNT + 1))
    if [ $COUNT -ge $MAX_RETRIES ]; then
      echo "entrypoint: timed out waiting for PostgreSQL after ${MAX_RETRIES} attempts"
      exit 1
    fi
    echo "entrypoint: waiting for PostgreSQL to accept connections (${COUNT}/${MAX_RETRIES})..."
    sleep 2
  done
  echo "entrypoint: PostgreSQL connection established successfully!"

  echo "entrypoint: running database migrations"
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
else
  # SQLite: locate target database file
  DB_FILE=$(python - <<'PY'
import os
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "Tourism.settings")
import django
django.setup()
from django.db import connection
print(connection.settings_dict["NAME"] if connection.vendor == "sqlite" else "")
PY
  )

  if [ -z "$DB_FILE" ]; then
    DB_FILE="/var/lib/tourism/data/db.sqlite3"
  fi

  mkdir -p "$(dirname "$DB_FILE")"
  if [ ! -s "$DB_FILE" ]; then
    echo "entrypoint: no database at $DB_FILE - installing the published seed database"
    python manage.py install_public_seed_db
  else
    echo "entrypoint: existing SQLite database found - applying any pending migrations"
    python manage.py migrate --noinput
  fi
fi

# Ensure signature curated travel plans, packages, and authentic images are populated
echo "entrypoint: seeding curated travel plans, packages, and authentic landmark images"
python manage.py seed_curated_travel_plans || true

exec "$@"
