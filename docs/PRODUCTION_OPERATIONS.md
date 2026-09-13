# Production Launch & Data Operations

The final operational section of the master specification. Everything here
is implemented and tested in code; this runbook is how operations run it in
production. Feature development is **frozen** — this is the maintain-the-
platform phase.

---

## 1. OAuth (Google / GitHub) — one-time credential setup

1. **Google**: Google Cloud Console → APIs & Services → Credentials →
   *OAuth client ID (Web application)*.
   - Authorized redirect URI: `https://<production-domain>/auth/callback/google`
2. **GitHub**: github.com/settings/developers → *New OAuth App*.
   - Authorization callback URL: `https://<production-domain>/auth/callback/github`
3. Configure:
   - Frontend `.env` (public values only): `VITE_GOOGLE_CLIENT_ID`, `VITE_GITHUB_CLIENT_ID`
   - Backend `.env` (secrets — **never in frontend code or git**):
     `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`, `GITHUB_CLIENT_ID`, `GITHUB_CLIENT_SECRET`
4. Verify: click *Continue with Google* → Google's account chooser appears →
   sign in → lands on `/dashboard`. The flow carries a CSRF `state`, links
   by verified email, and disabled-button UX shows while unconfigured.

## 2. Automated backups + periodic restore drill

Daily cron (RPO = 24 h; tune `--keep` for retention):

```cron
30 2 * * *  cd /srv/tourism/Tourism && /srv/tourism/.venv/bin/python manage.py backup_database --keep 14 --dir /mnt/offsite/tourism-backups >> /var/log/tourism-backup.log 2>&1
```

Each run: consistent SQLite snapshot → gzip → SHA-256 sidecar → retention
prune. Copy the backups directory **off-site** (the `--dir` mount above).

**Monthly restore drill** (RTO verified ≈ seconds for a 5.6 MB DB):

```bash
python manage.py restore_database --from /mnt/offsite/tourism-backups/db-<stamp>.sqlite3.gz --yes
# then: python manage.py check && restart the service
```

`restore_database` validates integrity *before* touching the live file and
preserves the pre-restore DB alongside it.

## 3. Duplicate review workflow (data quality)

```
detect_duplicate_destinations  →  candidate report (confidence-tiered)
        →  admin review (highest confidence first)
        →  POST /api/v1/admin/destinations/merge/ {source_id, target_id, reason}
        →  audit-logged merge (relations move, source soft-deleted)
```

Tiers: `high` (identical normalized names ≤ 0.5 km — safe to batch-review),
`medium` (identical names, near or same district), `needs_review` (≥ 0.85
name similarity within one district). **Never merge blind** — every merge
requires a human reason and is audit-logged.

## 4. Data enrichment (national dataset breadth)

The bundled OSM CSV (12,838 rows; 8,597 destinations) is the *current*
dataset, not the final national one. To enrich beyond it:

1. Run from a network that can reach Overpass:
   `python manage.py enrich_osm_services` / `import_trekking` / re-run the
   `ml_service` extraction to refresh `destinations_clean.csv`.
2. `python manage.py import_osm_destinations` — dedupes by OSM external_id,
   skips unnamed nodes (never fabricates names), writes honest descriptions.
3. `python manage.py normalize_district_names` — canonical spellings.
4. New records enter `pending`/candidate queues → admin review → publish.

The whole chain is one command: **`python manage.py run_data_pipeline`**
(report mode) / `run_data_pipeline --apply`. Publishing always stays a
human step.

## 5. Routing validation (pre-launch checklist)

Verified behaviour (see acceptance runs):

| Check | Result |
|---|---|
| Lakeside → Davis Falls | `graph_routed`, 6.97 km, 21 turn instructions |
| Pokhara → Sarangkot | `graph_routed`, 26.76 km, 18 instructions |
| Pokhara → Begnas | `graph_routed`, 11.6 km |
| Kathmandu → Pokhara | `graph_routed`, 255.16 km, 60 instructions, ETA 437 min |
| Pokhara → Chitwan | `graph_routed`, 147.9 km, ETA 254 min |
| Out-of-network (Delhi→Pokhara) | `routing_unavailable` — **no invented route**, straight-line explicitly labelled "not road distance" |

The bundled engine is a **tourism graph, not street-level** — every response
says so in its `note`. For street-level road geometry/ETA in production,
configure an OSRM/GraphHopper provider in admin → site setting
`routing_provider` (HTTPS base URL); the app prefers it automatically and
falls back honestly (`routing_unavailable`) rather than dressing up
straight-line distances as navigation.

## 6. Monitoring

- `GET /api/v1/system/health/` — DB/disk/error-rate liveness (alert if `ok=false`)
- Admin → audit app — action/error/latency logs; alert on severity ≥ error
- Routing: watch for `routing_unavailable` spikes (provider outage)
- Freshness: schedule `flag_stale_verifications --flag` weekly so stale
  "verified" badges expire (`VERIFICATION_INTERVAL_DAYS`, default 180)

## 7. Staging → production

- Separate `.env` per environment (both `.env.example` files document 100%
  of keys); `DEBUG=False`, explicit `ALLOWED_HOSTS`, strong `SECRET_KEY`,
  `ML_SERVICE_API_KEY`/`ML_WEBHOOK_SECRET` rotated per environment.
- Deploy gate: `manage.py test` (593) + `npm run test:e2e` (77) +
  `manage.py check` + `makemigrations --check` all green.
- Postgres in production: set `DB_ENGINE=postgres` + `DB_*`; the SQLite
  backup command steps aside for `pg_dump` in that case.

## 8. Final acceptance (launch checklist)

- [ ] OAuth live with production redirect URIs (section 1)
- [ ] Backup cron running + first off-site copy + restore drill PASS (2)
- [ ] High-confidence duplicates reviewed/merged (3)
- [ ] Enrichment run from unrestricted network; coverage report re-run (4)
- [ ] Routing provider configured + checklist re-run (5)
- [ ] Monitoring alerts wired (6)
- [ ] Staging deploy green, then production (7)
