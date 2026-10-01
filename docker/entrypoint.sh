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
      python manage.py loaddata /app/Tourism/load.json
    elif [ -f "/app/Tourism/dataset/data.json" ]; then
      echo "entrypoint: converting dataset/data.json to fixture format"
      python manage.py convert_dataset_to_fixture --output /tmp/tourism-load.json
      echo "entrypoint: loading data from generated transient fixture"
      python manage.py loaddata /tmp/tourism-load.json
      rm -f /tmp/tourism-load.json
      # A successful loaddata command is not enough: verify that the public
      # catalogue and media rows really reached PostgreSQL before the server
      # starts. This prevents a green-looking deployment with an empty API.
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
    cur.execute("SELECT COUNT(*) FROM tourist_destinationimage WHERE external_url <> '' OR image_path <> '' OR image IS NOT NULL")
    usable_images = cur.fetchone()[0]
print(f"entrypoint: PostgreSQL seed verification: destinations={destinations}, images={images}, usable_images={usable_images}")
if destinations == 0:
    raise SystemExit("Seed verification failed: tourist_destination is still empty")
if images == 0:
    print("entrypoint: WARNING - no destination media rows were imported")

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
