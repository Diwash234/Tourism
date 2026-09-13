# Staging Deployment (§19)

Automated by `scripts/staging_deploy.sh` — the pipeline below runs in
order and fails loudly at the first broken step.

```
Build → Migrate → Collect static → Django check → Migration-drift check
      → validate_production_config → Frontend build
      → Backend tests (594) → E2E smoke (77) → Health endpoint
```

## Environment layout (separate per §18 of the master spec)

| Concern | Development | Staging | Production |
|---|---|---|---|
| `.env` | `Tourism/.env` (dev values) | staging host `.env` | prod host `.env` |
| Database | SQLite `db.sqlite3` | Postgres (`DB_ENGINE=postgres`) | Postgres |
| Secrets | placeholders | staging-only keys | rotated, never in git |
| Domain | localhost:8000/5173 | staging.<domain> | <domain> |

Both `.env.example` files document 100% of the keys each side reads.

## Host prerequisites

- Python 3.11 venv with `Tourism/requirement.txt` + `ml_service/requirements.txt`
- Node 20+ with `frontend/Tourism` dependencies (`npm ci` runs in the script)
- Postgres reachable (staging/prod) — set `DB_*` variables
- Reverse proxy terminating HTTPS (secure cookie/HSTS defaults engage
  automatically when `DEBUG=False`)

## Services (systemd units recommended)

```
tourism-backend   daphne -b 0.0.0.0 -p 8000 Tourism.asgi:application   (cwd Tourism/)
tourism-ml        uvicorn app:app --host 127.0.0.1 --port 8001         (cwd ml_service/)
tourism-frontend  nginx serving frontend/Tourism/dist + /api proxy to :8000
```

`ML_SERVICE_URL=http://127.0.0.1:8001` keeps the ML service private.

## Deploy steps

```bash
git fetch && git checkout <release-commit>
VENV=/srv/tourism/.venv ./scripts/staging_deploy.sh
# service restart:
sudo systemctl restart tourism-backend tourism-ml
sudo nginx -s reload
```

The script's final step polls `GET /api/v1/system/health/` until
`"ok": true` (60 s budget) — that endpoint is the deployment health check
for load balancers too.

## Scheduled operations (cron on the host)

```cron
30 2 * * *  cd /srv/tourism/Tourism && ../.venv/bin/python manage.py backup_database --keep 14 --dir /mnt/offsite/tourism-backups
15 3 * * 1  cd /srv/tourism/Tourism && ../.venv/bin/python manage.py run_data_pipeline --apply
0  4 1 * *  cd /srv/tourism/Tourism && ../.venv/bin/python manage.py flag_stale_verifications --flag
```

Backup freshness is monitored live: `system_health` reports a 🔴 BACKUP
WARNING when the newest archive is older than 24 h.

## Rollback

1. `git checkout <previous-commit>` → re-run the deploy script
2. If data was migrated forward only: restore the pre-deploy backup
   (`manage.py restore_database --from <archive> --yes`) — restore always
   validates integrity and preserves the pre-restore DB.

## Acceptance smoke (§20)

After deploy, run the E2E suite (`npm run test:e2e`) — it exercises the
full user journey (signup → login → search → destination → nearby → AI →
itinerary → budget → routes → trip watch) and the admin lifecycle
(create/edit/verify/publish/archive round-trips) against the live stack.
