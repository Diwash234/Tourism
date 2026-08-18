# Production Operations

## Principles

- Missing official feeds, local contacts, road routes or images remain unavailable; never synthesize safety data.
- Only HTTPS authority feeds are accepted (localhost is allowed for development).
- User submissions and feedback are not ML-eligible until admin verification.
- News remains separate from official warnings.

## Environment

```env
DHM_FEED_URL=
DHM_API_KEY=
BIPAD_FEED_URL=
BIPAD_API_KEY=
EXTERNAL_SYNC_TIMEOUT=15
ROUTING_API_URL=
ROUTING_API_KEY=
```

Feed URLs must return the normalized `records` schema accepted by `risk_ingestion.py`. Configure them only after the authority confirms endpoint access and data-use conditions.

`ROUTING_API_URL` must expose an OSRM-compatible `/route/v1/driving/...` API. If blank or unavailable, the application returns `road_distance_km: null` and labels the displayed value as straight-line distance.

## Scheduled jobs

Example cron entries (adjust the virtualenv and project paths):

```cron
*/15 * * * * cd /app/Tourism && /app/.venv/bin/python manage.py sync_official_risk --provider all
0 2 * * * cd /app/Tourism && /app/.venv/bin/python manage.py health_snapshot
0 3 * * 0 cd /app/Tourism && /app/.venv/bin/python manage.py audit_data_quality --output /app/reports/data-gaps.csv
```

Use a platform scheduler or systemd timer in production rather than relying on a web process.

## Commands

```bash
python manage.py migrate
python manage.py sync_official_risk --provider all --dry-run
python manage.py sync_official_risk --provider all
python manage.py audit_data_quality --output reports/data-gaps.csv
python manage.py acceptance_check_nepal
python manage.py health_snapshot
```

## Routing API

```http
POST /api/v1/routing/metrics/
{
  "start_latitude": 28.2096,
  "start_longitude": 83.9856,
  "end_latitude": 28.2380,
  "end_longitude": 83.9956
}
```

The response always distinguishes `straight_line_km` from `road_distance_km` and reports routing status.

## ML operations

The admin ML registry records dataset size, version, previous version, status and logs. Only whitelisted trainers run. Before promotion in a production deployment:

1. Export approved records.
2. Train into a staging artifact directory.
3. Require model-specific holdout metrics.
4. Compare to the previous version.
5. Promote atomically only if thresholds pass.
6. Keep the previous artifact for rollback.

The current trainers do not all emit comparable quality metrics. A successful process exit is recorded but must not be treated as proof that a model is better.

## Backups and rollback

- Back up SQLite using SQLite's online backup API or `sqlite3 .backup`, not a live filesystem copy.
- Back up media and model artifacts separately.
- Apply migrations before starting web workers.
- Keep at least one prior database, media and model snapshot.

## Monitoring

Admin health output includes database, storage, ML service, Overpass, Wikimedia, DHM feed, BIPAD feed and routing configuration/reachability. Unconfigured optional integrations are reported as unconfigured, not as healthy live feeds.
