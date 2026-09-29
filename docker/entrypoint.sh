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

    # Try to load from a JSON fixture if one exists
    if [ -f "/app/Tourism/load.json" ]; then
      echo "entrypoint: loading data from load.json"
      python manage.py loaddata /app/Tourism/load.json --noinput
    elif [ -f "/app/downloads/nepal-tourism-seed.sqlite3.gz" ]; then
      echo "entrypoint: no load.json found, using SQLite seed database as fallback"
      python manage.py install_public_seed_db --skip-checksum
    else
      echo "entrypoint: WARNING - no seed data found. Database will be empty."
      echo "entrypoint: Run 'python manage.py export_render_data' locally and upload load.json"
    fi
  else
    echo "entrypoint: PostgreSQL database already has $DATA_EXISTS destinations - skipping data import"
  fi
fi

exec "$@"
