#!/bin/sh
# Container start-up: prepare the database, then run the given command.
#  * SQLite (default in docker-compose: /app/data/db.sqlite3 on the db_data
#    volume): on first start the published, privacy-safe seed database is
#    installed (checksum-verified, no user accounts). An existing database is
#    never overwritten.
#  * PostgreSQL (DATABASE_URL=postgres://...): schema migrations only.
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
fi

python manage.py migrate --noinput
exec "$@"
