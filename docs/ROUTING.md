# Real road routing

Navigation currently serves **straight-line distances and corridor estimates**,
and the app labels them as such. It never claims a road distance it cannot
back up. This is how to make those labels honest *and* true: run a real routing
engine over a real road network.

## What is true right now

```bash
python manage.py audit_routing
```

With `ROUTING_BASE_URL` unset this reports `NOT VERIFIED`, and it means it. The
bundled `graphml_fallback` gives a plausible-looking 232–256 km between places
that are 140 km apart, drawn from a coarse corridor graph. It is an estimate
with a clear label, not a route.

`validate_production_config` already treats an empty `ROUTING_BASE_URL` as a
production **FAIL**, so this cannot be shipped by accident.

## Step 1 — fetch and verify the extract

```bash
python scripts/fetch_osm_extract.py            # ~395 MB, verified
python scripts/fetch_osm_extract.py --print-only   # show what was verified
```

The script fetches Geofabrik's own published `.md5` **first**, verifies the
download against it, and records the hash, size, publisher timestamp and licence
in `data/osm/routing_extract_provenance.json`. It ships no hardcoded checksum —
a stale hash would either block every legitimate weekly update or get "fixed" by
someone blessing whatever they happened to download. The verifiable claim is
"this file matched the publisher's hash at this time".

If the checksum does not match, it stops. A truncated or corrupted extract
produces routing answers that look entirely plausible and are wrong, which is the
worst possible failure mode for navigation.

## Step 2 — build the routing graph

OSRM needs its own compiled graph, which is a one-off and must be redone after
every extract update. The project recommends the MLD pipeline and defaults to it.

The current image is **`ghcr.io/project-osrm/osrm-backend`**. The Docker Hub
repository `osrm/osrm-backend` now only carries older versions — its newest tag
is v5.25.0 from May 2021 — so do not use it for a fresh install.

From the repository root, with the extract in `data/osm`:

```bash
docker run --rm -t -v "${PWD}/data/osm:/data" ghcr.io/project-osrm/osrm-backend \
  osrm-extract -p /opt/car.lua /data/nepal-latest.osm.pbf
docker run --rm -t -v "${PWD}/data/osm:/data" ghcr.io/project-osrm/osrm-backend \
  osrm-partition /data/nepal-latest.osrm
docker run --rm -t -v "${PWD}/data/osm:/data" ghcr.io/project-osrm/osrm-backend \
  osrm-customize /data/nepal-latest.osrm
```

`/data/nepal-latest.osrm` is a **base path, not a file** — it refers to the set
of `nepal-latest.osrm.*` files the previous step wrote. The `.osrm` suffix may be
omitted.

Expect this to take a while and print almost nothing while it runs; that is
normal, not a hang. For the CH pipeline instead, replace `osrm-partition` +
`osrm-customize` with a single `osrm-contract` and pass `--algorithm ch` to
`osrm-routed`. MLD is the recommended default.

## Step 3 — run it

Add to `docker-compose.yml`:

```yaml
  routing:
    image: ghcr.io/project-osrm/osrm-backend
    command: osrm-routed --algorithm mld /data/nepal-latest.osrm
    ports:
      - "5000:5000"
    volumes:
      - ./data/osm:/data
    restart: unless-stopped
```

and in the `web` service environment:

```yaml
      - ROUTING_BASE_URL=${ROUTING_BASE_URL:-http://routing:5000}
```

Then `docker compose up -d routing` and rebuild `web`.

Smoke test it directly before trusting it:

```bash
curl "http://127.0.0.1:5000/route/v1/driving/85.3070,27.7048;83.9856,28.2096?overview=false"
```

## Step 4 — prove it

```bash
python manage.py audit_routing
```

This is the step that matters, and it is deliberately harder to fool than a
status code. For each probe pair it checks:

1. a provider is configured **and reachable**;
2. the response is labelled `osrm` and `routed`, not a fallback;
3. **the road distance is at least the straight-line distance.** A route cannot
   be shorter than the crow flight between the same two points. If a
   "real-road" answer comes back shorter, the service is not routing over roads
   and every distance in the app is quietly wrong;
4. the detour ratio is plausible. Nepal is mountainous, so Kathmandu→Pokhara
   should be roughly 1.5–1.7× the straight line. A ratio near 1.0 means the
   straight line is being echoed back; a ratio above 4× usually means the two
   points are not on the same network;
5. both endpoints carry real Nepal coordinates — a route between two null-island
   points, or between a point and itself, proves nothing, so those probes are
   refused rather than counted.

Only when all of that holds does it print `VERIFIED`. `--json` gives the same
verdict for monitoring.

## Honest limits

- **The route is only as good as the extract.** Geofabrik republishes Nepal
  daily; a month-old extract will not know about a new road, and may still route
  over a bridge that washed out. `routing_extract_provenance.json` records when
  the data was last verified so staleness is at least visible.
- **No live traffic.** OSRM's `driving` profile is free-flow, not
  congestion-aware. Do not describe durations as "the drive will take 5 hours".
- **Small lanes may be missing.** OSM in Nepal is uneven; a hotel in a narrow
  lane can snap to a road that is a few hundred metres away. Distance to the
  *road* is not distance to the *doorstep*.
- **Coordinates still gate quality.** 1,449 hospital and police rows have no
  coordinate provenance, and some destinations sit on shared points. A perfect
  routing engine over placeholder coordinates returns perfectly routed nonsense.
  See the coordinate section of `docs/LAUNCH_CHECKLIST.md`.
- **Rate limits are real.** `ROUTING_RATE_LIMIT` (default 30/s) and
  `ROUTING_CACHE_TTL` (default 600 s) exist because an open public endpoint
  pointed at a single-threaded `osrm-routed` will be the first thing to fall
  over. Keep the cache; raise the limit carefully.

## Alternatives

| Option | Real road routes | Cost | Notes |
|---|---|---|---|
| Self-hosted OSRM (this doc) | yes | ~395 MB download, ~2 GB RAM, your ops time | Full control, no per-request fee |
| `router.project-osrm.org` demo | yes | free | **Not for production.** The project publishes a usage policy for the demo server; treat it as a trial only |
| Mapbox / Google Directions | yes | paid, per request | Key required; the code already supports `ROUTING_API_KEY` |
| Nothing (current state) | no | free | Honest labels; distances are straight-line |

If you would rather not operate a routing server, the existing
`ROUTING_PROVIDER` abstraction and `ROUTING_API_KEY` support a paid provider
without code changes — only `ROUTING_BASE_URL` and the key need setting.
