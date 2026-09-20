# Deployment Guide — Digital Nepal Tourism Platform

A step-by-step path from this repository to a live website, plus the
pre-flight checklist. Written for a single Ubuntu/Debian VPS (2 GB+ RAM);
works the same on Render/Railway/Fly-style platforms (skip the nginx/systemd
sections and use the platform's process manager).

---

## 0. What you are deploying

| Piece | Where | Notes |
|---|---|---|
| Django + DRF API | `Tourism/` | Python 3.11+, `manage.py runserver` in dev only |
| React frontend | `frontend/Tourism/` | Vite build → static files served by nginx (or any CDN) |
| ML microservices (optional) | `ml_service/`, image service | The API degrades gracefully when they are off |
| Database | SQLite (default, WAL-hardened) or PostgreSQL | Switch with `DATABASE_URL`, zero code changes |

**SQLite is the default and is production-viable on a single node**
(WAL + foreign keys are applied automatically). Choose PostgreSQL when you
run more than one app instance or want managed backups.

---

## 1. Pre-flight checklist (before you touch a server)

Run these locally/on CI first — all must be green:

```bash
# backend: 454 tests (tourist + navigation)
cd Tourism && python manage.py test tourist navigation

# frontend: lint + build + 67-check API-level E2E (needs dev servers)
cd frontend/Tourism && npm ci && npm run lint && npm run build
npm run test:e2e:live        # backend + vite dev servers running

# data integrity: every public destination navigable, real Nepal coords
python manage.py audit_navigable_places
```

Then, on the server, run the one-command gate closer with your REAL env:

```bash
export SECRET_KEY="<50+ random chars>"
export DEBUG=False
export ALLOWED_HOSTS="yourdomain.com,www.yourdomain.com"
# optional but recommended:
export ROUTING_BASE_URL="https://your-osrm-host"     # real turn-by-turn roads
export OPENWEATHER_API_KEY="..."                     # live weather
export GOOGLE_CLIENT_ID="..." GOOGLE_CLIENT_SECRET="..."
export DATABASE_URL="postgres://user:pass@host:5432/tourism_db"  # if using PG
bash scripts/close_production_gates.sh
```

Every gate prints PASS/FAIL/SKIP. **Do not go live with FAILs.** Register of
what each gate means: `docs/REPOSITORY_AUDIT_REPORT.md`.

---

## 2. Server setup (VPS)

```bash
sudo apt update && sudo apt install -y python3.11 python3.11-venv nginx git
git clone <your-fork> /srv/tourism && cd /srv/tourism

# backend
python3.11 -m venv .venv && . .venv/bin/activate
pip install -r Tourism/requirements.txt

# configuration (never commit .env)
cp Tourism/.env.example Tourism/.env
nano Tourism/.env          # SECRET_KEY, DEBUG=False, ALLOWED_HOSTS, keys...
```

Key `.env` values:

| Variable | Production value |
|---|---|
| `SECRET_KEY` | ≥50 random chars (`python -c "import secrets;print(secrets.token_urlsafe(64))"`) |
| `DEBUG` | `False` (HTTPS redirects, secure cookies, HSTS then auto-enable) |
| `ALLOWED_HOSTS` | your domains, comma-separated |
| `DATABASE_URL` | omit for SQLite · `postgres://…` for PostgreSQL |
| `ROUTING_BASE_URL` | OSRM server for street-level turn-by-turn (optional) |
| `OPENWEATHER_API_KEY`, `GOOGLE_CLIENT_ID/SECRET` | optional features |

Validate loudly (must print `RESULT: PASS`):

```bash
python Tourism/manage.py validate_production_config
```

---

## 3. Database

```bash
cd Tourism
python manage.py migrate --noinput

# Option A — SQLite (default): nothing else to do. The tracked db.sqlite3
# already contains the seeded 6.6k destinations; keep it or start empty.

# Option B — PostgreSQL:
sudo -u postgres createuser tourism_user -P && createdb tourism_db -O tourism_user
# put DATABASE_URL in .env, then:
python manage.py migrate --noinput
# load the full dataset from the SQLite snapshot fixture if you want the
# seeded content, or re-run the pipeline:
python manage.py seed_taxonomy && python manage.py categorize_existing \
  && python manage.py normalize_district_names
```

Postgres client tools for backups: `sudo apt install postgresql-client-18`
(or set `PG_DUMP`/`PG_PSQL`/`PG_CREATEDB`/`PG_DROPDB` to full paths).

Verify data:

```bash
python manage.py audit_navigable_places     # 0 missing coords, all navigable
```

---

## 4. Build & serve

```bash
# static assets + frontend
python manage.py collectstatic --noinput
cd ../frontend/Tourism && npm ci && npm run build   # -> dist/
```

Gunicorn (systemd unit `/etc/systemd/system/tourism.service`):

```ini
[Unit]
Description=Tourism API
After=network.target

[Service]
User=www-data
WorkingDirectory=/srv/tourism/Tourism
EnvironmentFile=/srv/tourism/Tourism/.env
ExecStart=/srv/tourism/.venv/bin/gunicorn Tourism.wsgi:application \
  --workers 3 --bind 127.0.0.1:8000 --timeout 60
Restart=always

[Install]
WantedBy=multi-user.target
```

nginx (`/etc/nginx/sites-available/tourism`): serve `frontend/Tourism/dist`
as the site root with `try_files $uri /index.html;`, proxy `/api/` and
`/admin/` to `127.0.0.1:8000`, then get TLS:

```bash
sudo apt install -y certbot python3-certbot-nginx
sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com
```

`pip install gunicorn` belongs in requirements deployment; add it to the
venv if not present.

---

## 5. Scheduled jobs (cron)

```cron
# daily backup (rotates, sha256-verified)
0 3 * * *  cd /srv/tourism/Tourism && /srv/tourism/.venv/bin/python manage.py backup_database
# weekly restore drill (proves backups actually restore)
0 4 * * 0  cd /srv/tourism/Tourism && /srv/tourism/.venv/bin/python manage.py restore_database --file $(ls -t backups/*.gz | head -1) --target /tmp/restore-drill
```

---

## 6. Launch-day checks (in the browser)

1. `https://yourdomain.com` loads; no mixed-content console errors.
2. Register a user → verify email → log in.
3. Search "Pokhara" → open a destination → **Navigate** → map + step list
   (left/right instructions) renders; GPS permission prompt works on a phone.
4. Nearby POIs show hospitals/hotels/banks near a destination.
5. Itinerary planner builds a plan for a non-obvious district (e.g. Mustang).
6. Admin login → `/admin-cms` → edit a destination, see the revision saved.
7. `GET /api/v1/system/health/` returns ok; `validate_production_config`
   still PASSES on the server.

---

## 7. What to monitor after launch

- **Backups**: `system_health` warns when the newest archive is >24 h old.
- **Routing honesty**: responses carry `source` — `osrm` (live roads) vs
  `graphml_fallback` / `straight_line_fallback` (labelled estimates). Set
  `ROUTING_BASE_URL` to upgrade to street-level turn-by-turn.
- **Provider keys**: weather/OAuth/OSM all degrade gracefully; a missing key
  never breaks a page, it only hides that feature (by design).
- **Disk**: SQLite + WAL side files live next to `db.sqlite3`; keep ≥20 %
  free.

Rollback: redeploy the previous git tag, `python manage.py migrate` is
forward-only (never delete migrations), and `restore_database` can recover
data from any sha256-verified archive.
